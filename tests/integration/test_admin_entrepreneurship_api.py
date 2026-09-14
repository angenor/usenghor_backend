"""
Tests d'intégration — API admin Entrepreneuriat (PEI)
=====================================================

Spec : specs/021-pei-entrepreneurship-core/contracts/admin-api.md
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.editorial import EditorialContent, EditorialValueType
from app.models.entrepreneurship import (
    PeiCohort,
    PeiCohortType,
    PeiProgram,
    PeiProgramPhase,
    PeiResource,
    PeiResourceType,
)
from app.models.faq import FaqCategory, FaqEntry
from app.models.identity import AuditLog, Permission, Role, RolePermission, User, UserRole
from app.models.media import Media
from app.models.base import MediaType
from app.models.organization import Service
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

    async def fake_translate(src, lang, source=None):
        if not src or not str(src).strip():
            return None
        return f"[{lang}] {src}"

    monkeypatch.setattr(translation_service, "translate_text", fake_translate)
    monkeypatch.setattr(translation_service, "translate_html", fake_translate)
    return fake_translate


async def _audits(db: AsyncSession, action: str | None = None, table: str | None = None):
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if table:
        stmt = stmt.where(AuditLog.table_name == table)
    return (await db.execute(stmt)).scalars().all()


def _program_payload(code: str = "oser-test", **overrides) -> dict:
    payload = {
        "code": code,
        "sigle": "OSER",
        "title": "Parcours OSER",
        "phase": "awareness",
        "tagline": "Oser entreprendre",
        "content_md": "Contenu **riche**",
        "content_html": "<p>Contenu <strong>riche</strong></p>",
        "highlight": "4 crédits",
        "color": "teal",
    }
    payload.update(overrides)
    return payload


def _cohort_payload(code: str = "see-2026", **overrides) -> dict:
    payload = {
        "code": code,
        "label": "SEE 2026",
        "year": 2026,
        "type": "see",
        "focus": "Preuve de concept",
        "summary_md": "Bilan",
        "summary_html": "<p>Bilan</p>",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Dispositifs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_program_requires_auth(client: AsyncClient):
    response = await client.post(f"{BASE}/programs", json=_program_payload())
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_program_without_permission_returns_403(
    authenticated_client: AsyncClient,
):
    response = await authenticated_client.post(f"{BASE}/programs", json=_program_payload())
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_program_fr_only_autofills_translations(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
):
    response = await authenticated_client.post(f"{BASE}/programs", json=_program_payload())
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["title_en"] == "[en] Parcours OSER"
    assert body["title_ar"] == "[ar] Parcours OSER"
    assert body["content_ar_html"] == "[ar] <p>Contenu <strong>riche</strong></p>"
    assert body["content_en_md"] == "[en] Contenu **riche**"
    assert body["highlight_en"] == "[en] 4 crédits"
    assert body["display_order"] == 0
    assert body["active"] is True
    assert body["cover_image_url"] is None

    logs = await _audits(db_session, "entrepreneurship.program.create", "pei_programs")
    assert len(logs) == 1
    assert logs[0].record_id == body["id"]


@pytest.mark.asyncio
async def test_update_program_preserves_manual_translation(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
):
    created = (
        await authenticated_client.post(
            f"{BASE}/programs", json=_program_payload(title_en="Manual EN")
        )
    ).json()
    assert created["title_en"] == "Manual EN"

    response = await authenticated_client.patch(
        f"{BASE}/programs/{created['id']}", json={"title": "Parcours OSER modifié"}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "Parcours OSER modifié"
    assert body["title_en"] == "Manual EN"

    logs = await _audits(db_session, "entrepreneurship.program.update", "pei_programs")
    assert len(logs) == 1
    assert logs[0].old_values == {"title": "Parcours OSER"}
    assert logs[0].new_values == {"title": "Parcours OSER modifié"}


@pytest.mark.asyncio
async def test_program_duplicate_code_returns_409(
    authenticated_client: AsyncClient,
    entrepreneurship_permissions,
    translator_stub,
):
    first = await authenticated_client.post(f"{BASE}/programs", json=_program_payload("mti"))
    assert first.status_code == 201
    dup = await authenticated_client.post(f"{BASE}/programs", json=_program_payload("mti"))
    assert dup.status_code == 409

    other = await authenticated_client.post(f"{BASE}/programs", json=_program_payload("fse"))
    patch = await authenticated_client.patch(
        f"{BASE}/programs/{other.json()['id']}", json={"code": "mti"}
    )
    assert patch.status_code == 409


@pytest.mark.asyncio
async def test_program_invalid_color_and_code_return_422(
    authenticated_client: AsyncClient,
    entrepreneurship_permissions,
    translator_stub,
):
    bad_color = await authenticated_client.post(
        f"{BASE}/programs", json=_program_payload(color="green")
    )
    assert bad_color.status_code == 422
    bad_code = await authenticated_client.post(
        f"{BASE}/programs", json=_program_payload(code="Pas Bon")
    )
    assert bad_code.status_code == 422


@pytest.mark.asyncio
async def test_get_unknown_program_returns_404(
    authenticated_client: AsyncClient, entrepreneurship_permissions
):
    assert (await authenticated_client.get(f"{BASE}/programs/{uuid4()}")).status_code == 404
    assert (await authenticated_client.get(f"{BASE}/programs/pas-un-uuid")).status_code == 404


@pytest.mark.asyncio
async def test_list_programs_filters_and_pagination(
    authenticated_client: AsyncClient,
    entrepreneurship_permissions,
    translator_stub,
):
    await authenticated_client.post(f"{BASE}/programs", json=_program_payload("a-prog", title="Alpha"))
    await authenticated_client.post(
        f"{BASE}/programs", json=_program_payload("b-prog", title="Beta", phase="funding")
    )
    all_items = await authenticated_client.get(f"{BASE}/programs")
    assert all_items.status_code == 200
    assert all_items.json()["total"] == 2
    assert all_items.json()["page_size"] == 50

    by_phase = await authenticated_client.get(f"{BASE}/programs", params={"phase": "funding"})
    assert [i["code"] for i in by_phase.json()["items"]] == ["b-prog"]

    by_q = await authenticated_client.get(f"{BASE}/programs", params={"q": "alp"})
    assert [i["code"] for i in by_q.json()["items"]] == ["a-prog"]

    too_big = await authenticated_client.get(f"{BASE}/programs", params={"page_size": 101})
    assert too_big.status_code == 422


@pytest.mark.asyncio
async def test_reorder_programs(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
):
    ids = []
    for code in ("p-one", "p-two", "p-three"):
        resp = await authenticated_client.post(f"{BASE}/programs", json=_program_payload(code))
        ids.append(resp.json()["id"])

    incomplete = await authenticated_client.patch(
        f"{BASE}/programs/reorder", json={"ids": ids[:2]}
    )
    assert incomplete.status_code == 422

    unknown = await authenticated_client.patch(
        f"{BASE}/programs/reorder", json={"ids": [*ids, str(uuid4())]}
    )
    assert unknown.status_code == 422

    reversed_ids = list(reversed(ids))
    response = await authenticated_client.patch(
        f"{BASE}/programs/reorder", json={"ids": reversed_ids}
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"updated": 2}  # l'élément du milieu ne bouge pas

    rows = (
        await db_session.execute(
            select(PeiProgram.id, PeiProgram.display_order)
            .execution_options(populate_existing=True)
            .order_by(PeiProgram.display_order)
        )
    ).all()
    assert [str(r[0]) for r in rows] == reversed_ids
    assert [r[1] for r in rows] == [0, 1, 2]

    logs = await _audits(db_session, "entrepreneurship.program.reorder", "pei_programs")
    assert len(logs) == 1
    assert logs[0].record_id is None
    assert logs[0].new_values == {"ids": reversed_ids}


@pytest.mark.asyncio
async def test_toggle_program_active_and_delete(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
):
    created = (await authenticated_client.post(f"{BASE}/programs", json=_program_payload())).json()

    response = await authenticated_client.patch(
        f"{BASE}/programs/{created['id']}/active", json={"active": False}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["active"] is False
    assert set(body) == {"id", "active", "updated_at"}
    assert len(await _audits(db_session, "entrepreneurship.program.deactivate", "pei_programs")) == 1

    await authenticated_client.patch(f"{BASE}/programs/{created['id']}/active", json={"active": True})
    assert len(await _audits(db_session, "entrepreneurship.program.activate", "pei_programs")) == 1

    delete = await authenticated_client.delete(f"{BASE}/programs/{created['id']}")
    assert delete.status_code == 204
    assert (await authenticated_client.get(f"{BASE}/programs/{created['id']}")).status_code == 404
    delete_logs = await _audits(db_session, "entrepreneurship.program.delete", "pei_programs")
    assert len(delete_logs) == 1
    assert delete_logs[0].old_values["code"] == "oser-test"

    # Une ligne d'audit par écriture : create, deactivate, activate, delete
    assert len(await _audits(db_session, table="pei_programs")) == 4


@pytest.mark.asyncio
async def test_program_cover_image_url_resolved(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
):
    media = Media(
        id=str(uuid4()), name="visuel.jpg", type=MediaType.IMAGE, url="uploads/visuel.jpg"
    )
    db_session.add(media)
    await db_session.commit()

    response = await authenticated_client.post(
        f"{BASE}/programs", json=_program_payload(cover_image_external_id=media.id)
    )
    assert response.status_code == 201, response.text
    assert response.json()["cover_image_url"] == f"/api/public/media/{media.id}/download"

    bad = await authenticated_client.post(
        f"{BASE}/programs", json=_program_payload("autre", cover_image_external_id="xyz")
    )
    assert bad.status_code == 422


@pytest.mark.asyncio
async def test_translate_program_preview_without_persistence(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
):
    response = await authenticated_client.post(
        f"{BASE}/programs/translate", json={"title": "Titre", "content_html": "<p>x</p>"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title_en"] == "[en] Titre"
    assert body["content_ar_html"] == "[ar] <p>x</p>"
    assert body["tagline_en"] is None
    assert (await db_session.execute(select(PeiProgram))).scalars().all() == []


# ---------------------------------------------------------------------------
# Cohortes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_cohort_with_translation(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
):
    response = await authenticated_client.post(f"{BASE}/cohorts", json=_cohort_payload())
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["label_en"] == "[en] SEE 2026"
    assert body["focus_ar"] == "[ar] Preuve de concept"
    assert body["summary_en_html"] == "[en] <p>Bilan</p>"
    assert body["type"] == "see"
    assert len(await _audits(db_session, "entrepreneurship.cohort.create", "pei_cohorts")) == 1


@pytest.mark.asyncio
async def test_cohort_validation_errors(
    authenticated_client: AsyncClient,
    entrepreneurship_permissions,
    translator_stub,
):
    assert (await authenticated_client.post(f"{BASE}/cohorts", json=_cohort_payload("fse-1"))).status_code == 201
    dup = await authenticated_client.post(f"{BASE}/cohorts", json=_cohort_payload("fse-1"))
    assert dup.status_code == 409

    year = await authenticated_client.post(f"{BASE}/cohorts", json=_cohort_payload("old", year=1999))
    assert year.status_code == 422

    bad_type = await authenticated_client.post(
        f"{BASE}/cohorts", json=_cohort_payload("bad", type="xyz")
    )
    assert bad_type.status_code == 422


@pytest.mark.asyncio
async def test_cohort_reorder_toggle_and_delete(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
):
    ids = []
    for code in ("fse-1", "fse-2", "fse-3"):
        resp = await authenticated_client.post(f"{BASE}/cohorts", json=_cohort_payload(code))
        ids.append(resp.json()["id"])

    new_order = [ids[2], ids[0], ids[1]]
    reorder = await authenticated_client.patch(f"{BASE}/cohorts/reorder", json={"ids": new_order})
    assert reorder.status_code == 200
    listing = await authenticated_client.get(f"{BASE}/cohorts")
    items = listing.json()["items"]
    assert [i["id"] for i in items] == new_order
    assert [i["display_order"] for i in items] == [0, 1, 2]

    toggle = await authenticated_client.patch(f"{BASE}/cohorts/{ids[0]}/active", json={"active": False})
    assert toggle.status_code == 200
    assert toggle.json()["active"] is False
    assert len(await _audits(db_session, "entrepreneurship.cohort.deactivate", "pei_cohorts")) == 1

    inactive = await authenticated_client.get(f"{BASE}/cohorts", params={"active": False})
    assert [i["id"] for i in inactive.json()["items"]] == [ids[0]]

    delete = await authenticated_client.delete(f"{BASE}/cohorts/{ids[1]}")
    assert delete.status_code == 204
    assert len(await _audits(db_session, "entrepreneurship.cohort.delete", "pei_cohorts")) == 1


@pytest.mark.asyncio
async def test_update_cohort(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
):
    created = (await authenticated_client.post(f"{BASE}/cohorts", json=_cohort_payload())).json()
    response = await authenticated_client.patch(
        f"{BASE}/cohorts/{created['id']}", json={"year": 2027, "focus_en": "Manual"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["year"] == 2027
    assert response.json()["focus_en"] == "Manual"

    null_label = await authenticated_client.patch(
        f"{BASE}/cohorts/{created['id']}", json={"label": None}
    )
    assert null_label.status_code == 422
    assert len(await _audits(db_session, "entrepreneurship.cohort.update", "pei_cohorts")) == 1


# ---------------------------------------------------------------------------
# Ressources
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resource_document_without_media_returns_422(
    authenticated_client: AsyncClient, entrepreneurship_permissions, translator_stub
):
    response = await authenticated_client.post(
        f"{BASE}/resources", json={"title": "Guide", "type": "document"}
    )
    assert response.status_code == 422
    assert "Un document de la médiathèque est requis pour le type document" in response.text


@pytest.mark.asyncio
async def test_resource_link_invalid_url_returns_422(
    authenticated_client: AsyncClient, entrepreneurship_permissions, translator_stub
):
    response = await authenticated_client.post(
        f"{BASE}/resources", json={"title": "Lien", "type": "link", "url": "pas-une-url"}
    )
    assert response.status_code == 422
    assert "URL invalide" in response.text

    missing = await authenticated_client.post(
        f"{BASE}/resources", json={"title": "Vidéo", "type": "video"}
    )
    assert missing.status_code == 422
    assert "Une URL est requise pour le type lien ou vidéo" in missing.text


@pytest.mark.asyncio
async def test_resource_link_created_publish_cycle_and_categories(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
):
    response = await authenticated_client.post(
        f"{BASE}/resources",
        json={
            "title": "Bpifrance",
            "type": "link",
            "url": "https://www.bpifrance.fr/",
            "category": "Financement",
        },
    )
    assert response.status_code == 201, response.text
    link = response.json()
    assert link["category_en"] == "[en] Financement"
    assert link["is_published"] is False
    assert link["published_at"] is None
    assert link["media_url"] is None

    await authenticated_client.post(
        f"{BASE}/resources",
        json={"title": "Statuts", "type": "link", "url": "https://example.org", "category": "Juridique"},
    )
    await authenticated_client.post(
        f"{BASE}/resources",
        json={"title": "Autre financement", "type": "video", "url": "https://youtu.be/x", "category": "Financement"},
    )

    pub = await authenticated_client.patch(
        f"{BASE}/resources/{link['id']}/publish", json={"is_published": True}
    )
    assert pub.status_code == 200
    first_at = pub.json()["published_at"]
    assert first_at is not None

    unpub = await authenticated_client.patch(
        f"{BASE}/resources/{link['id']}/publish", json={"is_published": False}
    )
    assert unpub.status_code == 200
    assert unpub.json()["is_published"] is False
    assert unpub.json()["published_at"] == first_at

    assert len(await _audits(db_session, "entrepreneurship.resource.publish", "pei_resources")) == 1
    assert len(await _audits(db_session, "entrepreneurship.resource.unpublish", "pei_resources")) == 1

    categories = await authenticated_client.get(f"{BASE}/resources/categories")
    assert categories.status_code == 200
    assert categories.json() == ["Financement", "Juridique"]

    filtered = await authenticated_client.get(f"{BASE}/resources", params={"category": "Financement"})
    assert filtered.json()["total"] == 2
    assert {i["title"] for i in filtered.json()["items"]} == {"Bpifrance", "Autre financement"}


@pytest.mark.asyncio
async def test_resource_update_revalidates_merged_source(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
):
    media = Media(id=str(uuid4()), name="guide.pdf", type=MediaType.DOCUMENT, url="uploads/guide.pdf")
    db_session.add(media)
    await db_session.commit()

    created = await authenticated_client.post(
        f"{BASE}/resources",
        json={"title": "Guide", "type": "document", "media_external_id": media.id, "is_published": True},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["media_url"] == f"/api/public/media/{media.id}/download"
    assert body["published_at"] is not None

    # Passage en lien sans URL → refusé sur l'objet fusionné
    bad = await authenticated_client.patch(f"{BASE}/resources/{body['id']}", json={"type": "link"})
    assert bad.status_code == 422
    assert "Une URL est requise" in bad.text

    ok = await authenticated_client.patch(
        f"{BASE}/resources/{body['id']}", json={"type": "link", "url": "https://example.org/guide"}
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["type"] == "link"

    delete = await authenticated_client.delete(f"{BASE}/resources/{body['id']}")
    assert delete.status_code == 204
    assert len(await _audits(db_session, "entrepreneurship.resource.delete", "pei_resources")) == 1


@pytest.mark.asyncio
async def test_reorder_resources(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
):
    ids = []
    for i in range(3):
        resp = await authenticated_client.post(
            f"{BASE}/resources", json={"title": f"R{i}", "type": "link", "url": f"https://example.org/{i}"}
        )
        ids.append(resp.json()["id"])
    response = await authenticated_client.patch(
        f"{BASE}/resources/reorder", json={"ids": list(reversed(ids))}
    )
    assert response.status_code == 200
    listing = (await authenticated_client.get(f"{BASE}/resources")).json()["items"]
    assert [i["id"] for i in listing] == list(reversed(ids))
    assert len(await _audits(db_session, "entrepreneurship.resource.reorder", "pei_resources")) == 1


# ---------------------------------------------------------------------------
# Tableau de bord et traduction en lot
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_counts_and_dde_service(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
):
    db_session.add_all(
        [
            PeiProgram(code="p-a", title="Programme A", phase=PeiProgramPhase.AWARENESS, active=True),
            PeiProgram(code="p-b", title="Programme B", phase=PeiProgramPhase.FUNDING, active=False),
            PeiResource(title="Lien", type=PeiResourceType.LINK, url="https://example.org", is_published=True),
        ]
    )
    await db_session.commit()

    response = await authenticated_client.get(f"{BASE}/dashboard")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["programs"] == {"active": 1, "total": 2}
    assert body["cohorts"] == {"active": 0, "total": 0}
    assert body["resources"] == {"published": 1, "total": 1}
    assert body["dde_service"] == {"id": None, "name": None}

    service = Service(id=str(uuid4()), name="Direction du Développement et de l'Entrepreneuriat")
    db_session.add(service)
    db_session.add(
        EditorialContent(
            key="entrepreneurship.dde_service_id",
            value=service.id,
            value_type=EditorialValueType.TEXT,
        )
    )
    await db_session.commit()

    body = (await authenticated_client.get(f"{BASE}/dashboard")).json()
    assert body["dde_service"] == {
        "id": service.id,
        "name": "Direction du Développement et de l'Entrepreneuriat",
    }


@pytest.mark.asyncio
async def test_translate_missing_is_idempotent(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    translator_stub,
):
    db_session.add_all(
        [
            PeiProgram(code="p-a", title="Programme A", phase=PeiProgramPhase.AWARENESS),
            PeiProgram(code="p-b", title="Programme B", phase=PeiProgramPhase.FUNDING),
            PeiCohort(code="fse-1", label="FSE 1", year=2023, type=PeiCohortType.FSE),
        ]
    )
    await db_session.commit()

    first = await authenticated_client.post(f"{BASE}/translate-missing")
    assert first.status_code == 200, first.text
    assert first.json() == {"programs": 2, "cohorts": 1, "resources": 0, "laureates": 0, "faq_see": 0, "complete": True}

    logs = await _audits(db_session, "entrepreneurship.translate_missing")
    assert len(logs) == 1
    assert logs[0].record_id is None
    assert logs[0].table_name is None
    assert logs[0].new_values == {"programs": 2, "cohorts": 1, "resources": 0, "laureates": 0, "faq_see": 0, "complete": True}

    second = await authenticated_client.post(f"{BASE}/translate-missing")
    assert second.json() == {"programs": 0, "cohorts": 0, "resources": 0, "laureates": 0, "faq_see": 0, "complete": True}

    program = (
        await db_session.execute(
            select(PeiProgram).where(PeiProgram.code == "p-a").execution_options(populate_existing=True)
        )
    ).scalar_one()
    assert program.title_ar == "[ar] Programme A"


@pytest.mark.asyncio
async def test_translate_missing_stops_at_time_budget(
    db_session: AsyncSession,
    translator_stub,
):
    """Budget épuisé : travail partiel enregistré, ``complete`` faux, reprise possible."""
    from app.services.entrepreneurship_service import EntrepreneurshipService

    db_session.add_all(
        [
            PeiProgram(code="p-a", title="Programme A", phase=PeiProgramPhase.AWARENESS),
            PeiCohort(code="fse-1", label="FSE 1", year=2023, type=PeiCohortType.FSE),
        ]
    )
    await db_session.commit()

    partial = await EntrepreneurshipService(db_session).translate_missing(user_id=None, time_budget=0)
    assert partial.model_dump() == {"programs": 0, "cohorts": 0, "resources": 0, "laureates": 0, "faq_see": 0, "complete": False}

    full = await EntrepreneurshipService(db_session).translate_missing(user_id=None)
    assert full.model_dump() == {"programs": 1, "cohorts": 1, "resources": 0, "laureates": 0, "faq_see": 0, "complete": True}


@pytest.mark.asyncio
async def test_translate_missing_translates_published_see_faq_entries(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    monkeypatch,
):
    """Étape faq_see (spec 025) : seules les entrées publiées des catégories see-*."""
    from app.services import faq_service

    async def fake_translate(src, lang, source=None):
        if not src or not str(src).strip():
            return None
        return f"[{lang}] {src}"

    monkeypatch.setattr(faq_service, "translate_text", fake_translate)
    monkeypatch.setattr(faq_service, "translate_html", fake_translate)

    see = FaqCategory(id=str(uuid4()), code="see-t", label_fr="SEE", is_active=True)
    general = FaqCategory(id=str(uuid4()), code="general", label_fr="Général", is_active=True)
    db_session.add_all([see, general])
    await db_session.flush()

    def _entry(category_id: str, slug: str, published: bool) -> FaqEntry:
        return FaqEntry(
            id=str(uuid4()),
            category_id=category_id,
            slug=slug,
            question_fr=f"Question {slug} ?",
            answer_fr_md="Réponse",
            answer_fr_html="<p>Réponse</p>",
            is_published=published,
            published_at=datetime.now(timezone.utc) if published else None,
        )

    db_session.add_all(
        [
            _entry(see.id, "see-publiee", True),
            _entry(see.id, "see-brouillon", False),
            _entry(general.id, "general-publiee", True),
        ]
    )
    await db_session.commit()

    response = await authenticated_client.post(f"{BASE}/translate-missing")
    assert response.status_code == 200, response.text
    assert response.json()["faq_see"] == 1
    assert response.json()["complete"] is True

    entries = {
        e.slug: e
        for e in (
            await db_session.execute(select(FaqEntry).execution_options(populate_existing=True))
        ).scalars().all()
    }
    assert entries["see-publiee"].question_en == "[en] Question see-publiee ?"
    assert entries["see-publiee"].answer_ar_html == "[ar] <p>Réponse</p>"
    assert entries["see-publiee"].answer_en_md == "[en] Réponse"
    for slug in ("see-brouillon", "general-publiee"):
        assert entries[slug].question_en is None
        assert entries[slug].answer_ar_html is None

    second = await authenticated_client.post(f"{BASE}/translate-missing")
    assert second.json()["faq_see"] == 0


@pytest.mark.asyncio
async def test_translate_missing_forbidden_without_edit(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Un rôle disposant seulement de entrepreneurship.view reçoit 403."""
    view = Permission(
        id=str(uuid4()),
        code="entrepreneurship.view",
        name_fr="Voir le pôle Entrepreneuriat",
        created_at=datetime.now(timezone.utc),
    )
    role = Role(id=str(uuid4()), code="viewer", name_fr="Lecteur", created_at=datetime.now(timezone.utc))
    user = User(
        id=str(uuid4()),
        email="viewer@usenghor.org",
        password_hash=get_password_hash("Viewer123!"),
        last_name="Lecteur",
        first_name="Pei",
        active=True,
        email_verified=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add_all([view, role, user])
    await db_session.flush()
    db_session.add_all(
        [
            RolePermission(role_id=role.id, permission_id=view.id),
            UserRole(user_id=user.id, role_id=role.id),
        ]
    )
    await db_session.commit()

    token = create_access_token({"sub": user.id, "type": "access"})
    headers = {"Authorization": f"Bearer {token}"}

    assert (await client.get(f"{BASE}/dashboard", headers=headers)).status_code == 200
    response = await client.post(f"{BASE}/translate-missing", headers=headers)
    assert response.status_code == 403
