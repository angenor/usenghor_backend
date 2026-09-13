"""
Router Public - Entrepreneuriat (PEI)
=====================================

Lecture seule, sans authentification : dispositifs et cohortes actifs,
ressources publiées, portraits publiés (cohortes actives) et partenaires du pôle
actifs, triés par ``display_order, created_at``.
Les UUID de média ne sont pas exposés (``cover_image_url`` / ``media_url`` /
``photo_url`` / ``logo_url``). Routes statiques avant les routes ``/{code}``.

Spec : specs/021-pei-entrepreneurship-core/contracts/public-api.md,
specs/022-pei-laureates-partners/contracts/public-api.md
"""

from fastapi import APIRouter, Query, Response

from app.core.dependencies import DbSession
from app.models.entrepreneurship import PeiCohortType, PeiLaureateType, PeiResourceType
from app.schemas.entrepreneurship import (
    PeiCohortPublic,
    PeiLaureatesPublic,
    PeiPartnerFamilyPublic,
    PeiProgramPublic,
    PeiResourcePublic,
)
from app.services.entrepreneurship_service import EntrepreneurshipService

router = APIRouter(prefix="/entrepreneurship", tags=["Entrepreneurship"])


def _cache(response: Response) -> None:
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"


# ---------------------------------------------------------------------------
# Portraits et partenaires du pôle (routes statiques, avant tout ``/{code}``)
# ---------------------------------------------------------------------------


@router.get("/laureates", response_model=PeiLaureatesPublic)
async def list_laureates(
    db: DbSession,
    response: Response,
    type: PeiLaureateType | None = Query(None),  # noqa: A002
) -> PeiLaureatesPublic:
    """Portraits publiés des cohortes actives, groupés par cohorte, avec chiffres."""
    _cache(response)
    return await EntrepreneurshipService(db).list_public_laureates(type=type)


@router.get("/partners", response_model=list[PeiPartnerFamilyPublic])
async def list_partners(db: DbSession, response: Response) -> list[PeiPartnerFamilyPublic]:
    """Partenaires actifs du pôle, groupés en trois familles (ordre fixe)."""
    _cache(response)
    return await EntrepreneurshipService(db).list_public_partners()


# ---------------------------------------------------------------------------
# Dispositifs
# ---------------------------------------------------------------------------


@router.get("/programs", response_model=list[PeiProgramPublic])
async def list_programs(db: DbSession, response: Response) -> list[PeiProgramPublic]:
    """Dispositifs actifs."""
    _cache(response)
    return await EntrepreneurshipService(db).list_public_programs()


@router.get("/programs/{code}", response_model=PeiProgramPublic)
async def get_program(code: str, db: DbSession, response: Response) -> PeiProgramPublic:
    """Dispositif actif par code (404 si inconnu ou inactif)."""
    _cache(response)
    return await EntrepreneurshipService(db).get_public_program(code)


# ---------------------------------------------------------------------------
# Cohortes
# ---------------------------------------------------------------------------


@router.get("/cohorts", response_model=list[PeiCohortPublic])
async def list_cohorts(
    db: DbSession,
    response: Response,
    type: PeiCohortType | None = Query(None),  # noqa: A002
) -> list[PeiCohortPublic]:
    """Cohortes actives (filtre optionnel ``type=fse|see``)."""
    _cache(response)
    return await EntrepreneurshipService(db).list_public_cohorts(type=type)


@router.get("/cohorts/{code}", response_model=PeiCohortPublic)
async def get_cohort(code: str, db: DbSession, response: Response) -> PeiCohortPublic:
    """Cohorte active par code (404 si inconnue ou inactive)."""
    _cache(response)
    return await EntrepreneurshipService(db).get_public_cohort(code)


# ---------------------------------------------------------------------------
# Ressources
# ---------------------------------------------------------------------------


@router.get("/resources", response_model=list[PeiResourcePublic])
async def list_resources(
    db: DbSession,
    response: Response,
    type: PeiResourceType | None = Query(None),  # noqa: A002
    category: str | None = Query(None, description="Catégorie FR exacte"),
) -> list[PeiResourcePublic]:
    """Ressources publiées (filtres optionnels ``type`` et ``category``)."""
    _cache(response)
    return await EntrepreneurshipService(db).list_public_resources(
        type=type, category=category
    )
