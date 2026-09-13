"""
Tests d'intégration — API admin PEI : portraits (lauréats / étudiants-entrepreneurs)
===================================================================================

Spec : specs/022-pei-laureates-partners/contracts/admin-api.md
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entrepreneurship import (
    PeiCohort,
    PeiCohortType,
    PeiLaureate,
    PeiLaureateType,
    PeiPartner,
    PeiPartnerFamily,
)
from app.models.identity import AuditLog, Permission, Role, RolePermission
from app.models.partner import Partner, PartnerType
from app.services import translation_service

BASE = "/api/admin/entrepreneurship"
PERMISSION_CODES = [
    ("entrepreneurship.view", "Voir le pôle Entrepreneuriat"),
    ("entrepreneurship.create", "Créer des contenus du pôle Entrepreneuriat"),
    ("entrepreneurship.edit", "Modifier des contenus du pôle Entrepreneuriat"),
    ("entrepreneurship.delete", "Supprimer des contenus du pôle Entrepreneuriat"),
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def entrepreneurship_permissions(
    db_session: AsyncSession, admin_role: Role
) -> list[Permission]:
    """Greffe les 4 permissions entrepreneurship.* sur le rôle admin."""
    perms = []
    for code, name in PERMISSION_CODES:
        p = Permission(
            id=str(uuid4()),
            code=code,
            name_fr=name,
            category="entrepreneurship",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(p)
        perms.append(p)
    await db_session.flush()
    for p in perms:
        db_session.add(RolePermission(role_id=admin_role.id, permission_id=p.id))
    await db_session.commit()
    return perms


@pytest.fixture
def translator_stub(monkeypatch):
    """Remplace la traduction réseau par un stub déterministe « [lang] texte »."""
    calls: list[tuple[str, str]] = []

    async def fake_translate(src, lang, source=None):
        if not src or not str(src).strip():
            return None
        calls.append((src, lang))
        return f"[{lang}] {src}"

    monkeypatch.setattr(translation_service, "translate_text", fake_translate)
    monkeypatch.setattr(translation_service, "translate_html", fake_translate)
    return calls


@pytest_asyncio.fixture
async def cohorts(db_session: AsyncSession) -> dict[str, PeiCohort]:
    items = {
        "fse-1": PeiCohort(code="fse-1", label="FSE 1", year=2023, type=PeiCohortType.FSE, display_order=0),
        "fse-2": PeiCohort(code="fse-2", label="FSE 2", year=2024, type=PeiCohortType.FSE, display_order=1),
        "see-2026": PeiCohort(code="see-2026", label="SEE 2026", year=2026, type=PeiCohortType.SEE, display_order=2),
    }
    db_session.add_all(items.values())
    await db_session.commit()
    return items


async def _audits(db: AsyncSession, action: str):
    return (
        (await db.execute(select(AuditLog).where(AuditLog.action == action))).scalars().all()
    )


def _payload(cohort_id: str, **overrides) -> dict:
    payload = {
        "cohort_id": cohort_id,
        "type": "fse_laureate",
        "full_name": "Awa Diop",
        "project_name": "SantéConnect",
        "department_label": "Département Santé",
        "quote": "Grâce au FSE, notre projet a pris son envol.",
        "website_url": "https://santeconnect.example.org",
        "video_url": "https://www.youtube.com/watch?v=abc",
        "grant_amount": 5000,
        "is_featured": True,
    }
    payload.update(overrides)
    return payload


async def _create(client: AsyncClient, cohort_id: str, **overrides) -> dict:
    response = await client.post(f"{BASE}/laureates", json=_payload(cohort_id, **overrides))
    assert response.status_code == 201, response.text
    return response.json()


async def _orders(db: AsyncSession, cohort_id: str) -> list[tuple[str, int]]:
    rows = (
        await db.execute(
            select(PeiLaureate.id, PeiLaureate.display_order)
            .where(PeiLaureate.cohort_id == cohort_id)
            .order_by(PeiLaureate.display_order)
        )
    ).all()
    return [(str(r[0]), r[1]) for r in rows]


# ---------------------------------------------------------------------------
# Création, validation, traduction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_laureate_without_permission_returns_403(
    authenticated_client: AsyncClient, cohorts
):
    response = await authenticated_client.post(
        f"{BASE}/laureates", json=_payload(cohorts["fse-1"].id)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_laureate_autofills_translations(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
    cohorts,
):
    body = await _create(authenticated_client, cohorts["fse-1"].id)
    assert translator_stub, "la traduction automatique doit être appelée"
    assert body["department_label_en"] == "[en] Département Santé"
    assert body["quote_ar"] == "[ar] Grâce au FSE, notre projet a pris son envol."
    assert body["grant_amount"] == "5000.00"
    assert body["display_order"] == 0
    assert body["is_published"] is False
    assert body["published_at"] is None
    assert body["photo_url"] is None
    assert body["cohort"] == {
        "id": cohorts["fse-1"].id,
        "code": "fse-1",
        "label": "FSE 1",
        "type": "fse",
        "year": 2023,
        "active": True,
    }

    logs = await _audits(db_session, "entrepreneurship.laureate.create")
    assert len(logs) == 1
    assert logs[0].record_id == body["id"]
    assert logs[0].table_name == "pei_laureates"


@pytest.mark.asyncio
async def test_create_published_sets_published_at(
    authenticated_client: AsyncClient, entrepreneurship_permissions, translator_stub, cohorts
):
    body = await _create(authenticated_client, cohorts["fse-1"].id, is_published=True)
    assert body["published_at"] is not None


@pytest.mark.asyncio
async def test_laureate_type_must_match_cohort_type(
    authenticated_client: AsyncClient, entrepreneurship_permissions, translator_stub, cohorts
):
    wrong = await authenticated_client.post(
        f"{BASE}/laureates",
        json=_payload(cohorts["fse-1"].id, type="student_entrepreneur"),
    )
    assert wrong.status_code == 422
    assert wrong.json()["detail"] == "Un étudiant-entrepreneur doit appartenir à une cohorte SEE"

    created = await _create(authenticated_client, cohorts["fse-1"].id)
    patch = await authenticated_client.patch(
        f"{BASE}/laureates/{created['id']}", json={"type": "student_entrepreneur"}
    )
    assert patch.status_code == 422

    move = await authenticated_client.patch(
        f"{BASE}/laureates/{created['id']}", json={"cohort_id": cohorts["see-2026"].id}
    )
    assert move.status_code == 422
    assert move.json()["detail"] == "Un lauréat FSE doit appartenir à une cohorte FSE"

    both = await authenticated_client.patch(
        f"{BASE}/laureates/{created['id']}",
        json={"cohort_id": cohorts["see-2026"].id, "type": "student_entrepreneur"},
    )
    assert both.status_code == 200, both.text
    assert both.json()["type"] == "student_entrepreneur"


@pytest.mark.asyncio
async def test_create_laureate_unknown_cohort_returns_404(
    authenticated_client: AsyncClient, entrepreneurship_permissions, translator_stub
):
    response = await authenticated_client.post(
        f"{BASE}/laureates", json=_payload(str(uuid4()))
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_laureate_field_validation_returns_422(
    authenticated_client: AsyncClient, entrepreneurship_permissions, translator_stub, cohorts
):
    cohort_id = cohorts["fse-1"].id

    long_quote = await authenticated_client.post(
        f"{BASE}/laureates", json=_payload(cohort_id, quote="a" * 601)
    )
    assert long_quote.status_code == 422
    assert "Le verbatim ne doit pas dépasser 600 caractères" in long_quote.text

    bad_url = await authenticated_client.post(
        f"{BASE}/laureates", json=_payload(cohort_id, linkedin_url="linkedin")
    )
    assert bad_url.status_code == 422
    assert "Adresse web invalide : linkedin_url" in bad_url.text

    negative = await authenticated_client.post(
        f"{BASE}/laureates", json=_payload(cohort_id, grant_amount=-1)
    )
    assert negative.status_code == 422

    blank_url = await authenticated_client.post(
        f"{BASE}/laureates", json=_payload(cohort_id, instagram_url="")
    )
    assert blank_url.status_code == 201
    assert blank_url.json()["instagram_url"] is None


@pytest.mark.asyncio
async def test_long_translation_is_clamped_to_600(
    authenticated_client: AsyncClient,
    monkeypatch,
    entrepreneurship_permissions,
    cohorts,
):
    async def verbose_translate(src, lang, source=None):
        return (f"[{lang}] " + src + " ") * 3 if src else None

    monkeypatch.setattr(translation_service, "translate_text", verbose_translate)
    quote = "mot " * 150  # 600 caractères
    body = await _create(authenticated_client, cohorts["fse-1"].id, quote=quote.strip())
    assert len(body["quote_en"]) <= 600
    assert body["quote_en"].endswith("…")


# ---------------------------------------------------------------------------
# Publication, mise en avant, liste
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_publish_keeps_published_at_and_featured_toggles(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
    cohorts,
):
    created = await _create(authenticated_client, cohorts["fse-1"].id, is_featured=False)

    published = await authenticated_client.patch(
        f"{BASE}/laureates/{created['id']}/publish", json={"is_published": True}
    )
    assert published.status_code == 200, published.text
    first_date = published.json()["published_at"]
    assert first_date is not None

    unpublished = await authenticated_client.patch(
        f"{BASE}/laureates/{created['id']}/publish", json={"is_published": False}
    )
    assert unpublished.json()["is_published"] is False
    assert unpublished.json()["published_at"] == first_date

    featured = await authenticated_client.patch(
        f"{BASE}/laureates/{created['id']}/featured", json={"is_featured": True}
    )
    assert featured.status_code == 200
    assert featured.json()["is_featured"] is True
    assert set(featured.json()) == {"id", "is_featured", "updated_at"}

    for action in ("publish", "unpublish", "feature"):
        assert len(await _audits(db_session, f"entrepreneurship.laureate.{action}")) == 1


@pytest.mark.asyncio
async def test_list_laureates_filters_and_sort(
    authenticated_client: AsyncClient, entrepreneurship_permissions, translator_stub, cohorts
):
    a = await _create(authenticated_client, cohorts["fse-2"].id, full_name="Zoé", project_name="Projet Z")
    b = await _create(authenticated_client, cohorts["fse-1"].id, full_name="Bakary", project_name="AgriTech")
    c = await _create(
        authenticated_client,
        cohorts["see-2026"].id,
        type="student_entrepreneur",
        full_name="Chloé",
        project_name="EduLab",
        is_published=True,
    )

    everything = (await authenticated_client.get(f"{BASE}/laureates")).json()
    assert everything["total"] == 3
    # Tri : ordre de la cohorte, puis ordre dans la cohorte
    assert [i["id"] for i in everything["items"]] == [b["id"], a["id"], c["id"]]

    by_cohort = (
        await authenticated_client.get(f"{BASE}/laureates", params={"cohort_id": cohorts["fse-2"].id})
    ).json()
    assert [i["id"] for i in by_cohort["items"]] == [a["id"]]

    by_project = (await authenticated_client.get(f"{BASE}/laureates", params={"q": "agri"})).json()
    assert [i["id"] for i in by_project["items"]] == [b["id"]]

    by_type = (
        await authenticated_client.get(f"{BASE}/laureates", params={"type": "student_entrepreneur"})
    ).json()
    assert [i["id"] for i in by_type["items"]] == [c["id"]]

    drafts = (
        await authenticated_client.get(f"{BASE}/laureates", params={"is_published": "false"})
    ).json()
    assert drafts["total"] == 2


@pytest.mark.asyncio
async def test_get_unknown_laureate_returns_404(
    authenticated_client: AsyncClient, entrepreneurship_permissions
):
    assert (await authenticated_client.get(f"{BASE}/laureates/{uuid4()}")).status_code == 404
    assert (await authenticated_client.get(f"{BASE}/laureates/pas-un-uuid")).status_code == 404


# ---------------------------------------------------------------------------
# Ordre par cohorte
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reorder_is_scoped_to_cohort(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
    cohorts,
):
    fse1 = cohorts["fse-1"].id
    ids = [(await _create(authenticated_client, fse1, full_name=f"Portrait {i}"))["id"] for i in range(3)]
    other = await _create(authenticated_client, cohorts["fse-2"].id)
    assert other["display_order"] == 0

    incomplete = await authenticated_client.patch(
        f"{BASE}/laureates/reorder", json={"cohort_id": fse1, "ids": ids[:2]}
    )
    assert incomplete.status_code == 422

    out_of_scope = await authenticated_client.patch(
        f"{BASE}/laureates/reorder", json={"cohort_id": fse1, "ids": [*ids, other["id"]]}
    )
    assert out_of_scope.status_code == 422

    reordered = await authenticated_client.patch(
        f"{BASE}/laureates/reorder", json={"cohort_id": fse1, "ids": list(reversed(ids))}
    )
    assert reordered.status_code == 200, reordered.text
    assert reordered.json() == {"updated": 2}
    assert await _orders(db_session, fse1) == [(i, n) for n, i in enumerate(reversed(ids))]
    assert await _orders(db_session, cohorts["fse-2"].id) == [(other["id"], 0)]

    logs = await _audits(db_session, "entrepreneurship.laureate.reorder")
    assert len(logs) == 1
    assert logs[0].record_id is None
    assert logs[0].new_values == {"cohort_id": fse1, "ids": list(reversed(ids))}


@pytest.mark.asyncio
async def test_change_cohort_moves_to_last_and_renumbers_old(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
    cohorts,
):
    fse1, fse2 = cohorts["fse-1"].id, cohorts["fse-2"].id
    first, second, third = [
        (await _create(authenticated_client, fse1, full_name=f"Portrait {i}"))["id"] for i in range(3)
    ]
    existing = await _create(authenticated_client, fse2)

    moved = await authenticated_client.patch(f"{BASE}/laureates/{first}", json={"cohort_id": fse2})
    assert moved.status_code == 200, moved.text
    assert moved.json()["display_order"] == 1
    assert moved.json()["cohort"]["code"] == "fse-2"

    assert await _orders(db_session, fse1) == [(second, 0), (third, 1)]
    assert await _orders(db_session, fse2) == [(existing["id"], 0), (first, 1)]

    # Modification d'un portrait avec montant : l'ancienne valeur (Decimal) est auditée
    amount = await authenticated_client.patch(
        f"{BASE}/laureates/{second}", json={"grant_amount": 4200.5, "linkedin_url": ""}
    )
    assert amount.status_code == 200, amount.text
    assert amount.json()["grant_amount"] == "4200.50"
    amount_log = (await _audits(db_session, "entrepreneurship.laureate.update"))[-1]
    assert amount_log.old_values["grant_amount"] == "5000.00"

    deleted = await authenticated_client.delete(f"{BASE}/laureates/{second}")
    assert deleted.status_code == 204
    assert await _orders(db_session, fse1) == [(third, 0)]
    assert len(await _audits(db_session, "entrepreneurship.laureate.delete")) == 1
    assert len(await _audits(db_session, "entrepreneurship.laureate.update")) == 2


# ---------------------------------------------------------------------------
# Suppression d'une cohorte utilisée (409)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_cohort_used_by_laureate_returns_409(
    authenticated_client: AsyncClient, entrepreneurship_permissions, translator_stub, cohorts
):
    fse1 = cohorts["fse-1"].id
    created = await _create(authenticated_client, fse1)

    refused = await authenticated_client.delete(f"{BASE}/cohorts/{fse1}")
    assert refused.status_code == 409
    assert refused.json()["detail"] == "Cohorte utilisée par 1 lauréats"

    assert (await authenticated_client.delete(f"{BASE}/laureates/{created['id']}")).status_code == 204
    assert (await authenticated_client.delete(f"{BASE}/cohorts/{fse1}")).status_code == 204


# ---------------------------------------------------------------------------
# Traduction à la demande, tableau de bord, traduction en lot (US5)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_translate_laureate_fields_without_persistence(
    authenticated_client: AsyncClient, entrepreneurship_permissions, translator_stub
):
    response = await authenticated_client.post(
        f"{BASE}/laureates/translate", json={"department_label": "Département Culture", "quote": "Bravo"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "department_label_en": "[en] Département Culture",
        "department_label_ar": "[ar] Département Culture",
        "quote_en": "[en] Bravo",
        "quote_ar": "[ar] Bravo",
    }


@pytest.mark.asyncio
async def test_dashboard_counts_laureates_and_partners(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
    cohorts,
):
    await _create(authenticated_client, cohorts["fse-1"].id, is_published=True)
    await _create(authenticated_client, cohorts["fse-1"].id)

    active = Partner(name="AUF", type=PartnerType.OTHER, active=True)
    inactive = Partner(name="OIF", type=PartnerType.OTHER, active=False)
    db_session.add_all([active, inactive])
    await db_session.flush()
    db_session.add_all(
        [
            PeiPartner(partner_id=active.id, family=PeiPartnerFamily.INTERNATIONAL, display_order=0),
            PeiPartner(partner_id=inactive.id, family=PeiPartnerFamily.INTERNATIONAL, display_order=1),
        ]
    )
    await db_session.commit()

    body = (await authenticated_client.get(f"{BASE}/dashboard")).json()
    assert body["laureates"] == {"published": 1, "total": 2}
    assert body["partners"] == {"active": 1, "total": 2}


@pytest.mark.asyncio
async def test_translate_missing_fills_empty_laureate_fields(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
    cohorts,
):
    laureate = PeiLaureate(
        cohort_id=cohorts["fse-1"].id,
        type=PeiLaureateType.FSE_LAUREATE,
        full_name="Awa Diop",
        project_name="SantéConnect",
        quote="Merci",
        quote_ar="شكرا",
        display_order=0,
    )
    db_session.add(laureate)
    await db_session.commit()

    first = await authenticated_client.post(f"{BASE}/translate-missing")
    assert first.status_code == 200, first.text
    assert first.json()["laureates"] == 1

    await db_session.refresh(laureate)
    assert laureate.quote_en == "[en] Merci"
    assert laureate.quote_ar == "شكرا"

    second = await authenticated_client.post(f"{BASE}/translate-missing")
    assert second.json()["laureates"] == 0
