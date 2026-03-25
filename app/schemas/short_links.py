"""
Schémas Short Links
====================

Schémas Pydantic pour le réducteur de liens.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ShortLinkCreate(BaseModel):
    """Schéma pour la création d'un lien court."""

    target_url: str = Field(
        ..., min_length=1, max_length=2000, description="URL de destination"
    )


class ShortLinkRead(BaseModel):
    """Schéma pour la lecture d'un lien court (admin)."""

    id: str
    code: str
    target_url: str
    full_short_url: str = ""
    created_by_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShortLinkPublicResolve(BaseModel):
    """Schéma pour la résolution publique d'un lien court."""

    target_url: str

    model_config = {"from_attributes": True}


class AllowedDomainCreate(BaseModel):
    """Schéma pour l'ajout d'un domaine autorisé."""

    domain: str = Field(
        ..., min_length=1, max_length=255, description="Nom de domaine"
    )


class AllowedDomainRead(BaseModel):
    """Schéma pour la lecture d'un domaine autorisé."""

    id: str
    domain: str
    created_at: datetime

    model_config = {"from_attributes": True}
