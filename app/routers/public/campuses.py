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
from app.models.campus import Campus, CampusPartner
from app.models.core import Country
from app.models.media import Media
from app.models.partner import Partner, PartnerType
from app.services.campus_service import CampusService


def resolve_media_url(media: Media | None) -> str | None:
    """
    Résout l'URL d'un média.

    Retourne l'URL relative de l'endpoint de téléchargement public.
    Le frontend préfixera avec son apiBase configuré.
    """
    if not media:
        return None
    if media.is_external_url:
        return media.url
    # Pour les fichiers locaux, retourner l'URL de l'endpoint de téléchargement
    return f"/api/public/media/{media.id}/download"


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
