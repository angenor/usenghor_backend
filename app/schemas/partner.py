"""
Schémas Partner
===============

Schémas Pydantic pour la gestion des partenaires.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, HttpUrl

from app.models.partner import PartnerType


class PartnerBase(BaseModel):
    """Schéma de base pour les partenaires."""

    name: str = Field(..., min_length=1, max_length=255, description="Nom du partenaire")
    description: str | None = Field(None, description="Description du partenaire")
    logo_external_id: str | None = Field(None, description="ID du logo")
    country_external_id: str | None = Field(None, description="ID du pays")
    website: str | None = Field(None, max_length=500, description="Site web")
    type: PartnerType = Field(..., description="Type de partenaire")
    email: EmailStr | None = Field(None, description="Email de contact")
    phone: str | None = Field(None, max_length=30, description="Téléphone")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class PartnerCreate(PartnerBase):
    """Schéma pour la création d'un partenaire."""

    active: bool = Field(True, description="Statut actif")


class PartnerUpdate(BaseModel):
    """Schéma pour la mise à jour d'un partenaire."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    logo_external_id: str | None = None
    country_external_id: str | None = None
    website: str | None = Field(None, max_length=500)
    type: PartnerType | None = None
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=30)
    display_order: int | None = Field(None, ge=0)
    active: bool | None = None


class PartnerRead(PartnerBase):
    """Schéma pour la lecture d'un partenaire."""

    id: str
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PartnerPublic(BaseModel):
    """Schéma pour l'affichage public d'un partenaire."""

    id: str
    name: str
    description: str | None
    logo_external_id: str | None
    country_external_id: str | None
    website: str | None
    type: PartnerType

    model_config = {"from_attributes": True}


class PartnerReorder(BaseModel):
    """Schéma pour le réordonnancement des partenaires."""

    partner_ids: list[str] = Field(..., min_length=1, description="Liste ordonnée des IDs")
