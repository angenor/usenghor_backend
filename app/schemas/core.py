"""
Schémas Core
============

Schémas Pydantic pour les données de référence (pays).
"""

from datetime import datetime

from pydantic import BaseModel, Field


# =============================================================================
# COUNTRIES
# =============================================================================


class CountryBase(BaseModel):
    """Schéma de base pour les pays."""

    iso_code: str = Field(..., min_length=2, max_length=2, description="Code ISO 2 lettres")
    iso_code3: str | None = Field(None, min_length=3, max_length=3, description="Code ISO 3 lettres")
    name_fr: str = Field(..., min_length=1, max_length=100, description="Nom en français")
    name_en: str | None = Field(None, max_length=100, description="Nom en anglais")
    name_ar: str | None = Field(None, max_length=100, description="Nom en arabe")
    phone_code: str | None = Field(None, max_length=10, description="Indicatif téléphonique")


class CountryCreate(CountryBase):
    """Schéma pour la création d'un pays."""

    active: bool = Field(True, description="Statut actif")


class CountryUpdate(BaseModel):
    """Schéma pour la mise à jour d'un pays."""

    iso_code: str | None = Field(None, min_length=2, max_length=2)
    iso_code3: str | None = Field(None, min_length=3, max_length=3)
    name_fr: str | None = Field(None, min_length=1, max_length=100)
    name_en: str | None = Field(None, max_length=100)
    name_ar: str | None = Field(None, max_length=100)
    phone_code: str | None = Field(None, max_length=10)
    active: bool | None = None


class CountryRead(CountryBase):
    """Schéma pour la lecture d'un pays."""

    id: str
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CountryPublic(BaseModel):
    """Schéma public pour les pays (sans dates)."""

    id: str
    iso_code: str
    iso_code3: str | None
    name_fr: str
    name_en: str | None
    name_ar: str | None
    phone_code: str | None

    model_config = {"from_attributes": True}


class CountryBulkToggle(BaseModel):
    """Schéma pour le basculement en masse."""

    country_ids: list[str] = Field(..., min_length=1, description="Liste des IDs")
    active: bool = Field(..., description="Nouveau statut actif")


class CountryImportISO(BaseModel):
    """Schéma pour l'import des pays ISO."""

    overwrite_existing: bool = Field(False, description="Écraser les pays existants")
