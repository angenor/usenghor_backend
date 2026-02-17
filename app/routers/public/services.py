"""
Router Public - Services
========================

Endpoints publics pour les services de l'université.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.models.identity import User
from app.models.media import Media
from app.models.organization import ServiceTeam
from app.core.media_utils import resolve_media_url
from app.schemas.organization import (
    ServiceObjectiveRead,
    ServiceAchievementRead,
    ServiceProjectRead,
    ServicePublic,
    ServicePublicWithDetails,
)
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/services", tags=["Services"])


# =============================================================================
# Schémas publics enrichis pour les équipes de service
# =============================================================================


class ServiceTeamUserPublic(BaseModel):
    """Données publiques d'un utilisateur dans une équipe de service."""

    id: str
    first_name: str
    last_name: str
    email: str | None
    photo_url: str | None


class ServiceTeamMemberPublic(BaseModel):
    """Membre d'équipe de service enrichi avec données utilisateur."""

    id: str
    service_id: str
    user_external_id: str
    position: str
    display_order: int
    start_date: str | None
    end_date: str | None
    active: bool
    user: ServiceTeamUserPublic | None = None


class ServicePublicWithDetailsEnriched(ServicePublic):
    """Schéma public pour un service avec détails et équipe enrichie."""

    objectives: list[ServiceObjectiveRead] = []
    achievements: list[ServiceAchievementRead] = []
    projects: list[ServiceProjectRead] = []
    team: list[ServiceTeamMemberPublic] = []


# =============================================================================
# Endpoints
# =============================================================================


@router.get("", response_model=list[ServicePublic])
async def list_services(
    db: DbSession,
    sector_id: str | None = Query(None, description="Filtrer par secteur"),
) -> list:
    """Liste les services actifs, optionnellement filtrés par secteur."""
    service = OrganizationService(db)
    return await service.get_active_services(sector_id=sector_id)


@router.get("/{service_id}", response_model=ServicePublicWithDetailsEnriched)
async def get_service(
    service_id: str,
    db: DbSession,
) -> ServicePublicWithDetailsEnriched:
    """Récupère un service par son ID avec ses objectifs, réalisations, projets et équipe enrichie."""
    org_service = OrganizationService(db)
    svc = await org_service.get_service_with_details(service_id)
    if not svc:
        raise NotFoundException("Service non trouvé")

    # Enrichir les membres d'équipe avec les données utilisateur et photo
    enriched_team: list[ServiceTeamMemberPublic] = []
    if svc.team:
        user_ids = [m.user_external_id for m in svc.team]
        # Jointure User + Media pour récupérer noms et photos
        query = (
            select(User, Media)
            .outerjoin(Media, User.photo_external_id == Media.id)
            .where(User.id.in_(user_ids), User.email_verified == True)
        )
        result = await db.execute(query)
        users_map: dict[str, tuple[User, Media | None]] = {}
        for user, photo_media in result.all():
            users_map[user.id] = (user, photo_media)

        for member in svc.team:
            user_data = None
            if member.user_external_id in users_map:
                user, photo_media = users_map[member.user_external_id]
                user_data = ServiceTeamUserPublic(
                    id=user.id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=user.email,
                    photo_url=resolve_media_url(photo_media),
                )

            enriched_team.append(ServiceTeamMemberPublic(
                id=member.id,
                service_id=member.service_id,
                user_external_id=member.user_external_id,
                position=member.position,
                display_order=member.display_order,
                start_date=str(member.start_date) if member.start_date else None,
                end_date=str(member.end_date) if member.end_date else None,
                active=member.active,
                user=user_data,
            ))

    return ServicePublicWithDetailsEnriched(
        id=svc.id,
        name=svc.name,
        sigle=svc.sigle,
        color=svc.color,
        description=svc.description,
        mission=svc.mission,
        email=svc.email,
        phone=svc.phone,
        sector_id=svc.sector_id,
        head_external_id=svc.head_external_id,
        album_external_id=svc.album_external_id,
        display_order=svc.display_order,
        objectives=svc.objectives,
        achievements=svc.achievements,
        projects=svc.projects,
        team=enriched_team,
    )
