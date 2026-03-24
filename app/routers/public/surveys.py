"""
Router Public - Sondages
=========================

Endpoints publics pour les formulaires de sondage.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.core.dependencies import DbSession
from app.core.exceptions import GoneException, NotFoundException
from app.models.base import SurveyCampaignStatus
from app.models.survey import SurveyAssociation
from app.schemas.survey import (
    SurveyCampaignListPublic,
    SurveyCampaignPublic,
    SurveySubmitRequest,
)
from app.services.survey_service import SurveyService

logger = logging.getLogger(__name__)

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

    result = SurveyCampaignPublic.model_validate(campaign)

    # Résoudre l'image de couverture depuis la première association
    try:
        assoc_result = await db.execute(
            select(SurveyAssociation)
            .where(SurveyAssociation.campaign_id == campaign.id)
            .limit(1)
        )
        assoc = assoc_result.scalar_one_or_none()
        if assoc:
            cover_id = await _get_entity_cover_image(db, assoc.entity_type, assoc.entity_id)
            if cover_id:
                result.cover_image_external_id = str(cover_id)
    except Exception as e:
        logger.warning(f"Impossible de résoudre l'image de couverture: {e}")

    return result


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


async def _get_entity_cover_image(db, entity_type: str, entity_id: str) -> str | None:
    """Récupère le cover_image_external_id de l'entité associée."""
    from app.models.academic import Program
    from app.models.application import ApplicationCall
    from app.models.content import Event

    entity_model_map: dict = {
        "event": Event,
        "application_call": ApplicationCall,
        "program": Program,
    }

    model_class = entity_model_map.get(entity_type)
    if not model_class:
        return None

    result = await db.execute(
        select(model_class.cover_image_external_id).where(model_class.id == entity_id)
    )
    return result.scalar_one_or_none()
