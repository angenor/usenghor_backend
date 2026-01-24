"""
Router Public - Pays
====================

Endpoints publics pour les pays (sans authentification).
"""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession
from app.core.pagination import PaginationParams, paginate
from app.models.core import Country
from app.schemas.core import CountryPublic
from app.services.core_service import CoreService

router = APIRouter(prefix="/countries", tags=["Countries (Public)"])


@router.get("", response_model=dict)
async def list_countries(
    db: DbSession,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur code ou nom"),
) -> dict:
    """Liste les pays actifs avec pagination."""
    service = CoreService(db)
    query = await service.get_countries(search=search, active=True)
    return await paginate(db, query, pagination, Country)


@router.get("/all", response_model=list[CountryPublic])
async def list_all_countries(
    db: DbSession,
) -> list[Country]:
    """Liste tous les pays actifs (sans pagination, pour les selects)."""
    service = CoreService(db)
    query = await service.get_countries(active=True)
    result = await db.execute(query.order_by(Country.name_fr))
    return list(result.scalars().all())


@router.get("/{iso_code}", response_model=CountryPublic)
async def get_country_by_code(
    iso_code: str,
    db: DbSession,
) -> Country:
    """Récupère un pays par son code ISO."""
    service = CoreService(db)
    country = await service.get_country_by_iso_code(iso_code)
    if not country or not country.active:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Pays non trouvé")
    return country
