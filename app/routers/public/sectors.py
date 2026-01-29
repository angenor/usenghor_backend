"""
Router Public - Secteurs
========================

Endpoints publics pour les secteurs de l'université.
"""

from fastapi import APIRouter

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.schemas.organization import SectorPublic, SectorPublicWithServices
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/sectors", tags=["Sectors"])


@router.get("", response_model=list[SectorPublic])
async def list_sectors(
    db: DbSession,
) -> list:
    """Liste les secteurs actifs triés par ordre d'affichage."""
    service = OrganizationService(db)
    return await service.get_active_sectors()


@router.get("/with-services", response_model=list[SectorPublicWithServices])
async def list_sectors_with_services(
    db: DbSession,
) -> list:
    """Liste les secteurs actifs avec leurs services actifs."""
    service = OrganizationService(db)
    return await service.get_active_sectors_with_active_services()


@router.get("/{code}", response_model=SectorPublicWithServices)
async def get_sector_by_code(
    code: str,
    db: DbSession,
) -> SectorPublicWithServices:
    """Récupère un secteur par son code avec ses services."""
    service = OrganizationService(db)
    sector = await service.get_sector_by_code(code)
    if not sector:
        raise NotFoundException("Secteur non trouvé")
    if not sector.active:
        raise NotFoundException("Secteur non trouvé")
    # Filtrer les services inactifs
    sector.services = [s for s in sector.services if s.active]
    sector.services.sort(key=lambda s: (s.display_order, s.name))
    return sector
