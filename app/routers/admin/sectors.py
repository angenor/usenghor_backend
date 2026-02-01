"""
Router Admin - Secteurs
=======================

Endpoints CRUD pour la gestion des secteurs.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.organization import Sector
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.organization import (
    SectorCreate,
    SectorRead,
    SectorReorder,
    SectorUpdate,
    SectorWithServices,
    ServiceRead,
)
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/sectors", tags=["Sectors"])


@router.get("", response_model=dict)
async def list_sectors(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur code ou nom"),
    active: bool | None = Query(None, description="Filtrer par statut actif"),
    _: bool = Depends(PermissionChecker("organization.view")),
) -> dict:
    """Liste les secteurs avec pagination et filtres."""
    service = OrganizationService(db)
    query = await service.get_sectors(search=search, active=active)
    return await paginate(db, query, pagination, Sector, SectorRead)


@router.get("/{sector_id}", response_model=SectorWithServices)
async def get_sector(
    sector_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> Sector:
    """Récupère un secteur par son ID."""
    service = OrganizationService(db)
    sector = await service.get_sector_by_id(sector_id)
    if not sector:
        raise NotFoundException("Secteur non trouvé")
    return sector


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_sector(
    sector_data: SectorCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> IdResponse:
    """Crée un nouveau secteur."""
    service = OrganizationService(db)
    sector = await service.create_sector(
        code=sector_data.code,
        name=sector_data.name,
        description=sector_data.description,
        mission=sector_data.mission,
        icon_external_id=sector_data.icon_external_id,
        cover_image_external_id=sector_data.cover_image_external_id,
        head_external_id=sector_data.head_external_id,
        display_order=sector_data.display_order,
        active=sector_data.active,
    )
    return IdResponse(id=sector.id, message="Secteur créé avec succès")


@router.put("/{sector_id}", response_model=SectorRead)
async def update_sector(
    sector_id: str,
    sector_data: SectorUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> Sector:
    """Met à jour un secteur."""
    service = OrganizationService(db)
    update_dict = sector_data.model_dump(exclude_unset=True)
    return await service.update_sector(sector_id, **update_dict)


@router.delete("/{sector_id}", response_model=MessageResponse)
async def delete_sector(
    sector_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> MessageResponse:
    """Supprime un secteur."""
    service = OrganizationService(db)
    await service.delete_sector(sector_id)
    return MessageResponse(message="Secteur supprimé avec succès")


@router.post("/{sector_id}/toggle-active", response_model=SectorRead)
async def toggle_sector_active(
    sector_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> Sector:
    """Bascule le statut actif d'un secteur."""
    service = OrganizationService(db)
    return await service.toggle_sector_active(sector_id)


@router.post("/{sector_id}/duplicate", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_sector(
    sector_id: str,
    db: DbSession,
    current_user: CurrentUser,
    new_code: str = Query(..., description="Code unique pour le nouveau secteur"),
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> IdResponse:
    """Duplique un secteur avec un nouveau code."""
    service = OrganizationService(db)
    sector = await service.duplicate_sector(sector_id, new_code)
    return IdResponse(id=sector.id, message="Secteur dupliqué avec succès")


@router.put("/reorder", response_model=list[SectorRead])
async def reorder_sectors(
    reorder_data: SectorReorder,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> list[Sector]:
    """Réordonne les secteurs."""
    service = OrganizationService(db)
    return await service.reorder_sectors(reorder_data.sector_ids)


@router.get("/{sector_id}/services", response_model=list[ServiceRead])
async def get_sector_services(
    sector_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> list:
    """Récupère les services d'un secteur."""
    service = OrganizationService(db)
    return await service.get_sector_services(sector_id)
