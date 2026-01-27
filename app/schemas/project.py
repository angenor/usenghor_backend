"""
Schémas Project
===============

Schémas Pydantic pour la gestion des projets institutionnels.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.base import PublicationStatus
from app.models.organization import ProjectStatus
from app.models.project import ProjectCallStatus, ProjectCallType


# =============================================================================
# CATEGORIES
# =============================================================================


class ProjectCategoryBase(BaseModel):
    """Schéma de base pour les catégories de projet."""

    name: str = Field(..., min_length=1, max_length=100, description="Nom")
    slug: str = Field(..., min_length=1, max_length=100, description="Slug URL")
    description: str | None = Field(None, description="Description")
    icon: str | None = Field(None, max_length=50, description="Icône")


class ProjectCategoryCreate(ProjectCategoryBase):
    """Schéma pour la création d'une catégorie."""

    pass


class ProjectCategoryUpdate(BaseModel):
    """Schéma pour la mise à jour d'une catégorie."""

    name: str | None = Field(None, min_length=1, max_length=100)
    slug: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    icon: str | None = None


class ProjectCategoryRead(ProjectCategoryBase):
    """Schéma pour la lecture d'une catégorie."""

    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# PROJECTS
# =============================================================================


class ProjectBase(BaseModel):
    """Schéma de base pour les projets."""

    title: str = Field(..., min_length=1, max_length=255, description="Titre")
    slug: str = Field(..., min_length=1, max_length=255, description="Slug URL")
    summary: str | None = Field(None, description="Résumé")
    description: str | None = Field(None, description="Description complète")


class ProjectCreate(ProjectBase):
    """Schéma pour la création d'un projet."""

    cover_image_external_id: str | None = Field(None, description="ID image couverture")
    department_external_id: str | None = Field(None, description="ID département")
    manager_external_id: str | None = Field(None, description="ID responsable")
    album_external_id: str | None = Field(None, description="ID album principal")
    start_date: date | None = Field(None, description="Date de début")
    end_date: date | None = Field(None, description="Date de fin")
    budget: Decimal | None = Field(None, ge=0, description="Budget")
    currency: str = Field("EUR", max_length=10, description="Devise")
    beneficiaries: str | None = Field(None, description="Bénéficiaires")
    status: ProjectStatus = Field(ProjectStatus.PLANNED, description="Statut")
    publication_status: PublicationStatus = Field(
        PublicationStatus.DRAFT, description="Statut publication"
    )
    category_ids: list[str] | None = Field(None, description="IDs catégories")
    country_ids: list[str] | None = Field(None, description="IDs pays")


class ProjectUpdate(BaseModel):
    """Schéma pour la mise à jour d'un projet."""

    title: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    summary: str | None = None
    description: str | None = None
    cover_image_external_id: str | None = None
    department_external_id: str | None = None
    manager_external_id: str | None = None
    album_external_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: Decimal | None = Field(None, ge=0)
    currency: str | None = Field(None, max_length=10)
    beneficiaries: str | None = None
    status: ProjectStatus | None = None
    publication_status: PublicationStatus | None = None
    category_ids: list[str] | None = None
    country_ids: list[str] | None = None


class ProjectRead(ProjectBase):
    """Schéma pour la lecture d'un projet."""

    id: str
    cover_image_external_id: str | None
    department_external_id: str | None
    manager_external_id: str | None
    album_external_id: str | None
    start_date: date | None
    end_date: date | None
    budget: Decimal | None
    currency: str
    beneficiaries: str | None
    status: ProjectStatus
    publication_status: PublicationStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectReadWithRelations(ProjectRead):
    """Schéma de projet avec relations."""

    categories: list[ProjectCategoryRead] = []


class ProjectPublic(BaseModel):
    """Schéma public pour un projet."""

    id: str
    title: str
    slug: str
    summary: str | None
    description: str | None
    cover_image_external_id: str | None
    start_date: date | None
    end_date: date | None
    status: ProjectStatus

    model_config = {"from_attributes": True}


# =============================================================================
# PROJECT COUNTRIES
# =============================================================================


class ProjectCountryCreate(BaseModel):
    """Schéma pour ajouter un pays à un projet."""

    country_external_id: str = Field(..., description="ID du pays")


class ProjectCountryRead(BaseModel):
    """Schéma pour la lecture d'un pays de projet."""

    project_id: str
    country_external_id: str

    model_config = {"from_attributes": True}


# =============================================================================
# PROJECT PARTNERS
# =============================================================================


class ProjectPartnerCreate(BaseModel):
    """Schéma pour ajouter un partenaire à un projet."""

    partner_external_id: str = Field(..., description="ID du partenaire")
    partner_role: str | None = Field(None, max_length=255, description="Rôle")


class ProjectPartnerUpdate(BaseModel):
    """Schéma pour mettre à jour un partenaire de projet."""

    partner_role: str | None = Field(None, max_length=255)


class ProjectPartnerRead(BaseModel):
    """Schéma pour la lecture d'un partenaire de projet."""

    project_id: str
    partner_external_id: str
    partner_role: str | None

    model_config = {"from_attributes": True}


# =============================================================================
# PROJECT CALLS
# =============================================================================


class ProjectCallBase(BaseModel):
    """Schéma de base pour les appels de projet."""

    title: str = Field(..., min_length=1, max_length=255, description="Titre")
    description: str | None = Field(None, description="Description")
    cover_image_external_id: str | None = Field(None, description="ID image de couverture")
    conditions: str | None = Field(None, description="Conditions")
    type: ProjectCallType | None = Field(None, description="Type d'appel")
    deadline: datetime | None = Field(None, description="Date limite")


class ProjectCallCreate(ProjectCallBase):
    """Schéma pour la création d'un appel de projet."""

    status: ProjectCallStatus = Field(
        ProjectCallStatus.UPCOMING, description="Statut"
    )


class ProjectCallUpdate(BaseModel):
    """Schéma pour la mise à jour d'un appel de projet."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    cover_image_external_id: str | None = None
    status: ProjectCallStatus | None = None
    conditions: str | None = None
    type: ProjectCallType | None = None
    deadline: datetime | None = None


class ProjectCallRead(ProjectCallBase):
    """Schéma pour la lecture d'un appel de projet."""

    id: str
    project_id: str
    status: ProjectCallStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# PROJECT MEDIA LIBRARY
# =============================================================================


class ProjectMediaCreate(BaseModel):
    """Schéma pour ajouter un album à la médiathèque."""

    album_external_id: str = Field(..., description="ID de l'album")


class ProjectMediaRead(BaseModel):
    """Schéma pour la lecture d'un album de médiathèque."""

    project_id: str
    album_external_id: str

    model_config = {"from_attributes": True}


# =============================================================================
# STATISTICS
# =============================================================================


class ProjectStatistics(BaseModel):
    """Statistiques globales des projets."""

    total_projects: int
    ongoing_projects: int
    completed_projects: int
    planned_projects: int
    suspended_projects: int
    total_budget: Decimal
    total_categories: int
