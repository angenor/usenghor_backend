"""
Router Admin - Campagnes de sondage
====================================

Endpoints CRUD et cycle de vie pour les campagnes de sondage.
"""

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.pagination import PaginationParams, paginate
from app.models.base import SurveyCampaignStatus
from app.models.survey import SurveyCampaign, SurveyResponse
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.survey import (
    SurveyAssociationCreate,
    SurveyAssociationRead,
    SurveyCampaignCreate,
    SurveyCampaignRead,
    SurveyCampaignReadWithStats,
    SurveyCampaignUpdate,
    SurveyDuplicateRequest,
    SurveyResponseRead,
    SurveyStatsResponse,
)
from app.services.survey_service import SurveyService

router = APIRouter(prefix="/surveys", tags=["Surveys"])


def _is_super_admin(user) -> bool:
    return user.has_role("super_admin")


# =============================================================================
# CAMPAGNES - CRUD
# =============================================================================


@router.get("", response_model=dict)
async def list_campaigns(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur titre ou slug"),
    campaign_status: SurveyCampaignStatus | None = Query(None, alias="status", description="Filtrer par statut"),
    sort_by: str | None = Query(None, description="Champ de tri"),
    sort_order: str | None = Query(None, description="Ordre de tri (asc/desc)"),
    _: bool = Depends(PermissionChecker("survey.manage")),
) -> dict:
    """Liste les campagnes du gestionnaire connecté (paginée)."""
    service = SurveyService(db)
    query = await service.get_campaigns(
        user_id=current_user.id,
        is_super_admin=_is_super_admin(current_user),
        search=search,
        status=campaign_status,
    )

    if sort_by:
        from sqlalchemy import asc, desc
        col = getattr(SurveyCampaign, sort_by, None)
        if col is not None:
            order_func = desc if sort_order == "desc" else asc
            query = query.order_by(order_func(col))
    else:
        query = query.order_by(SurveyCampaign.created_at.desc())

    result = await paginate(db, query, pagination, SurveyCampaign, SurveyCampaignRead)

    # Enrichir avec response_count et last_response_at
    enriched_items = []
    for item in result["items"]:
        item_dict = item.model_dump() if hasattr(item, "model_dump") else dict(item)
        campaign_id = item_dict["id"]
        item_dict["response_count"] = await service.get_campaign_response_count(campaign_id)
        item_dict["last_response_at"] = await service.get_campaign_last_response_at(campaign_id)
        enriched_items.append(item_dict)

    result["items"] = enriched_items
    return result


@router.get("/{campaign_id}", response_model=SurveyCampaignRead)
async def get_campaign(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("survey.manage")),
) -> SurveyCampaign:
    """Récupère une campagne par son ID."""
    service = SurveyService(db)
    return await service.get_campaign_by_id(
        campaign_id, current_user.id, _is_super_admin(current_user)
    )


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: SurveyCampaignCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("survey.manage")),
) -> IdResponse:
    """Crée une nouvelle campagne (statut draft)."""
    service = SurveyService(db)
    campaign = await service.create_campaign(
        data=data.model_dump(), user_id=current_user.id
    )
    return IdResponse(id=campaign.id, message="Campagne créée avec succès")


@router.put("/{campaign_id}", response_model=SurveyCampaignRead)
async def update_campaign(
    campaign_id: str,
    data: SurveyCampaignUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("survey.manage")),
) -> SurveyCampaign:
    """Met à jour une campagne (partial update)."""
    service = SurveyService(db)
    update_dict = data.model_dump(exclude_unset=True)
    return await service.update_campaign(
        campaign_id,
        current_user.id,
        _is_super_admin(current_user),
        **update_dict,
    )


@router.delete("/{campaign_id}", response_model=MessageResponse)
async def delete_campaign(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("survey.manage")),
) -> MessageResponse:
    """Supprime une campagne et toutes ses réponses."""
    service = SurveyService(db)
    await service.delete_campaign(
        campaign_id, current_user.id, _is_super_admin(current_user)
    )
    return MessageResponse(message="Campagne supprimée avec succès")


# =============================================================================
# CAMPAGNES - CYCLE DE VIE
# =============================================================================


@router.post("/{campaign_id}/publish", response_model=SurveyCampaignRead)
async def publish_campaign(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("survey.manage")),
) -> SurveyCampaign:
    """Publie une campagne (draft/paused -> active)."""
    service = SurveyService(db)
    return await service.publish_campaign(
        campaign_id, current_user.id, _is_super_admin(current_user)
    )


@router.post("/{campaign_id}/pause", response_model=SurveyCampaignRead)
async def pause_campaign(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("survey.manage")),
) -> SurveyCampaign:
    """Met en pause une campagne (active -> paused)."""
    service = SurveyService(db)
    return await service.pause_campaign(
        campaign_id, current_user.id, _is_super_admin(current_user)
    )


@router.post("/{campaign_id}/close", response_model=SurveyCampaignRead)
async def close_campaign(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("survey.manage")),
) -> SurveyCampaign:
    """Clôture une campagne (active/paused -> closed)."""
    service = SurveyService(db)
    return await service.close_campaign(
        campaign_id, current_user.id, _is_super_admin(current_user)
    )


@router.post("/{campaign_id}/duplicate", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_campaign(
    campaign_id: str,
    data: SurveyDuplicateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("survey.manage")),
) -> IdResponse:
    """Duplique une campagne (structure uniquement, sans réponses)."""
    service = SurveyService(db)
    new_campaign = await service.duplicate_campaign(
        campaign_id, data.slug, current_user.id, _is_super_admin(current_user)
    )
    return IdResponse(id=new_campaign.id, message="Campagne dupliquée avec succès")


# =============================================================================
# RÉPONSES & STATISTIQUES
# =============================================================================


@router.get("/{campaign_id}/responses", response_model=dict)
async def list_responses(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    sort_by: str | None = Query(None, description="Champ de tri"),
    sort_order: str | None = Query(None, description="Ordre de tri (asc/desc)"),
    _: bool = Depends(PermissionChecker("survey.manage")),
) -> dict:
    """Liste paginée des réponses d'une campagne."""
    service = SurveyService(db)
    # Vérifier l'accès à la campagne
    await service.get_campaign_by_id(
        campaign_id, current_user.id, _is_super_admin(current_user)
    )

    query = await service.get_responses(campaign_id)

    if sort_by == "submitted_at":
        from sqlalchemy import asc, desc
        order_func = desc if sort_order == "desc" else asc
        query = query.order_by(order_func(SurveyResponse.submitted_at))
    else:
        query = query.order_by(SurveyResponse.submitted_at.desc())

    return await paginate(db, query, pagination, SurveyResponse, SurveyResponseRead)


@router.get("/{campaign_id}/stats", response_model=SurveyStatsResponse)
async def get_campaign_stats(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("survey.manage")),
) -> dict:
    """Statistiques agrégées d'une campagne."""
    service = SurveyService(db)
    # Vérifier l'accès à la campagne
    await service.get_campaign_by_id(
        campaign_id, current_user.id, _is_super_admin(current_user)
    )
    return await service.get_stats(campaign_id)


@router.get("/{campaign_id}/export")
async def export_campaign_csv(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("survey.manage")),
):
    """Export CSV des réponses d'une campagne."""
    service = SurveyService(db)
    # Vérifier l'accès à la campagne
    campaign = await service.get_campaign_by_id(
        campaign_id, current_user.id, _is_super_admin(current_user)
    )
    csv_content = await service.export_csv(campaign_id)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="campagne-{campaign.slug}-export.csv"'
        },
    )


# =============================================================================
# ASSOCIATIONS
# =============================================================================


@router.get("/{campaign_id}/associations", response_model=list[SurveyAssociationRead])
async def list_associations(
    campaign_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("survey.manage")),
) -> list:
    """Liste les associations d'une campagne."""
    service = SurveyService(db)
    await service.get_campaign_by_id(
        campaign_id, current_user.id, _is_super_admin(current_user)
    )
    return await service.get_associations(campaign_id)


@router.post("/{campaign_id}/associations", response_model=SurveyAssociationRead, status_code=status.HTTP_201_CREATED)
async def create_association(
    campaign_id: str,
    data: SurveyAssociationCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("survey.manage")),
):
    """Associe une campagne à un élément du site."""
    service = SurveyService(db)
    await service.get_campaign_by_id(
        campaign_id, current_user.id, _is_super_admin(current_user)
    )
    return await service.create_association(
        campaign_id, data.entity_type, data.entity_id
    )


@router.delete("/{campaign_id}/associations/{association_id}", response_model=MessageResponse)
async def delete_association(
    campaign_id: str,
    association_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("survey.manage")),
) -> MessageResponse:
    """Retire une association."""
    service = SurveyService(db)
    await service.get_campaign_by_id(
        campaign_id, current_user.id, _is_super_admin(current_user)
    )
    await service.delete_association(association_id)
    return MessageResponse(message="Association supprimée avec succès")
