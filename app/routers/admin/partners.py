"""
Router Admin - Partenaires
==========================

Endpoints CRUD pour la gestion des partenaires.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.partner import Partner, PartnerType
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.partner import (
    PartnerCreate,
    PartnerRead,
    PartnerReorder,
    PartnerUpdate,
)
from app.services.partner_service import PartnerService

router = APIRouter(prefix="/partners", tags=["Partners"])


@router.get("", response_model=dict)
async def list_partners(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur nom ou description"),
    partner_type: PartnerType | None = Query(None, description="Filtrer par type"),
    country_id: str | None = Query(None, description="Filtrer par pays"),
    active: bool | None = Query(None, description="Filtrer par statut actif"),
    _: bool = Depends(PermissionChecker("partners.view")),
) -> dict:
    """Liste les partenaires avec pagination et filtres."""
    service = PartnerService(db)
    query = await service.get_partners(
        search=search,
        partner_type=partner_type,
        country_id=country_id,
        active=active,
    )
    return await paginate(db, query, pagination, Partner)


@router.get("/{partner_id}", response_model=PartnerRead)
async def get_partner(
    partner_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("partners.view")),
) -> Partner:
    """Récupère un partenaire par son ID."""
    service = PartnerService(db)
    partner = await service.get_partner_by_id(partner_id)
    if not partner:
        raise NotFoundException("Partenaire non trouvé")
    return partner


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_partner(
    partner_data: PartnerCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("partners.create")),
) -> IdResponse:
    """Crée un nouveau partenaire."""
    service = PartnerService(db)
    partner = await service.create_partner(
        name=partner_data.name,
        partner_type=partner_data.type,
        description=partner_data.description,
        logo_external_id=partner_data.logo_external_id,
        country_external_id=partner_data.country_external_id,
        website=partner_data.website,
        email=partner_data.email,
        phone=partner_data.phone,
        display_order=partner_data.display_order,
        active=partner_data.active,
    )
    return IdResponse(id=partner.id, message="Partenaire créé avec succès")


@router.put("/{partner_id}", response_model=PartnerRead)
async def update_partner(
    partner_id: str,
    partner_data: PartnerUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("partners.edit")),
) -> Partner:
    """Met à jour un partenaire."""
    service = PartnerService(db)
    update_dict = partner_data.model_dump(exclude_unset=True)
    return await service.update_partner(partner_id, **update_dict)


@router.delete("/{partner_id}", response_model=MessageResponse)
async def delete_partner(
    partner_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("partners.delete")),
) -> MessageResponse:
    """Supprime un partenaire."""
    service = PartnerService(db)
    await service.delete_partner(partner_id)
    return MessageResponse(message="Partenaire supprimé avec succès")


@router.post("/{partner_id}/toggle-active", response_model=PartnerRead)
async def toggle_partner_active(
    partner_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("partners.edit")),
) -> Partner:
    """Bascule le statut actif d'un partenaire."""
    service = PartnerService(db)
    return await service.toggle_partner_active(partner_id)


@router.put("/reorder", response_model=list[PartnerRead])
async def reorder_partners(
    reorder_data: PartnerReorder,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("partners.edit")),
) -> list[Partner]:
    """Réordonne les partenaires."""
    service = PartnerService(db)
    return await service.reorder_partners(reorder_data.partner_ids)
