"""
Schémas Media
=============

Schémas Pydantic pour la gestion des médias (images, vidéos, documents).
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.base import MediaType, PublicationStatus


# =============================================================================
# MEDIA
# =============================================================================


class MediaBase(BaseModel):
    """Schéma de base pour les médias."""

    name: str = Field(..., min_length=1, max_length=255, description="Nom du fichier")
    description: str | None = Field(None, description="Description")
    alt_text: str | None = Field(None, max_length=255, description="Texte alternatif")
    credits: str | None = Field(None, max_length=255, description="Crédits")


class MediaCreate(MediaBase):
    """Schéma pour la création d'un média (upload)."""

    type: MediaType = Field(..., description="Type de média")
    url: str = Field(..., max_length=500, description="URL du fichier")
    is_external_url: bool = Field(False, description="URL externe")
    size_bytes: int | None = Field(None, ge=0, description="Taille en octets")
    mime_type: str | None = Field(None, max_length=100, description="Type MIME")
    width: int | None = Field(None, ge=0, description="Largeur (images/vidéos)")
    height: int | None = Field(None, ge=0, description="Hauteur (images/vidéos)")
    duration_seconds: int | None = Field(None, ge=0, description="Durée (audio/vidéo)")


class MediaUpdate(BaseModel):
    """Schéma pour la mise à jour d'un média."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    alt_text: str | None = Field(None, max_length=255)
    credits: str | None = Field(None, max_length=255)


class MediaRead(MediaBase):
    """Schéma pour la lecture d'un média."""

    id: str
    type: MediaType
    url: str
    is_external_url: bool
    size_bytes: int | None
    mime_type: str | None
    width: int | None
    height: int | None
    duration_seconds: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MediaUploadResponse(BaseModel):
    """Réponse après upload d'un fichier."""

    id: str
    name: str
    url: str
    type: MediaType
    mime_type: str | None
    size_bytes: int | None

    model_config = {"from_attributes": True}


class MediaBulkDelete(BaseModel):
    """Schéma pour la suppression en masse."""

    media_ids: list[str] = Field(..., min_length=1, description="Liste des IDs")


class MediaStatistics(BaseModel):
    """Statistiques des médias."""

    total: int
    by_type: dict[str, int]
    total_size_bytes: int


# =============================================================================
# ALBUMS
# =============================================================================


class AlbumBase(BaseModel):
    """Schéma de base pour les albums."""

    title: str = Field(..., min_length=1, max_length=255, description="Titre")
    description: str | None = Field(None, description="Description")


class AlbumCreate(AlbumBase):
    """Schéma pour la création d'un album."""

    status: PublicationStatus = Field(
        PublicationStatus.DRAFT, description="Statut de publication"
    )


class AlbumUpdate(BaseModel):
    """Schéma pour la mise à jour d'un album."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: PublicationStatus | None = None


class AlbumRead(AlbumBase):
    """Schéma pour la lecture d'un album."""

    id: str
    status: PublicationStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlbumWithMedia(AlbumRead):
    """Schéma pour un album avec ses médias."""

    media_items: list[MediaRead] = []


class AlbumMediaAdd(BaseModel):
    """Schéma pour ajouter des médias à un album."""

    media_ids: list[str] = Field(..., min_length=1, description="Liste des IDs médias")


class AlbumMediaReorder(BaseModel):
    """Schéma pour réordonner les médias d'un album."""

    media_order: list[str] = Field(
        ...,
        min_length=1,
        description="Liste des IDs médias dans le nouvel ordre",
    )
