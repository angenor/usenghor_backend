"""
Tests d'intégration — API publique Entrepreneuriat (PEI)
========================================================

Spec : specs/021-pei-entrepreneurship-core/contracts/public-api.md
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import MediaType
from app.models.entrepreneurship import (
    PeiCohort,
    PeiCohortType,
    PeiProgram,
    PeiProgramPhase,
    PeiResource,
    PeiResourceType,
)
from app.models.media import Media

BASE = "/api/public/entrepreneurship"
CACHE_CONTROL = "public, max-age=60, stale-while-revalidate=300"


async def _seed_programs(db: AsyncSession) -> None:
    db.add_all(
        [
            PeiProgram(
                code="mti",
                title="Mature Ton Idée",
                phase=PeiProgramPhase.PRE_INCUBATION,
                content_md="md",
                content_html="<p>html</p>",
                color="blue",
                display_order=1,
                active=True,
            ),
            PeiProgram(
                code="oser",
                title="Parcours OSER",
                phase=PeiProgramPhase.AWARENESS,
                color="teal",
                display_order=0,
                active=True,
            ),
            PeiProgram(
                code="inactif",
                title="Dispositif inactif",
                phase=PeiProgramPhase.FUNDING,
                display_order=2,
                active=False,
            ),
        ]
    )
    await db.commit()


# ---------------------------------------------------------------------------
# Dispositifs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_public_programs_only_active_sorted(client: AsyncClient, db_session: AsyncSession):
    await _seed_programs(db_session)

    response = await client.get(f"{BASE}/programs")
    assert response.status_code == 200
    assert response.headers["cache-control"] == CACHE_CONTROL
    body = response.json()
    assert [p["code"] for p in body] == ["oser", "mti"]
    for item in body:
        assert "content_md" not in item
        assert "content_en_md" not in item
        assert "cover_image_external_id" not in item
        assert "cover_image_url" in item
    assert body[1]["content_html"] == "<p>html</p>"
    assert body[1]["phase"] == "pre_incubation"


@pytest.mark.asyncio
async def test_public_program_by_code(client: AsyncClient, db_session: AsyncSession):
    await _seed_programs(db_session)

    ok = await client.get(f"{BASE}/programs/mti")
    assert ok.status_code == 200
    assert ok.json()["title"] == "Mature Ton Idée"
    assert ok.headers["cache-control"] == CACHE_CONTROL

    assert (await client.get(f"{BASE}/programs/inactif")).status_code == 404
    assert (await client.get(f"{BASE}/programs/inconnu")).status_code == 404


@pytest.mark.asyncio
async def test_public_endpoints_are_read_only(client: AsyncClient):
    response = await client.post(f"{BASE}/programs", json={"code": "x"})
    assert response.status_code == 405
    assert (await client.delete(f"{BASE}/cohorts/fse-1")).status_code == 405


# ---------------------------------------------------------------------------
# Cohortes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_public_cohorts(client: AsyncClient, db_session: AsyncSession):
    db_session.add_all(
        [
            PeiCohort(code="fse-1", label="FSE 1", year=2023, type=PeiCohortType.FSE, display_order=2,
                      summary_md="md", summary_html="<p>bilan</p>"),
            PeiCohort(code="fse-3", label="FSE 3", year=2025, type=PeiCohortType.FSE, display_order=0),
            PeiCohort(code="see-2026", label="SEE 2026", year=2026, type=PeiCohortType.SEE, display_order=1),
            PeiCohort(code="fse-2", label="FSE 2", year=2024, type=PeiCohortType.FSE, display_order=3,
                      active=False),
        ]
    )
    await db_session.commit()

    response = await client.get(f"{BASE}/cohorts")
    assert response.status_code == 200
    assert response.headers["cache-control"] == CACHE_CONTROL
    body = response.json()
    assert [c["code"] for c in body] == ["fse-3", "see-2026", "fse-1"]
    for item in body:
        assert "summary_md" not in item
        assert "summary_en_md" not in item
    assert body[2]["summary_html"] == "<p>bilan</p>"

    see = await client.get(f"{BASE}/cohorts", params={"type": "see"})
    assert [c["code"] for c in see.json()] == ["see-2026"]

    assert (await client.get(f"{BASE}/cohorts/fse-3")).status_code == 200
    assert (await client.get(f"{BASE}/cohorts/fse-2")).status_code == 404
    assert (await client.get(f"{BASE}/cohorts/inconnue")).status_code == 404


# ---------------------------------------------------------------------------
# Ressources
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_public_resources(client: AsyncClient, db_session: AsyncSession):
    media = Media(id=str(uuid4()), name="guide.pdf", type=MediaType.DOCUMENT, url="uploads/guide.pdf")
    db_session.add(media)
    await db_session.flush()
    db_session.add_all(
        [
            PeiResource(title="Guide", type=PeiResourceType.DOCUMENT, media_external_id=media.id,
                        category="Juridique", is_published=True, display_order=1),
            PeiResource(title="Bpifrance", type=PeiResourceType.LINK, url="https://www.bpifrance.fr/",
                        category="Financement", is_published=True, display_order=0),
            PeiResource(title="Brouillon", type=PeiResourceType.LINK, url="https://example.org",
                        category="Financement", is_published=False, display_order=2),
        ]
    )
    await db_session.commit()

    response = await client.get(f"{BASE}/resources")
    assert response.status_code == 200
    assert response.headers["cache-control"] == CACHE_CONTROL
    body = response.json()
    assert [r["title"] for r in body] == ["Bpifrance", "Guide"]
    for item in body:
        assert "media_external_id" not in item

    link, document = body
    assert link["url"] == "https://www.bpifrance.fr/"
    assert link["media_url"] is None
    assert document["media_url"] == f"/api/public/media/{media.id}/download"
    assert document["url"] is None

    by_category = await client.get(f"{BASE}/resources", params={"category": "Financement"})
    assert [r["title"] for r in by_category.json()] == ["Bpifrance"]

    by_type = await client.get(f"{BASE}/resources", params={"type": "document"})
    assert [r["title"] for r in by_type.json()] == ["Guide"]
