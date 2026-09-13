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


# ---------------------------------------------------------------------------
# Feature 022 : verbatim, cohérence type / cohorte, reorder scopé
# ---------------------------------------------------------------------------

from app.models.entrepreneurship import PeiLaureate, PeiLaureateType  # noqa: E402
from app.services.entrepreneurship_service import _clamp_text  # noqa: E402


def test_clamp_text_keeps_short_values():
    assert _clamp_text(None) is None
    assert _clamp_text("a" * 600) == "a" * 600


def test_clamp_text_cuts_at_last_space():
    value = ("mot " * 200).strip()  # 799 caractères
    clamped = _clamp_text(value)
    assert len(clamped) <= 600
    assert clamped.endswith("mot…")


def test_clamp_quote_on_object():
    obj = SimpleNamespace(quote="ok", quote_en="x" * 700, quote_ar=None)
    EntrepreneurshipService._clamp_quote(obj)
    assert obj.quote == "ok"
    assert len(obj.quote_en) == 600
    assert obj.quote_ar is None


@pytest.mark.parametrize(
    ("laureate_type", "cohort_type", "ok"),
    [
        (PeiLaureateType.FSE_LAUREATE, PeiCohortType.FSE, True),
        (PeiLaureateType.STUDENT_ENTREPRENEUR, PeiCohortType.SEE, True),
        ("fse_laureate", "see", False),
        (PeiLaureateType.STUDENT_ENTREPRENEUR, PeiCohortType.FSE, False),
    ],
)
def test_assert_laureate_cohort(laureate_type, cohort_type, ok):
    cohort = SimpleNamespace(type=cohort_type)
    if ok:
        EntrepreneurshipService._assert_laureate_cohort(laureate_type, cohort)
    else:
        with pytest.raises(ValidationException):
            EntrepreneurshipService._assert_laureate_cohort(laureate_type, cohort)


@pytest.mark.asyncio
async def test_scoped_reorder_rejects_ids_from_another_cohort(db_session: AsyncSession):
    cohort_ids = await _seed_cohorts(db_session, 2)
    laureates = [
        PeiLaureate(cohort_id=cohort_ids[i % 2], type=PeiLaureateType.FSE_LAUREATE,
                    full_name=f"Portrait {i}", project_name="Projet", display_order=i)
        for i in range(3)
    ]
    db_session.add_all(laureates)
    await db_session.commit()
    in_first = [laureates[0].id, laureates[2].id]

    service = EntrepreneurshipService(db_session)
    with pytest.raises(ValidationException):
        await service._reorder(
            PeiLaureate, [*in_first, laureates[1].id], "pei_laureates",
            "entrepreneurship.laureate.reorder", None, scope={"cohort_id": cohort_ids[0]},
        )

    result = await service._reorder(
        PeiLaureate, list(reversed(in_first)), "pei_laureates",
        "entrepreneurship.laureate.reorder", None, scope={"cohort_id": cohort_ids[0]},
    )
    assert result.updated == 2
    assert await service._next_display_order(PeiLaureate, cohort_id=cohort_ids[1]) == 2
