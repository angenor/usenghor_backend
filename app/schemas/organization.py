"""
Schémas Organization
====================

Schémas Pydantic pour la gestion de la structure organisationnelle.
"""

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.organization import ProjectStatus


# =============================================================================
# SERVICE OBJECTIVES
# =============================================================================


class ServiceObjectiveBase(BaseModel):
    """Schéma de base pour les objectifs de service."""

    title: str = Field(..., min_length=1, max_length=255, description="Titre de l'objectif")
    description: str | None = Field(None, description="Description de l'objectif")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class ServiceObjectiveCreate(ServiceObjectiveBase):
    """Schéma pour la création d'un objectif."""

    pass


class ServiceObjectiveUpdate(BaseModel):
    """Schéma pour la mise à jour d'un objectif."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    display_order: int | None = Field(None, ge=0)


class ServiceObjectiveRead(ServiceObjectiveBase):
    """Schéma pour la lecture d'un objectif."""

    id: str
    service_id: str

    model_config = {"from_attributes": True}


# =============================================================================
# SERVICE ACHIEVEMENTS
# =============================================================================


class ServiceAchievementBase(BaseModel):
    """Schéma de base pour les réalisations de service."""

    title: str = Field(..., min_length=1, max_length=255, description="Titre de la réalisation")
    description: str | None = Field(None, description="Description")
    type: str | None = Field(None, max_length=100, description="Type de réalisation")
    cover_image_external_id: str | None = Field(None, description="ID de l'image de couverture")
    achievement_date: date | None = Field(None, description="Date de la réalisation")


class ServiceAchievementCreate(ServiceAchievementBase):
    """Schéma pour la création d'une réalisation."""

    pass


class ServiceAchievementUpdate(BaseModel):
    """Schéma pour la mise à jour d'une réalisation."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    type: str | None = Field(None, max_length=100)
    cover_image_external_id: str | None = None
    achievement_date: date | None = None


class ServiceAchievementRead(ServiceAchievementBase):
    """Schéma pour la lecture d'une réalisation."""

    id: str
    service_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# SERVICE PROJECTS
# =============================================================================


class ServiceProjectBase(BaseModel):
    """Schéma de base pour les projets de service."""

    title: str = Field(..., min_length=1, max_length=255, description="Titre du projet")
    description: str | None = Field(None, description="Description")
    cover_image_external_id: str | None = Field(None, description="ID de l'image de couverture")
    progress: int = Field(0, ge=0, le=100, description="Progression en %")
    status: ProjectStatus = Field(ProjectStatus.PLANNED, description="Statut du projet")
    start_date: date | None = Field(None, description="Date de début")
    expected_end_date: date | None = Field(None, description="Date de fin prévue")


class ServiceProjectCreate(ServiceProjectBase):
    """Schéma pour la création d'un projet."""

    pass


class ServiceProjectUpdate(BaseModel):
    """Schéma pour la mise à jour d'un projet."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    cover_image_external_id: str | None = None
    progress: int | None = Field(None, ge=0, le=100)
    status: ProjectStatus | None = None
    start_date: date | None = None
    expected_end_date: date | None = None


class ServiceProjectRead(ServiceProjectBase):
    """Schéma pour la lecture d'un projet."""

    id: str
    service_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# SERVICE TEAM
# =============================================================================


class ServiceTeamBase(BaseModel):
    """Schéma de base pour les membres d'équipe d'un service."""

    user_external_id: str = Field(..., description="ID externe de l'utilisateur")
    position: str = Field(..., min_length=1, max_length=255, description="Poste/fonction")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")
    start_date: date | None = Field(None, description="Date de début")
    end_date: date | None = Field(None, description="Date de fin")
    active: bool = Field(True, description="Membre actif")


class ServiceTeamCreate(ServiceTeamBase):
    """Schéma pour l'ajout d'un membre à l'équipe."""

    pass


class ServiceTeamUpdate(BaseModel):
    """Schéma pour la mise à jour d'un membre de l'équipe."""

    user_external_id: str | None = None
    position: str | None = Field(None, min_length=1, max_length=255)
    display_order: int | None = Field(None, ge=0)
    start_date: date | None = None
    end_date: date | None = None
    active: bool | None = None


class ServiceTeamRead(ServiceTeamBase):
    """Schéma pour la lecture d'un membre de l'équipe."""

    id: str
    service_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# SERVICES
# =============================================================================


class ServiceBase(BaseModel):
    """Schéma de base pour les services."""

    name: str = Field(..., min_length=1, max_length=255, description="Nom du service")
    description: str | None = Field(None, description="Description du service")
    mission: str | None = Field(None, description="Mission du service")
    email: EmailStr | None = Field(None, description="Email du service")
    phone: str | None = Field(None, max_length=30, description="Téléphone du service")
    head_external_id: str | None = Field(None, description="ID du responsable")
    album_external_id: str | None = Field(None, description="ID de l'album")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class ServiceCreate(ServiceBase):
    """Schéma pour la création d'un service."""

    sector_id: str | None = Field(None, description="ID du secteur parent")
    active: bool = Field(True, description="Statut actif")


class ServiceUpdate(BaseModel):
    """Schéma pour la mise à jour d'un service."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    mission: str | None = None
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=30)
    sector_id: str | None = None
    head_external_id: str | None = None
    album_external_id: str | None = None
    display_order: int | None = Field(None, ge=0)
    active: bool | None = None


class ServiceRead(ServiceBase):
    """Schéma pour la lecture d'un service."""

    id: str
    sector_id: str | None
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ServiceWithDetails(ServiceRead):
    """Schéma pour un service avec ses détails (objectifs, réalisations, projets, équipe)."""

    objectives: list[ServiceObjectiveRead] = []
    achievements: list[ServiceAchievementRead] = []
    projects: list[ServiceProjectRead] = []
    team: list[ServiceTeamRead] = []


class ServiceReorder(BaseModel):
    """Schéma pour le réordonnancement des services."""

    service_ids: list[str] = Field(..., min_length=1, description="Liste ordonnée des IDs")


# =============================================================================
# SECTORS
# =============================================================================


class SectorBase(BaseModel):
    """Schéma de base pour les secteurs."""

    code: str = Field(..., min_length=1, max_length=20, description="Code unique du secteur")
    name: str = Field(..., min_length=1, max_length=255, description="Nom du secteur")
    description: str | None = Field(None, description="Description du secteur")
    mission: str | None = Field(None, description="Mission du secteur")
    icon_external_id: str | None = Field(None, description="ID de l'icône")
    cover_image_external_id: str | None = Field(None, description="ID de l'image de couverture")
    head_external_id: str | None = Field(None, description="ID du responsable")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class SectorCreate(SectorBase):
    """Schéma pour la création d'un secteur."""

    active: bool = Field(True, description="Statut actif")


class SectorUpdate(BaseModel):
    """Schéma pour la mise à jour d'un secteur."""

    code: str | None = Field(None, min_length=1, max_length=20)
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    mission: str | None = None
    icon_external_id: str | None = None
    cover_image_external_id: str | None = None
    head_external_id: str | None = None
    display_order: int | None = Field(None, ge=0)
    active: bool | None = None


class SectorRead(SectorBase):
    """Schéma pour la lecture d'un secteur."""

    id: str
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SectorWithServices(SectorRead):
    """Schéma pour un secteur avec ses services."""

    services: list[ServiceRead] = []


class SectorReorder(BaseModel):
    """Schéma pour le réordonnancement des secteurs."""

    sector_ids: list[str] = Field(..., min_length=1, description="Liste ordonnée des IDs")


# =============================================================================
# PUBLIC SCHEMAS
# =============================================================================


class SectorPublic(BaseModel):
    """Schéma public pour un secteur (sans données sensibles)."""

    id: str
    code: str
    name: str
    description: str | None
    mission: str | None
    icon_external_id: str | None
    cover_image_external_id: str | None
    display_order: int

    model_config = {"from_attributes": True}


class ServicePublic(BaseModel):
    """Schéma public pour un service (sans données sensibles)."""

    id: str
    name: str
    description: str | None
    mission: str | None
    email: str | None
    phone: str | None
    sector_id: str | None
    head_external_id: str | None
    album_external_id: str | None
    display_order: int

    model_config = {"from_attributes": True}


class ServicePublicWithDetails(ServicePublic):
    """Schéma public pour un service avec ses détails."""

    objectives: list[ServiceObjectiveRead] = []
    achievements: list[ServiceAchievementRead] = []
    projects: list[ServiceProjectRead] = []
    team: list[ServiceTeamRead] = []


class SectorPublicWithServices(SectorPublic):
    """Schéma public pour un secteur avec ses services."""

    services: list[ServicePublic] = []
