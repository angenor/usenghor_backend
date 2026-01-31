"""
Schémas Content
===============

Schémas Pydantic pour la gestion des actualités et événements.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.base import PublicationStatus
from app.models.content import EventType, NewsHighlightStatus, RegistrationStatus


# =============================================================================
# TAGS
# =============================================================================


class TagBase(BaseModel):
    """Schéma de base pour les tags."""

    name: str = Field(..., min_length=1, max_length=100, description="Nom du tag")
    slug: str = Field(..., min_length=1, max_length=100, description="Slug URL")
    icon: str | None = Field(None, max_length=50, description="Icône du tag")
    description: str | None = Field(None, description="Description du tag")


class TagCreate(TagBase):
    """Schéma pour la création d'un tag."""

    pass


class TagUpdate(BaseModel):
    """Schéma pour la mise à jour d'un tag."""

    name: str | None = Field(None, min_length=1, max_length=100)
    slug: str | None = Field(None, min_length=1, max_length=100)
    icon: str | None = Field(None, max_length=50)
    description: str | None = None


class TagRead(TagBase):
    """Schéma pour la lecture d'un tag."""

    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TagMerge(BaseModel):
    """Schéma pour fusionner des tags."""

    source_tag_ids: list[str] = Field(..., min_length=1, description="Tags à fusionner")
    target_tag_id: str = Field(..., description="Tag cible")


# =============================================================================
# EVENT REGISTRATIONS
# =============================================================================


class EventRegistrationBase(BaseModel):
    """Schéma de base pour les inscriptions."""

    last_name: str | None = Field(None, max_length=100, description="Nom")
    first_name: str | None = Field(None, max_length=100, description="Prénom")
    email: EmailStr = Field(..., description="Email")
    phone: str | None = Field(None, max_length=30, description="Téléphone")
    organization: str | None = Field(None, max_length=255, description="Organisation")


class EventRegistrationCreate(EventRegistrationBase):
    """Schéma pour la création d'une inscription."""

    user_external_id: str | None = Field(None, description="ID utilisateur")


class EventRegistrationUpdate(BaseModel):
    """Schéma pour la mise à jour d'une inscription."""

    last_name: str | None = Field(None, max_length=100)
    first_name: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=30)
    organization: str | None = Field(None, max_length=255)
    status: RegistrationStatus | None = None


class EventRegistrationRead(EventRegistrationBase):
    """Schéma pour la lecture d'une inscription."""

    id: str
    event_id: str
    user_external_id: str | None
    status: RegistrationStatus
    registered_at: datetime

    model_config = {"from_attributes": True}


class EventRegistrationBulkAction(BaseModel):
    """Schéma pour les actions en masse sur les inscriptions."""

    registration_ids: list[str] = Field(..., min_length=1)
    action: str = Field(..., pattern="^(confirm|cancel)$")


# =============================================================================
# EVENTS
# =============================================================================


class EventBase(BaseModel):
    """Schéma de base pour les événements."""

    title: str = Field(..., min_length=1, max_length=255, description="Titre")
    slug: str = Field(..., min_length=1, max_length=255, description="Slug URL")
    description: str | None = Field(None, description="Description courte")
    content: str | None = Field(None, description="Contenu riche")

    type: EventType = Field(..., description="Type d'événement")
    type_other: str | None = Field(None, max_length=100, description="Type personnalisé")

    start_date: datetime = Field(..., description="Date de début")
    end_date: datetime | None = Field(None, description="Date de fin")

    venue: str | None = Field(None, max_length=255, description="Lieu")
    address: str | None = Field(None, description="Adresse")
    city: str | None = Field(None, max_length=100, description="Ville")
    latitude: Decimal | None = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Decimal | None = Field(None, ge=-180, le=180, description="Longitude")

    is_online: bool = Field(False, description="Événement en ligne")
    video_conference_link: str | None = Field(None, max_length=500)

    registration_required: bool = Field(False, description="Inscription requise")
    registration_link: str | None = Field(None, max_length=500)
    max_attendees: int | None = Field(None, ge=1, description="Capacité maximale")


class EventCreate(EventBase):
    """Schéma pour la création d'un événement."""

    cover_image_external_id: str | None = None
    country_external_id: str | None = None
    campus_external_id: str | None = None
    sector_external_id: str | None = None
    project_external_id: str | None = None
    organizer_external_id: str | None = None
    album_external_id: str | None = None
    status: PublicationStatus = PublicationStatus.DRAFT


class EventUpdate(BaseModel):
    """Schéma pour la mise à jour d'un événement."""

    title: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    content: str | None = None

    type: EventType | None = None
    type_other: str | None = Field(None, max_length=100)

    start_date: datetime | None = None
    end_date: datetime | None = None

    venue: str | None = Field(None, max_length=255)
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    latitude: Decimal | None = Field(None, ge=-90, le=90)
    longitude: Decimal | None = Field(None, ge=-180, le=180)

    is_online: bool | None = None
    video_conference_link: str | None = Field(None, max_length=500)

    registration_required: bool | None = None
    registration_link: str | None = Field(None, max_length=500)
    max_attendees: int | None = Field(None, ge=1)

    cover_image_external_id: str | None = None
    country_external_id: str | None = None
    campus_external_id: str | None = None
    sector_external_id: str | None = None
    project_external_id: str | None = None
    organizer_external_id: str | None = None
    album_external_id: str | None = None
    status: PublicationStatus | None = None


class EventRead(EventBase):
    """Schéma pour la lecture d'un événement."""

    id: str
    cover_image_external_id: str | None
    country_external_id: str | None
    campus_external_id: str | None
    sector_external_id: str | None
    project_external_id: str | None
    organizer_external_id: str | None
    album_external_id: str | None
    status: PublicationStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventWithRegistrations(EventRead):
    """Schéma pour un événement avec ses inscriptions."""

    registrations: list[EventRegistrationRead] = []
    registrations_count: int = 0


class EventPublic(BaseModel):
    """Schéma public pour les événements."""

    id: str
    title: str
    slug: str
    description: str | None
    type: EventType
    type_other: str | None
    start_date: datetime
    end_date: datetime | None
    venue: str | None
    city: str | None
    is_online: bool
    registration_required: bool
    max_attendees: int | None
    cover_image_external_id: str | None

    model_config = {"from_attributes": True}


# =============================================================================
# NEWS
# =============================================================================


class NewsBase(BaseModel):
    """Schéma de base pour les actualités."""

    title: str = Field(..., min_length=1, max_length=255, description="Titre")
    slug: str = Field(..., min_length=1, max_length=255, description="Slug URL")
    summary: str | None = Field(None, description="Résumé")
    content: str | None = Field(None, description="Contenu riche")
    video_url: str | None = Field(None, max_length=500, description="URL vidéo")
    highlight_status: NewsHighlightStatus = Field(
        NewsHighlightStatus.STANDARD, description="Mise en avant"
    )


class NewsCreate(NewsBase):
    """Schéma pour la création d'une actualité."""

    cover_image_external_id: str | None = None
    campus_external_id: str | None = None
    sector_external_id: str | None = None
    service_external_id: str | None = None
    event_external_id: str | None = None
    project_external_id: str | None = None
    author_external_id: str | None = None
    status: PublicationStatus = PublicationStatus.DRAFT
    published_at: datetime | None = None
    visible_from: datetime | None = None
    tag_ids: list[str] = Field(default_factory=list, description="IDs des tags")


class NewsUpdate(BaseModel):
    """Schéma pour la mise à jour d'une actualité."""

    title: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    summary: str | None = None
    content: str | None = None
    video_url: str | None = Field(None, max_length=500)
    highlight_status: NewsHighlightStatus | None = None

    cover_image_external_id: str | None = None
    campus_external_id: str | None = None
    sector_external_id: str | None = None
    service_external_id: str | None = None
    event_external_id: str | None = None
    project_external_id: str | None = None
    author_external_id: str | None = None
    status: PublicationStatus | None = None
    published_at: datetime | None = None
    visible_from: datetime | None = None
    tag_ids: list[str] | None = None


class NewsRead(NewsBase):
    """Schéma pour la lecture d'une actualité."""

    id: str
    cover_image_external_id: str | None
    campus_external_id: str | None
    sector_external_id: str | None
    service_external_id: str | None
    event_external_id: str | None
    project_external_id: str | None
    author_external_id: str | None
    status: PublicationStatus
    published_at: datetime | None
    visible_from: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NewsWithTags(NewsRead):
    """Schéma pour une actualité avec ses tags."""

    tags: list[TagRead] = []


class NewsPublic(BaseModel):
    """Schéma public pour les actualités."""

    id: str
    title: str
    slug: str
    summary: str | None
    content: str | None
    video_url: str | None
    cover_image_external_id: str | None
    highlight_status: NewsHighlightStatus
    published_at: datetime | None
    tags: list[TagRead] = []

    model_config = {"from_attributes": True}


class NewsPublish(BaseModel):
    """Schéma pour publier/dépublier une actualité."""

    published_at: datetime | None = Field(None, description="Date de publication")


# =============================================================================
# STATISTICS
# =============================================================================


class TimelineDataPoint(BaseModel):
    """Point de données pour les graphiques de tendance."""

    period: str = Field(..., description="Période (ex: '2025-01')")
    count: int = Field(..., description="Nombre d'éléments")


class EventStatistics(BaseModel):
    """Statistiques des événements."""

    total: int = Field(0, description="Total des événements")
    published: int = Field(0, description="Événements publiés")
    draft: int = Field(0, description="Événements en brouillon")
    archived: int = Field(0, description="Événements archivés")
    upcoming: int = Field(0, description="Événements à venir")
    past: int = Field(0, description="Événements passés")
    by_type: dict[str, int] = Field(default_factory=dict, description="Par type")
    timeline: list[TimelineDataPoint] = Field(
        default_factory=list, description="Tendance par mois"
    )


class NewsStatistics(BaseModel):
    """Statistiques des actualités."""

    total: int = Field(0, description="Total des actualités")
    published: int = Field(0, description="Actualités publiées")
    draft: int = Field(0, description="Actualités en brouillon")
    archived: int = Field(0, description="Actualités archivées")
    headline: int = Field(0, description="Actualités à la une")
    featured: int = Field(0, description="Actualités mises en avant")
    timeline: list[TimelineDataPoint] = Field(
        default_factory=list, description="Publications par mois"
    )
