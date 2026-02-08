"""
Router Public - Utilisateurs
=============================

Endpoint public pour les profils utilisateurs (sans authentification).
"""

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.core.media_utils import resolve_media_url
from app.models.campus import Campus, CampusTeam
from app.models.core import Country
from app.models.identity import User
from app.models.media import Media
from app.models.organization import Service, ServiceTeam

router = APIRouter(prefix="/users", tags=["Users (Public)"])


# =============================================================================
# Schémas publics
# =============================================================================


class UserProfileCampusAffiliation(BaseModel):
    """Affiliation campus d'un utilisateur."""

    campus_id: str
    campus_name: str
    campus_code: str
    position: str
    active: bool


class UserProfileServiceAffiliation(BaseModel):
    """Affiliation service d'un utilisateur."""

    service_id: str
    service_name: str
    position: str
    active: bool


class UserPublicProfile(BaseModel):
    """Profil public d'un utilisateur."""

    id: str
    first_name: str
    last_name: str
    salutation: str | None = None
    biography: str | None = None
    photo_url: str | None = None
    email: str | None = None
    phone: str | None = None
    city: str | None = None
    linkedin: str | None = None
    facebook: str | None = None
    nationality_country_name_fr: str | None = None
    nationality_country_iso_code: str | None = None
    campus_affiliations: list[UserProfileCampusAffiliation] = []
    service_affiliations: list[UserProfileServiceAffiliation] = []


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/{user_id}/profile", response_model=UserPublicProfile)
async def get_user_profile(
    user_id: str,
    db: DbSession,
) -> UserPublicProfile:
    """
    Récupère le profil public d'un utilisateur.

    Retourne les informations publiques de l'utilisateur avec ses
    affiliations campus et services.
    """
    # Récupérer l'utilisateur avec photo et nationalité
    query = (
        select(User, Media, Country)
        .outerjoin(Media, User.photo_external_id == Media.id)
        .outerjoin(Country, User.nationality_external_id == Country.id)
        .where(User.id == user_id, User.active == True)
    )
    result = await db.execute(query)
    row = result.one_or_none()

    if not row:
        raise NotFoundException("Utilisateur non trouvé")

    user, photo_media, nationality_country = row

    # Récupérer les affiliations campus
    campus_query = (
        select(CampusTeam, Campus)
        .join(Campus, CampusTeam.campus_id == Campus.id)
        .where(
            CampusTeam.user_external_id == user_id,
            CampusTeam.active == True,
            Campus.active == True,
        )
        .order_by(CampusTeam.display_order)
    )
    campus_result = await db.execute(campus_query)
    campus_affiliations = [
        UserProfileCampusAffiliation(
            campus_id=campus.id,
            campus_name=campus.name,
            campus_code=campus.code,
            position=team_member.position,
            active=team_member.active,
        )
        for team_member, campus in campus_result.all()
    ]

    # Récupérer les affiliations service
    service_query = (
        select(ServiceTeam, Service)
        .join(Service, ServiceTeam.service_id == Service.id)
        .where(
            ServiceTeam.user_external_id == user_id,
            ServiceTeam.active == True,
            Service.active == True,
        )
        .order_by(ServiceTeam.display_order)
    )
    service_result = await db.execute(service_query)
    service_affiliations = [
        UserProfileServiceAffiliation(
            service_id=service.id,
            service_name=service.name,
            position=team_member.position,
            active=team_member.active,
        )
        for team_member, service in service_result.all()
    ]

    return UserPublicProfile(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        salutation=user.salutation,
        biography=user.biography,
        photo_url=resolve_media_url(photo_media),
        email=user.email,
        phone=user.phone,
        city=user.city,
        linkedin=user.linkedin,
        facebook=user.facebook,
        nationality_country_name_fr=nationality_country.name_fr if nationality_country else None,
        nationality_country_iso_code=nationality_country.iso_code if nationality_country else None,
        campus_affiliations=campus_affiliations,
        service_affiliations=service_affiliations,
    )
