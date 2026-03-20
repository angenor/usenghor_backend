"""
Router Public - Sondages
=========================

Endpoints publics pour les formulaires de sondage.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.core.dependencies import DbSession
from app.core.exceptions import GoneException, NotFoundException
from app.models.base import SurveyCampaignStatus
from app.schemas.survey import (
    SurveyCampaignListPublic,
    SurveyCampaignPublic,
    SurveySubmitRequest,
)
from app.services.survey_service import SurveyService

router = APIRouter(prefix="/surveys", tags=["Surveys"])


@router.get("/by-entity/{entity_type}/{entity_id}", response_model=list[SurveyCampaignListPublic])
async def get_campaigns_by_entity(
    entity_type: str,
    entity_id: str,
    db: DbSession,
) -> list:
    """Récupère les campagnes actives associées à un élément du site."""
    service = SurveyService(db)
    campaigns = await service.get_campaigns_by_entity(entity_type, entity_id)
    return [SurveyCampaignListPublic.model_validate(c) for c in campaigns]


@router.get("/{slug}", response_model=SurveyCampaignPublic)
async def get_survey_by_slug(
    slug: str,
    db: DbSession,
) -> SurveyCampaignPublic:
    """Récupère le formulaire d'une campagne active par son slug."""
    service = SurveyService(db)
    campaign = await service.get_campaign_by_slug(slug)

    # Auto-clôture si closes_at dépassé
    if campaign.closes_at and campaign.closes_at < datetime.now(timezone.utc):
        if campaign.status == SurveyCampaignStatus.ACTIVE:
            campaign.status = SurveyCampaignStatus.CLOSED
            await db.commit()

    if campaign.status in (SurveyCampaignStatus.PAUSED, SurveyCampaignStatus.CLOSED):
        raise GoneException("Ce formulaire n'est plus disponible")

    if campaign.status == SurveyCampaignStatus.DRAFT:
        raise NotFoundException("Formulaire introuvable")

    return SurveyCampaignPublic.model_validate(campaign)


@router.post("/{slug}/submit", status_code=201)
async def submit_response(
    slug: str,
    data: SurveySubmitRequest,
    request: Request,
    db: DbSession,
):
    """Soumet une réponse à un formulaire."""
    service = SurveyService(db)

    # Rejet silencieux si honeypot rempli
    if data.honeypot:
        return {"message": "Réponse enregistrée avec succès"}

    ip_address = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
    session_id = request.headers.get("X-Session-Id")

    await service.submit_response(
        slug=slug,
        response_data=data.response_data,
        ip_address=ip_address,
        session_id=session_id,
    )
    return {"message": "Réponse enregistrée avec succès"}
