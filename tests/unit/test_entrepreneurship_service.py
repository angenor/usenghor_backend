"""
Tests unitaires — EntrepreneurshipService
=========================================

Validation de la source des ressources, renumérotation ``_reorder`` et
calcul de ``_next_display_order``.
"""

from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationException
from app.models.entrepreneurship import PeiCohort, PeiCohortType, PeiResourceType
from app.schemas.entrepreneurship import MSG_DOCUMENT_REQUIRED, MSG_URL_REQUIRED
from app.services.entrepreneurship_service import EntrepreneurshipService

validate = EntrepreneurshipService._validate_resource_source


# ---------------------------------------------------------------------------
# _validate_resource_source
# ---------------------------------------------------------------------------


def test_validate_document_with_media_ok():
    validate(SimpleNamespace(type=PeiResourceType.DOCUMENT, media_external_id="x", url=None))


def test_validate_document_without_media_raises():
    with pytest.raises(ValidationException) as exc:
        validate(SimpleNamespace(type="document", media_external_id=None, url="https://a.b"))
    assert exc.value.status_code == 422
    assert exc.value.detail == MSG_DOCUMENT_REQUIRED


def test_validate_link_with_url_ok():
    validate(SimpleNamespace(type=PeiResourceType.LINK, media_external_id=None, url="https://a.b"))


def test_validate_video_without_url_raises():
    with pytest.raises(ValidationException) as exc:
        validate(SimpleNamespace(type=PeiResourceType.VIDEO, media_external_id="x", url="  "))
    assert exc.value.detail == MSG_URL_REQUIRED


# ---------------------------------------------------------------------------
# _reorder / _next_display_order (base de test)
# ---------------------------------------------------------------------------


async def _seed_cohorts(db: AsyncSession, n: int = 3) -> list[str]:
    cohorts = [
        PeiCohort(code=f"fse-{i}", label=f"FSE {i}", year=2023 + i, type=PeiCohortType.FSE, display_order=i)
        for i in range(n)
    ]
    db.add_all(cohorts)
    await db.commit()
    return [c.id for c in cohorts]


@pytest.mark.asyncio
async def test_next_display_order_empty_table(db_session: AsyncSession):
    service = EntrepreneurshipService(db_session)
    assert await service._next_display_order(PeiCohort) == 0


@pytest.mark.asyncio
async def test_next_display_order_after_rows(db_session: AsyncSession):
    await _seed_cohorts(db_session, 2)
    assert await EntrepreneurshipService(db_session)._next_display_order(PeiCohort) == 2


@pytest.mark.asyncio
async def test_reorder_reversed_list_renumbers(db_session: AsyncSession):
    ids = await _seed_cohorts(db_session, 3)
    service = EntrepreneurshipService(db_session)

    result = await service._reorder(
        PeiCohort, list(reversed(ids)), "pei_cohorts", "entrepreneurship.cohort.reorder", None
    )
    assert result.updated == 2

    rows = (
        await db_session.execute(
            select(PeiCohort.id, PeiCohort.display_order).order_by(PeiCohort.display_order)
        )
    ).all()
    assert [str(r[0]) for r in rows] == list(reversed(ids))
    assert [r[1] for r in rows] == [0, 1, 2]


@pytest.mark.asyncio
async def test_reorder_incomplete_list_raises(db_session: AsyncSession):
    ids = await _seed_cohorts(db_session, 3)
    with pytest.raises(ValidationException):
        await EntrepreneurshipService(db_session)._reorder(
            PeiCohort, ids[:2], "pei_cohorts", "entrepreneurship.cohort.reorder", None
        )


@pytest.mark.asyncio
async def test_reorder_unknown_id_raises(db_session: AsyncSession):
    ids = await _seed_cohorts(db_session, 2)
    with pytest.raises(ValidationException):
        await EntrepreneurshipService(db_session)._reorder(
            PeiCohort,
            [*ids, "00000000-0000-0000-0000-000000000000"],
            "pei_cohorts",
            "entrepreneurship.cohort.reorder",
            None,
        )
