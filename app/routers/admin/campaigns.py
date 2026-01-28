"""
Router Admin - Campagnes Newsletter
====================================

Endpoints CRUD pour la gestion des campagnes de newsletter.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.newsletter import CampaignStatus, NewsletterCampaign
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.newsletter import (
    CampaignCreate,
    CampaignRead,
    CampaignSchedule,
    CampaignStatistics,
    CampaignUpdate,
    NewsletterStatistics,
    SendRead,
)
from app.services.newsletter_service import NewsletterService

router = APIRouter(prefix="/campaigns", tags=["Newsletter Campaigns"])


@router.get("", response_model=dict)
async def list_campaigns(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur titre ou sujet"),
    status: CampaignStatus | None = Query(None, description="Filtrer par statut"),
    _: bool = Depends(PermissionChecker("newsletter.view")),
) -> dict:
    """Liste les campagnes avec pagination et filtres."""
    service = NewsletterService(db)
    query = await service.get_campaigns(
        search=search,
        status=status,
    )
    return await paginate(db, query, pagination, NewsletterCampaign)


@router.get("/statistics", response_model=NewsletterStatistics)
async def get_statistics(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.view")),
) -> NewsletterStatistics:
    """Récupère les statistiques globales de la newsletter."""
    service = NewsletterService(db)
    stats = await service.get_statistics()
    return NewsletterStatistics(**stats)


@router.get("/{campaign_id}", response_model=CampaignRead)
async def get_campaign(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.view")),
) -> NewsletterCampaign:
    """Récupère une campagne par son ID."""
    service = NewsletterService(db)
    campaign = await service.get_campaign_by_id(campaign_id)
    if not campaign:
        raise NotFoundException("Campagne non trouvée")
    return campaign


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: CampaignCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.create")),
) -> IdResponse:
    """Crée une nouvelle campagne."""
    service = NewsletterService(db)
    campaign = await service.create_campaign(
        **data.model_dump(exclude_unset=True),
        created_by_external_id=current_user.id,
    )
    return IdResponse(id=campaign.id, message="Campagne créée avec succès")


@router.put("/{campaign_id}", response_model=CampaignRead)
async def update_campaign(
    campaign_id: str,
    data: CampaignUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.edit")),
) -> NewsletterCampaign:
    """Met à jour une campagne."""
    service = NewsletterService(db)
    return await service.update_campaign(
        campaign_id, **data.model_dump(exclude_unset=True)
    )


@router.delete("/{campaign_id}", response_model=MessageResponse)
async def delete_campaign(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.delete")),
) -> MessageResponse:
    """Supprime une campagne."""
    service = NewsletterService(db)
    await service.delete_campaign(campaign_id)
    return MessageResponse(message="Campagne supprimée avec succès")


@router.post("/{campaign_id}/schedule", response_model=CampaignRead)
async def schedule_campaign(
    campaign_id: str,
    data: CampaignSchedule,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.edit")),
) -> NewsletterCampaign:
    """Programme l'envoi d'une campagne."""
    service = NewsletterService(db)
    return await service.schedule_campaign(campaign_id, data.scheduled_send_at)


@router.post("/{campaign_id}/cancel-schedule", response_model=CampaignRead)
async def cancel_schedule(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.edit")),
) -> NewsletterCampaign:
    """Annule la programmation d'une campagne."""
    service = NewsletterService(db)
    return await service.cancel_schedule(campaign_id)


@router.post("/{campaign_id}/send", response_model=CampaignRead)
async def send_campaign(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.edit")),
) -> NewsletterCampaign:
    """Envoie une campagne immédiatement."""
    service = NewsletterService(db)
    return await service.send_campaign(campaign_id)


@router.post("/{campaign_id}/duplicate", response_model=IdResponse)
async def duplicate_campaign(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.create")),
) -> IdResponse:
    """Duplique une campagne."""
    service = NewsletterService(db)
    campaign = await service.duplicate_campaign(campaign_id)
    return IdResponse(id=campaign.id, message="Campagne dupliquée avec succès")


@router.get("/{campaign_id}/statistics", response_model=CampaignStatistics)
async def get_campaign_statistics(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.view")),
) -> CampaignStatistics:
    """Récupère les statistiques d'une campagne."""
    service = NewsletterService(db)
    stats = await service.get_campaign_statistics(campaign_id)
    return CampaignStatistics(**stats)


@router.get("/{campaign_id}/sends", response_model=list[SendRead])
async def get_campaign_sends(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.view")),
) -> list[SendRead]:
    """Récupère les envois d'une campagne."""
    service = NewsletterService(db)
    campaign = await service.get_campaign_by_id(campaign_id)
    if not campaign:
        raise NotFoundException("Campagne non trouvée")
    sends = await service.get_sends_by_campaign(campaign_id)
    return [SendRead.model_validate(s) for s in sends]
