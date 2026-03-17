"""
Schémas Fundraising
===================

Schémas Pydantic pour la gestion des levées de fonds.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.fundraising import ContributorCategory, FundraiserStatus


# =============================================================================
# CONTRIBUTEURS
# =============================================================================


class ContributorBase(BaseModel):
    """Schéma de base pour les contributeurs."""

    name: str = Field(..., min_length=1, max_length=255, description="Nom (FR)")
    name_en: str | None = Field(None, max_length=255, description="Nom (EN)")
    name_ar: str | None = Field(None, max_length=255, description="Nom (AR)")
    category: ContributorCategory = Field(..., description="Catégorie")
    amount: Decimal = Field(0, ge=0, description="Montant (EUR)")
    logo_external_id: str | None = Field(None, description="ID média logo")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class ContributorCreate(ContributorBase):
    """Schéma pour la création d'un contributeur."""

    pass


class ContributorUpdate(BaseModel):
    """Schéma pour la mise à jour d'un contributeur."""

    name: str | None = Field(None, min_length=1, max_length=255)
    name_en: str | None = Field(None, max_length=255)
    name_ar: str | None = Field(None, max_length=255)
    category: ContributorCategory | None = None
    amount: Decimal | None = Field(None, ge=0)
    logo_external_id: str | None = None
    display_order: int | None = Field(None, ge=0)


class ContributorRead(ContributorBase):
    """Schéma pour la lecture d'un contributeur."""

    id: str
    fundraiser_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContributorPublic(BaseModel):
    """Schéma public pour un contributeur."""

    id: str
    name: str
    name_en: str | None
    name_ar: str | None
    category: ContributorCategory
    amount: Decimal
    logo_external_id: str | None

    model_config = {"from_attributes": True}


# =============================================================================
# LEVÉES DE FONDS
# =============================================================================


class FundraiserBase(BaseModel):
    """Schéma de base pour les levées de fonds."""

    title: str = Field(..., min_length=1, max_length=255, description="Titre")
    slug: str = Field(..., min_length=1, max_length=255, description="Slug URL")
    description_html: str | None = Field(None, description="Description (HTML FR)")
    description_md: str | None = Field(None, description="Description (Markdown FR)")
    description_en_html: str | None = Field(None, description="Description (HTML EN)")
    description_en_md: str | None = Field(None, description="Description (Markdown EN)")
    description_ar_html: str | None = Field(None, description="Description (HTML AR)")
    description_ar_md: str | None = Field(None, description="Description (Markdown AR)")
    goal_amount: Decimal = Field(..., gt=0, description="Objectif financier (EUR)")


class FundraiserCreate(FundraiserBase):
    """Schéma pour la création d'une levée de fonds."""

    cover_image_external_id: str | None = None
    status: FundraiserStatus = FundraiserStatus.DRAFT


class FundraiserUpdate(BaseModel):
    """Schéma pour la mise à jour d'une levée de fonds."""

    title: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    description_html: str | None = None
    description_md: str | None = None
    description_en_html: str | None = None
    description_en_md: str | None = None
    description_ar_html: str | None = None
    description_ar_md: str | None = None
    cover_image_external_id: str | None = None
    goal_amount: Decimal | None = Field(None, gt=0)
    status: FundraiserStatus | None = None


class FundraiserRead(FundraiserBase):
    """Schéma pour la lecture d'une levée de fonds (admin)."""

    id: str
    cover_image_external_id: str | None
    status: FundraiserStatus
    total_raised: Decimal = Decimal("0")
    progress_percentage: float = 0.0
    contributor_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FundraiserPublic(BaseModel):
    """Schéma public pour la liste des levées de fonds."""

    id: str
    title: str
    slug: str
    cover_image_external_id: str | None
    goal_amount: Decimal
    total_raised: Decimal = Decimal("0")
    progress_percentage: float = 0.0
    status: FundraiserStatus
    contributor_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class FundraiserPublicDetail(BaseModel):
    """Schéma public pour le détail d'une levée de fonds."""

    id: str
    title: str
    slug: str
    description_html: str | None
    description_en_html: str | None
    description_ar_html: str | None
    cover_image_external_id: str | None
    goal_amount: Decimal
    total_raised: Decimal = Decimal("0")
    progress_percentage: float = 0.0
    status: FundraiserStatus
    contributors: list[ContributorPublic] = []
    news: list[dict] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# ASSOCIATION ACTUALITÉS
# =============================================================================


class FundraiserNewsCreate(BaseModel):
    """Schéma pour associer une actualité à une levée de fonds."""

    news_id: str = Field(..., description="ID de l'actualité à associer")


# =============================================================================
# STATISTIQUES
# =============================================================================


class FundraiserStatistics(BaseModel):
    """Statistiques des levées de fonds."""

    total: int = Field(0, description="Total")
    draft: int = Field(0, description="Brouillons")
    active: int = Field(0, description="En cours")
    completed: int = Field(0, description="Terminées")
    total_goal: Decimal = Field(Decimal("0"), description="Objectif total")
    total_raised: Decimal = Field(Decimal("0"), description="Total levé")
