"""
Router Public - Campus
======================

Endpoints publics pour les campus (sans authentification).
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.campus import Campus, CampusMediaLibrary, CampusPartner, CampusTeam
from app.models.core import Country
from app.models.identity import User
from app.models.media import Album, AlbumMedia, Media, PublicationStatus
from app.models.partner import Partner, PartnerType
from app.core.media_utils import resolve_media_url
from app.services.campus_service import CampusService


# =============================================================================
# SCHEMAS PUBLICS
# =============================================================================


class CampusPublicEnriched(BaseModel):
    """Schéma public enrichi pour les campus (avec données de pays résolues)."""

    id: str
    code: str  # Utilisé comme slug dans le frontend
    name: str
    description: str | None
    cover_image_url: str | None  # Résolu depuis cover_image_external_id
    city: str | None
    email: str | None
    phone: str | None
    address: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    is_headquarters: bool

    # Données de pays (résolues depuis country_external_id)
    country_iso_code: str | None
    country_name_fr: str | None

    model_config = {"from_attributes": True}


class CampusPartnerPublic(BaseModel):
    """Schéma public pour un partenaire de campus."""

    id: str
    name: str
    description: str | None
    logo_url: str | None
    website: str | None
    type: PartnerType
    country_iso_code: str | None
    country_name_fr: str | None

    model_config = {"from_attributes": True}


class CampusTeamMemberPublic(BaseModel):
    """Schéma public pour un membre d'équipe de campus."""

    id: str
    first_name: str
    last_name: str
    position: str
    photo_url: str | None
    email: str | None  # Email public pour contact
    display_order: int

    model_config = {"from_attributes": True}


class MediaPublic(BaseModel):
    """Schéma public pour un média dans un album."""

    id: str
    name: str
    type: str
    url: str | None
    alt_text: str | None

    model_config = {"from_attributes": True}


class AlbumPublicWithMedia(BaseModel):
    """Schéma public pour un album avec ses médias."""

    id: str
    title: str
    description: str | None
    media_items: list[MediaPublic]

    model_config = {"from_attributes": True}


# =============================================================================
# ROUTER
# =============================================================================


router = APIRouter(prefix="/campuses", tags=["Campuses (Public)"])


@router.get("", response_model=dict)
async def list_campuses(
    db: DbSession,
    pagination: PaginationParams = Depends(),
    country_id: str | None = Query(None, description="Filtrer par pays"),
    is_headquarters: bool | None = Query(None, description="Filtrer par siège principal"),
) -> dict:
    """Liste les campus actifs avec pagination."""
    service = CampusService(db)
    query = await service.get_campuses(
        country_id=country_id,
        is_headquarters=is_headquarters,
        active=True,  # Seulement les campus actifs
    )
    return await paginate(db, query, pagination, Campus)


@router.get("/all", response_model=list[CampusPublicEnriched])
async def list_all_campuses(
    db: DbSession,
    is_headquarters: bool | None = Query(None, description="Filtrer par siège principal"),
) -> list[CampusPublicEnriched]:
    """
    Liste tous les campus actifs (sans pagination, pour la carte).

    Retourne les données enrichies avec les informations de pays résolues.
    """
    query = select(Campus, Country, Media).outerjoin(
        Country, Campus.country_external_id == Country.id
    ).outerjoin(
        Media, Campus.cover_image_external_id == Media.id
    ).where(Campus.active == True)

    if is_headquarters is not None:
        query = query.where(Campus.is_headquarters == is_headquarters)

    query = query.order_by(Campus.is_headquarters.desc(), Campus.name)
    result = await db.execute(query)
    rows = result.all()

    campuses = []
    for campus, country, cover_media in rows:
        campuses.append(CampusPublicEnriched(
            id=campus.id,
            code=campus.code,
            name=campus.name,
            description=campus.description,
            cover_image_url=resolve_media_url(cover_media),
            city=campus.city,
            email=campus.email,
            phone=campus.phone,
            address=campus.address,
            latitude=campus.latitude,
            longitude=campus.longitude,
            is_headquarters=campus.is_headquarters,
            country_iso_code=country.iso_code if country else None,
            country_name_fr=country.name_fr if country else None,
        ))

    return campuses


@router.get("/{code}", response_model=CampusPublicEnriched)
async def get_campus_by_code(
    code: str,
    db: DbSession,
) -> CampusPublicEnriched:
    """
    Récupère un campus actif par son code (utilisé comme slug).

    Le code est insensible à la casse (sera converti en majuscules).
    """
    code_upper = code.upper()

    # Requête avec jointures pour récupérer les données de pays et média
    query = select(Campus, Country, Media).outerjoin(
        Country, Campus.country_external_id == Country.id
    ).outerjoin(
        Media, Campus.cover_image_external_id == Media.id
    ).where(
        Campus.code == code_upper,
        Campus.active == True,
    )

    result = await db.execute(query)
    row = result.first()

    if not row:
        raise NotFoundException("Campus non trouvé")

    campus, country, cover_media = row

    return CampusPublicEnriched(
        id=campus.id,
        code=campus.code,
        name=campus.name,
        description=campus.description,
        cover_image_url=resolve_media_url(cover_media),
        city=campus.city,
        email=campus.email,
        phone=campus.phone,
        address=campus.address,
        latitude=campus.latitude,
        longitude=campus.longitude,
        is_headquarters=campus.is_headquarters,
        country_iso_code=country.iso_code if country else None,
        country_name_fr=country.name_fr if country else None,
    )


@router.get("/{campus_id}/partners", response_model=list[CampusPartnerPublic])
async def get_campus_partners(
    campus_id: str,
    db: DbSession,
) -> list[CampusPartnerPublic]:
    """
    Récupère les partenaires d'un campus.

    Retourne la liste des partenaires actifs associés au campus,
    avec leurs informations enrichies (logo, pays).
    """
    # Vérifier que le campus existe
    campus_result = await db.execute(
        select(Campus).where(Campus.id == campus_id, Campus.active == True)
    )
    if not campus_result.scalar_one_or_none():
        raise NotFoundException("Campus non trouvé")

    # Récupérer les partenaires avec jointures
    query = (
        select(Partner, Media, Country)
        .join(CampusPartner, CampusPartner.partner_external_id == Partner.id)
        .outerjoin(Media, Partner.logo_external_id == Media.id)
        .outerjoin(Country, Partner.country_external_id == Country.id)
        .where(
            CampusPartner.campus_id == campus_id,
            Partner.active == True,
        )
        .order_by(Partner.display_order, Partner.name)
    )

    result = await db.execute(query)
    rows = result.all()

    partners = []
    for partner, logo_media, country in rows:
        partners.append(CampusPartnerPublic(
            id=partner.id,
            name=partner.name,
            description=partner.description,
            logo_url=resolve_media_url(logo_media),
            website=partner.website,
            type=partner.type,
            country_iso_code=country.iso_code if country else None,
            country_name_fr=country.name_fr if country else None,
        ))

    return partners


@router.get("/{campus_id}/team", response_model=list[CampusTeamMemberPublic])
async def get_campus_team(
    campus_id: str,
    db: DbSession,
) -> list[CampusTeamMemberPublic]:
    """
    Récupère les membres de l'équipe d'un campus.

    Retourne la liste des membres actifs de l'équipe du campus,
    avec leurs informations publiques (nom, poste, photo).
    """
    # Vérifier que le campus existe
    campus_result = await db.execute(
        select(Campus).where(Campus.id == campus_id, Campus.active == True)
    )
    if not campus_result.scalar_one_or_none():
        raise NotFoundException("Campus non trouvé")

    # Récupérer les membres d'équipe avec jointures
    query = (
        select(CampusTeam, User, Media)
        .join(User, CampusTeam.user_external_id == User.id)
        .outerjoin(Media, User.photo_external_id == Media.id)
        .where(
            CampusTeam.campus_id == campus_id,
            CampusTeam.active == True,
            User.active == True,
        )
        .order_by(CampusTeam.display_order, User.last_name)
    )

    result = await db.execute(query)
    rows = result.all()

    team_members = []
    for team_member, user, photo_media in rows:
        team_members.append(CampusTeamMemberPublic(
            id=team_member.id,
            first_name=user.first_name,
            last_name=user.last_name,
            position=team_member.position,
            photo_url=resolve_media_url(photo_media),
            email=user.email,
            display_order=team_member.display_order,
        ))

    return team_members


@router.get("/{campus_id}/albums", response_model=list[AlbumPublicWithMedia])
async def get_campus_albums(
    campus_id: str,
    db: DbSession,
) -> list[AlbumPublicWithMedia]:
    """
    Récupère les albums publiés associés à un campus.

    Retourne la liste des albums avec leurs médias,
    triés par ordre de création (les plus récents d'abord).
    """
    # Vérifier que le campus existe
    campus_result = await db.execute(
        select(Campus).where(Campus.id == campus_id, Campus.active == True)
    )
    if not campus_result.scalar_one_or_none():
        raise NotFoundException("Campus non trouvé")

    # Récupérer les albums associés au campus (publiés uniquement)
    album_query = (
        select(Album)
        .join(CampusMediaLibrary, CampusMediaLibrary.album_external_id == Album.id)
        .where(
            CampusMediaLibrary.campus_id == campus_id,
            Album.status == PublicationStatus.PUBLISHED,
        )
        .order_by(Album.created_at.desc())
    )

    album_result = await db.execute(album_query)
    albums = album_result.scalars().all()

    # Pour chaque album, récupérer ses médias
    albums_with_media = []
    for album in albums:
        media_query = (
            select(Media, AlbumMedia.display_order)
            .join(AlbumMedia, AlbumMedia.media_id == Media.id)
            .where(AlbumMedia.album_id == album.id)
            .order_by(AlbumMedia.display_order)
        )

        media_result = await db.execute(media_query)
        media_rows = media_result.all()

        media_items = []
        for media, _ in media_rows:
            media_items.append(MediaPublic(
                id=media.id,
                name=media.name,
                type=media.type.value if hasattr(media.type, 'value') else str(media.type),
                url=resolve_media_url(media),
                alt_text=media.alt_text,
            ))

        albums_with_media.append(AlbumPublicWithMedia(
            id=album.id,
            title=album.title,
            description=album.description,
            media_items=media_items,
        ))

    return albums_with_media
