"""
Router Public - Services
========================

Endpoints publics pour les services de l'université.
"""

from fastapi import APIRouter, Query

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.schemas.organization import ServicePublic, ServicePublicWithDetails
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=list[ServicePublic])
async def list_services(
    db: DbSession,
    sector_id: str | None = Query(None, description="Filtrer par secteur"),
) -> list:
    """Liste les services actifs, optionnellement filtrés par secteur."""
    service = OrganizationService(db)
    return await service.get_active_services(sector_id=sector_id)


@router.get("/{service_id}", response_model=ServicePublicWithDetails)
async def get_service(
    service_id: str,
    db: DbSession,
) -> ServicePublicWithDetails:
    """Récupère un service par son ID avec ses objectifs, réalisations et projets."""
    org_service = OrganizationService(db)
    svc = await org_service.get_service_with_details(service_id)
    if not svc:
        raise NotFoundException("Service non trouvé")
    return svc
