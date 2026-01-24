"""
Schémas Campus
==============

Schémas Pydantic pour la gestion des campus.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


# =============================================================================
# CAMPUS TEAM
# =============================================================================


class CampusTeamBase(BaseModel):
    """Schéma de base pour les membres d'équipe campus."""

    user_external_id: str = Field(..., description="ID de l'utilisateur")
    position: str = Field(..., min_length=1, max_length=255, description="Poste occupé")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")
    start_date: date | None = Field(None, description="Date de début")
    end_date: date | None = Field(None, description="Date de fin")


class CampusTeamCreate(CampusTeamBase):
    """Schéma pour la création d'un membre d'équipe."""

    campus_id: str = Field(..., description="ID du campus")
    active: bool = Field(True, description="Statut actif")


class CampusTeamUpdate(BaseModel):
    """Schéma pour la mise à jour d'un membre d'équipe."""

    user_external_id: str | None = None
    position: str | None = Field(None, min_length=1, max_length=255)
    display_order: int | None = Field(None, ge=0)
    start_date: date | None = None
    end_date: date | None = None
    active: bool | None = None


class CampusTeamRead(CampusTeamBase):
    """Schéma pour la lecture d'un membre d'équipe."""

    id: str
    campus_id: str
    active: bool

    model_config = {"from_attributes": True}


class CampusTeamReorder(BaseModel):
    """Schéma pour le réordonnancement des membres d'équipe."""

    team_member_ids: list[str] = Field(..., min_length=1, description="Liste ordonnée des IDs")


# =============================================================================
# CAMPUS PARTNERS
# =============================================================================


class CampusPartnerBase(BaseModel):
    """Schéma de base pour les partenaires de campus."""

    partner_external_id: str = Field(..., description="ID du partenaire")
    start_date: date | None = Field(None, description="Date de début du partenariat")
    end_date: date | None = Field(None, description="Date de fin du partenariat")


class CampusPartnerCreate(CampusPartnerBase):
    """Schéma pour l'ajout d'un partenaire à un campus."""

    pass


class CampusPartnerUpdate(BaseModel):
    """Schéma pour la mise à jour d'un partenariat."""

    start_date: date | None = None
    end_date: date | None = None


class CampusPartnerRead(CampusPartnerBase):
    """Schéma pour la lecture d'un partenariat."""

    campus_id: str

    model_config = {"from_attributes": True}


# =============================================================================
# CAMPUS MEDIA LIBRARY
# =============================================================================


class CampusMediaLibraryCreate(BaseModel):
    """Schéma pour l'ajout d'un album à la médiathèque."""

    album_external_id: str = Field(..., description="ID de l'album")


class CampusMediaLibraryRead(BaseModel):
    """Schéma pour la lecture d'une entrée médiathèque."""

    campus_id: str
    album_external_id: str

    model_config = {"from_attributes": True}


# =============================================================================
# CAMPUS
# =============================================================================


class CampusBase(BaseModel):
    """Schéma de base pour les campus."""

    code: str = Field(..., min_length=1, max_length=20, description="Code unique du campus")
    name: str = Field(..., min_length=1, max_length=255, description="Nom du campus")
    description: str | None = Field(None, description="Description du campus")
    cover_image_external_id: str | None = Field(None, description="ID de l'image de couverture")
    country_external_id: str | None = Field(None, description="ID du pays")
    head_external_id: str | None = Field(None, description="ID du responsable")
    album_external_id: str | None = Field(None, description="ID de l'album principal")
    email: EmailStr | None = Field(None, description="Email du campus")
    phone: str | None = Field(None, max_length=30, description="Téléphone du campus")
    city: str | None = Field(None, max_length=100, description="Ville")
    address: str | None = Field(None, description="Adresse complète")
    postal_code: str | None = Field(None, max_length=20, description="Code postal")
    latitude: Decimal | None = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Decimal | None = Field(None, ge=-180, le=180, description="Longitude")
    is_headquarters: bool = Field(False, description="Est le siège principal")


class CampusCreate(CampusBase):
    """Schéma pour la création d'un campus."""

    active: bool = Field(True, description="Statut actif")


class CampusUpdate(BaseModel):
    """Schéma pour la mise à jour d'un campus."""

    code: str | None = Field(None, min_length=1, max_length=20)
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    cover_image_external_id: str | None = None
    country_external_id: str | None = None
    head_external_id: str | None = None
    album_external_id: str | None = None
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=30)
    city: str | None = Field(None, max_length=100)
    address: str | None = None
    postal_code: str | None = Field(None, max_length=20)
    latitude: Decimal | None = Field(None, ge=-90, le=90)
    longitude: Decimal | None = Field(None, ge=-180, le=180)
    is_headquarters: bool | None = None
    active: bool | None = None


class CampusRead(CampusBase):
    """Schéma pour la lecture d'un campus."""

    id: str
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CampusWithTeam(CampusRead):
    """Schéma pour un campus avec son équipe."""

    team_members: list[CampusTeamRead] = []


class CampusPublic(BaseModel):
    """Schéma pour l'affichage public d'un campus."""

    id: str
    code: str
    name: str
    description: str | None
    cover_image_external_id: str | None
    country_external_id: str | None
    city: str | None
    email: str | None
    phone: str | None
    is_headquarters: bool

    model_config = {"from_attributes": True}
