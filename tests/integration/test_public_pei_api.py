"""
Tests d'intégration — API publique PEI : portraits et partenaires du pôle
========================================================================

Spec : specs/022-pei-laureates-partners/contracts/public-api.md
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import MediaType
from app.models.entrepreneurship import (
    PeiCohort,
    PeiCohortType,
    PeiLaureate,
    PeiLaureateType,
    PeiPartner,
    PeiPartnerFamily,
)
from app.models.media import Media
from app.models.partner import Partner, PartnerType

BASE = "/api/public/entrepreneurship"
CACHE_CONTROL = "public, max-age=60, stale-while-revalidate=300"


def _laureate(cohort: PeiCohort, order: int, **overrides) -> PeiLaureate:
    values = {
        "cohort_id": cohort.id,
        "type": PeiLaureateType.FSE_LAUREATE
        if cohort.type == PeiCohortType.FSE
        else PeiLaureateType.STUDENT_ENTREPRENEUR,
        "full_name": f"Portrait {cohort.code} {order}",
        "project_name": "Projet",
        "is_published": True,
        "display_order": order,
    }
    values.update(overrides)
    return PeiLaureate(**values)


async def _seed_laureates(db: AsyncSession) -> dict:
    photo = Media(id=str(uuid4()), name="awa.jpg", type=MediaType.IMAGE, url="uploads/awa.jpg")
    fse1 = PeiCohort(code="fse-1", label="FSE 1", label_en="FSE 1 EN", year=2023, type=PeiCohortType.FSE, display_order=1)
    fse2 = PeiCohort(code="fse-2", label="FSE 2", year=2024, type=PeiCohortType.FSE, display_order=2)
    fse3 = PeiCohort(code="fse-3", label="FSE 3", year=2025, type=PeiCohortType.FSE, display_order=3, active=False)
    see = PeiCohort(code="see-2026", label="SEE 2026", year=2026, type=PeiCohortType.SEE, display_order=0)
    empty = PeiCohort(code="see-2027", label="SEE 2027", year=2027, type=PeiCohortType.SEE, display_order=4)
    db.add_all([photo, fse1, fse2, fse3, see, empty])
    await db.flush()
    db.add_all(
        [
            _laureate(fse1, 1, full_name="Second", grant_amount=Decimal("3000.00")),
            _laureate(
                fse1,
                0,
                full_name="Premier",
                photo_external_id=photo.id,
                grant_amount=Decimal("5000.00"),
                quote="Merci",
                quote_en="",
                is_featured=True,
            ),
            _laureate(fse2, 0, full_name="Brouillon", is_published=False),
            _laureate(fse3, 0, full_name="Cohorte inactive", grant_amount=Decimal("9000.00")),
            _laureate(see, 0, full_name="Étudiante"),
            _laureate(empty, 0, full_name="Brouillon SEE", is_published=False),
        ]
    )
    await db.commit()
    return {"photo": photo}


# ---------------------------------------------------------------------------
# Portraits
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_public_laureates_grouped_by_active_cohort(client: AsyncClient, db_session: AsyncSession):
    seeded = await _seed_laureates(db_session)

    response = await client.get(f"{BASE}/laureates")
    assert response.status_code == 200
    assert response.headers["cache-control"] == CACHE_CONTROL
    body = response.json()

    assert [g["cohort"]["code"] for g in body["groups"]] == ["see-2026", "fse-1"]
    fse1 = body["groups"][1]
    assert [l["full_name"] for l in fse1["laureates"]] == ["Premier", "Second"]
    assert "summary_md" not in fse1["cohort"]

    first = fse1["laureates"][0]
    assert first["photo_url"] == f"/api/public/media/{seeded['photo'].id}/download"
    assert first["cohort_label"] == "FSE 1"
    assert first["cohort_label_en"] == "FSE 1 EN"
    assert first["is_featured"] is True
    assert first["quote_en"] == ""
    for hidden in ("photo_external_id", "grant_amount", "published_at", "created_by", "cohort_id"):
        assert hidden not in first

    assert body["stats"] == {"laureates": 3, "cohorts": 2, "max_grant_amount": "5000.00"}


@pytest.mark.asyncio
async def test_public_laureates_type_filter(client: AsyncClient, db_session: AsyncSession):
    await _seed_laureates(db_session)
    body = (await client.get(f"{BASE}/laureates", params={"type": "student_entrepreneur"})).json()
    assert [g["cohort"]["code"] for g in body["groups"]] == ["see-2026"]
    assert body["stats"] == {"laureates": 1, "cohorts": 1, "max_grant_amount": None}


@pytest.mark.asyncio
async def test_public_laureates_empty(client: AsyncClient, db_session: AsyncSession):
    body = (await client.get(f"{BASE}/laureates")).json()
    assert body == {"groups": [], "stats": {"laureates": 0, "cohorts": 0, "max_grant_amount": None}}


# ---------------------------------------------------------------------------
# Partenaires du pôle
# ---------------------------------------------------------------------------


async def _seed_partners(db: AsyncSession) -> dict[str, Partner]:
    logo = Media(id=str(uuid4()), name="auf.png", type=MediaType.IMAGE, url="uploads/auf.png")
    db.add(logo)
    await db.flush()
    items = {
        "campus": Partner(name="Campus France", description="Agence", description_en="Agency", type=PartnerType.OTHER, website="https://www.campusfrance.org", active=True),
        "auf": Partner(name="AUF", type=PartnerType.CHARTER_OPERATOR, logo_external_id=logo.id, active=True),
        "oif": Partner(name="OIF", type=PartnerType.CHARTER_OPERATOR, active=True),
        "inactive": Partner(name="Inactif", type=PartnerType.OTHER, active=False),
    }
    db.add_all(items.values())
    await db.flush()
    db.add_all(
        [
            PeiPartner(partner_id=items["campus"].id, family=PeiPartnerFamily.ACADEMIC, display_order=0),
            PeiPartner(partner_id=items["oif"].id, family=PeiPartnerFamily.INTERNATIONAL, display_order=1),
            PeiPartner(partner_id=items["auf"].id, family=PeiPartnerFamily.INTERNATIONAL, display_order=0),
            PeiPartner(partner_id=items["inactive"].id, family=PeiPartnerFamily.INTERNATIONAL, display_order=2),
        ]
    )
    await db.commit()
    return items


@pytest.mark.asyncio
async def test_public_partners_three_families(client: AsyncClient, db_session: AsyncSession):
    items = await _seed_partners(db_session)

    response = await client.get(f"{BASE}/partners")
    assert response.status_code == 200
    assert response.headers["cache-control"] == CACHE_CONTROL
    body = response.json()

    assert [g["family"] for g in body] == ["academic", "support", "international"]
    assert body[1]["partners"] == []
    assert [p["name"] for p in body[2]["partners"]] == ["AUF", "OIF"]

    campus = body[0]["partners"][0]
    assert campus["description_en"] == "Agency"
    assert campus["website"] == "https://www.campusfrance.org"
    assert campus["logo_url"] is None
    auf = body[2]["partners"][0]
    assert auf["logo_url"] == f"/api/public/media/{items['auf'].logo_external_id}/download"
    for partner in (campus, auf):
        assert "logo_external_id" not in partner
        assert "email" not in partner


@pytest.mark.asyncio
async def test_public_partners_deleted_partner_disappears(client: AsyncClient, db_session: AsyncSession):
    items = await _seed_partners(db_session)
    await db_session.execute(delete(Partner).where(Partner.id == items["auf"].id))
    await db_session.commit()

    response = await client.get(f"{BASE}/partners")
    assert response.status_code == 200
    assert [p["name"] for p in response.json()[2]["partners"]] == ["OIF"]


@pytest.mark.asyncio
async def test_public_partners_empty_returns_three_empty_families(client: AsyncClient, db_session: AsyncSession):
    body = (await client.get(f"{BASE}/partners")).json()
    assert body == [
        {"family": "academic", "partners": []},
        {"family": "support", "partners": []},
        {"family": "international", "partners": []},
    ]
