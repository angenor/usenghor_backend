"""
Router Admin - Demandes de partenariat
=======================================

Endpoints CRUD pour la gestion des demandes de partenariat.
"""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.partnership_request import (
    PartnershipRequest,
    PartnershipRequestStatus,
    PartnershipRequestType,
)
from app.schemas.common import MessageResponse
from app.schemas.partner import PartnerRead
from app.schemas.partnership_request import (
    PartnershipRequestApprove,
    PartnershipRequestRead,
    PartnershipRequestReject,
    PartnershipRequestStats,
)
from app.services.partnership_request_service import PartnershipRequestService

router = APIRouter(prefix="/partnership-requests", tags=["Partnership Requests"])


@router.get("/stats", response_model=PartnershipRequestStats)
async def get_partnership_request_stats(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("partners.view")),
) -> PartnershipRequestStats:
    """Statistiques des demandes de partenariat."""
    service = PartnershipRequestService(db)
    stats = await service.get_stats()
    return PartnershipRequestStats(**stats)


@router.get("", response_model=dict)
async def list_partnership_requests(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur nom, email ou organisation"),
    request_status: PartnershipRequestStatus | None = Query(
        None, alias="status", description="Filtrer par statut",
    ),
    request_type: PartnershipRequestType | None = Query(
        None, alias="type", description="Filtrer par type",
    ),
    _: bool = Depends(PermissionChecker("partners.view")),
) -> dict:
    """Liste les demandes de partenariat avec pagination et filtres."""
    service = PartnershipRequestService(db)
    query = await service.get_requests(
        search=search,
        status=request_status,
        request_type=request_type,
    )
    return await paginate(
        db, query, pagination, PartnershipRequest, PartnershipRequestRead
    )


@router.get("/{request_id}", response_model=PartnershipRequestRead)
async def get_partnership_request(
    request_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("partners.view")),
) -> PartnershipRequest:
    """Récupère une demande de partenariat par son ID."""
    service = PartnershipRequestService(db)
    request = await service.get_request_by_id(request_id)
    if not request:
        raise NotFoundException("Demande de partenariat non trouvée")
    return request


@router.post("/{request_id}/approve", response_model=dict)
async def approve_partnership_request(
    request_id: str,
    data: PartnershipRequestApprove,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("partners.create")),
) -> dict:
    """
    Approuve une demande et crée automatiquement un partenaire.

    Retourne la demande mise à jour et le partenaire créé.
    """
    service = PartnershipRequestService(db)
    updated_request, partner = await service.approve_request(
        request_id=request_id,
        reviewer_id=current_user.id,
        partner_type_override=data.partner_type,
        partner_name_override=data.partner_name,
    )
    return {
        "request": PartnershipRequestRead.model_validate(updated_request),
        "partner": PartnerRead.model_validate(partner),
        "message": "Demande approuvée et partenaire créé avec succès",
    }


@router.post("/{request_id}/reject", response_model=PartnershipRequestRead)
async def reject_partnership_request(
    request_id: str,
    data: PartnershipRequestReject,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("partners.edit")),
) -> PartnershipRequest:
    """Rejette une demande de partenariat."""
    service = PartnershipRequestService(db)
    return await service.reject_request(
        request_id=request_id,
        reviewer_id=current_user.id,
        reason=data.reason,
    )


@router.delete("/{request_id}", response_model=MessageResponse)
async def delete_partnership_request(
    request_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("partners.delete")),
) -> MessageResponse:
    """Supprime une demande de partenariat."""
    service = PartnershipRequestService(db)
    await service.delete_request(request_id)
    return MessageResponse(message="Demande supprimée avec succès")
