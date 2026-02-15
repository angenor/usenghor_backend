"""
Schémas Academic
================

Schémas Pydantic pour la gestion des programmes et formations.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.academic import ProgramType
from app.models.base import PublicationStatus


# =============================================================================
# PROGRAM COURSE
# =============================================================================


class ProgramCourseBase(BaseModel):
    """Schéma de base pour les cours."""

    code: str | None = Field(None, max_length=20, description="Code du cours")
    title: str = Field(..., min_length=1, max_length=255, description="Titre du cours")
    description: str | None = Field(None, description="Description du cours")
    credits: int | None = Field(None, ge=0, description="Crédits ECTS")
    lecture_hours: int = Field(0, ge=0, description="Heures de cours magistraux")
    tutorial_hours: int = Field(0, ge=0, description="Heures de TD")
    practical_hours: int = Field(0, ge=0, description="Heures de TP")
    coefficient: Decimal | None = Field(None, ge=0, description="Coefficient")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class ProgramCourseCreate(ProgramCourseBase):
    """Schéma pour la création d'un cours."""

    pass


class ProgramCourseUpdate(BaseModel):
    """Schéma pour la mise à jour d'un cours."""

    code: str | None = Field(None, max_length=20)
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    credits: int | None = Field(None, ge=0)
    lecture_hours: int | None = Field(None, ge=0)
    tutorial_hours: int | None = Field(None, ge=0)
    practical_hours: int | None = Field(None, ge=0)
    coefficient: Decimal | None = Field(None, ge=0)
    display_order: int | None = Field(None, ge=0)


class ProgramCourseRead(ProgramCourseBase):
    """Schéma pour la lecture d'un cours."""

    id: str
    semester_id: str

    model_config = {"from_attributes": True}


class ProgramCourseReorder(BaseModel):
    """Schéma pour le réordonnancement des cours."""

    course_ids: list[str] = Field(..., min_length=1, description="Liste ordonnée des IDs")


# =============================================================================
# PROGRAM SEMESTER
# =============================================================================


class ProgramSemesterBase(BaseModel):
    """Schéma de base pour les semestres."""

    number: int = Field(..., ge=1, description="Numéro du semestre")
    title: str | None = Field(None, max_length=255, description="Titre du semestre")
    credits: int = Field(1, ge=0, description="Crédits du semestre")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class ProgramSemesterCreate(ProgramSemesterBase):
    """Schéma pour la création d'un semestre."""

    program_id: str = Field(..., description="ID du programme")


class ProgramSemesterUpdate(BaseModel):
    """Schéma pour la mise à jour d'un semestre."""

    number: int | None = Field(None, ge=1)
    title: str | None = Field(None, max_length=255)
    credits: int | None = Field(None, ge=0)
    display_order: int | None = Field(None, ge=0)


class ProgramSemesterRead(ProgramSemesterBase):
    """Schéma pour la lecture d'un semestre."""

    id: str
    program_id: str

    model_config = {"from_attributes": True}


class ProgramSemesterWithCourses(ProgramSemesterRead):
    """Schéma pour un semestre avec ses cours."""

    courses: list[ProgramCourseRead] = []


# =============================================================================
# PROGRAM SKILL
# =============================================================================


class ProgramSkillBase(BaseModel):
    """Schéma de base pour les compétences."""

    title: str = Field(..., min_length=1, max_length=255, description="Titre de la compétence")
    description: str | None = Field(None, description="Description de la compétence")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class ProgramSkillCreate(ProgramSkillBase):
    """Schéma pour la création d'une compétence."""

    program_id: str = Field(..., description="ID du programme")


class ProgramSkillUpdate(BaseModel):
    """Schéma pour la mise à jour d'une compétence."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    display_order: int | None = Field(None, ge=0)


class ProgramSkillRead(ProgramSkillBase):
    """Schéma pour la lecture d'une compétence."""

    id: str
    program_id: str

    model_config = {"from_attributes": True}


class ProgramSkillReorder(BaseModel):
    """Schéma pour le réordonnancement des compétences."""

    skill_ids: list[str] = Field(..., min_length=1, description="Liste ordonnée des IDs")


# =============================================================================
# PROGRAM CAREER OPPORTUNITY
# =============================================================================


class ProgramCareerOpportunityBase(BaseModel):
    """Schéma de base pour les débouchés."""

    title: str = Field(..., min_length=1, max_length=255, description="Titre du débouché")
    description: str | None = Field(None, description="Description du débouché")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class ProgramCareerOpportunityCreate(ProgramCareerOpportunityBase):
    """Schéma pour la création d'un débouché."""

    program_id: str = Field(..., description="ID du programme")


class ProgramCareerOpportunityUpdate(BaseModel):
    """Schéma pour la mise à jour d'un débouché."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    display_order: int | None = Field(None, ge=0)


class ProgramCareerOpportunityRead(ProgramCareerOpportunityBase):
    """Schéma pour la lecture d'un débouché."""

    id: str
    program_id: str

    model_config = {"from_attributes": True}


class ProgramCareerOpportunityReorder(BaseModel):
    """Schéma pour le réordonnancement des débouchés."""

    opportunity_ids: list[str] = Field(..., min_length=1, description="Liste ordonnée des IDs")


# =============================================================================
# PROGRAM FIELD (Champs disciplinaires)
# =============================================================================


class ProgramFieldBase(BaseModel):
    """Schéma de base pour les champs disciplinaires."""

    name: str = Field(..., min_length=1, max_length=255, description="Nom du champ")
    slug: str = Field(..., min_length=1, max_length=255, description="Slug URL")
    description: str | None = Field(None, description="Description du champ")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class ProgramFieldCreate(ProgramFieldBase):
    """Schéma pour la création d'un champ."""

    pass


class ProgramFieldUpdate(BaseModel):
    """Schéma pour la mise à jour d'un champ."""

    name: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    display_order: int | None = Field(None, ge=0)


class ProgramFieldRead(ProgramFieldBase):
    """Schéma pour la lecture d'un champ."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProgramFieldReorder(BaseModel):
    """Schéma pour le réordonnancement des champs."""

    field_ids: list[str] = Field(..., min_length=1, description="Liste ordonnée des IDs")


# =============================================================================
# PROGRAM CAMPUS
# =============================================================================


class ProgramCampusCreate(BaseModel):
    """Schéma pour l'ajout d'un campus à un programme."""

    campus_external_id: str = Field(..., description="ID du campus")


class ProgramCampusRead(BaseModel):
    """Schéma pour la lecture d'un campus de programme."""

    program_id: str
    campus_external_id: str

    model_config = {"from_attributes": True}


# =============================================================================
# PROGRAM PARTNER
# =============================================================================


class ProgramPartnerBase(BaseModel):
    """Schéma de base pour les partenaires de programme."""

    partner_external_id: str = Field(..., description="ID du partenaire")
    partnership_type: str | None = Field(None, max_length=100, description="Type de partenariat")


class ProgramPartnerCreate(ProgramPartnerBase):
    """Schéma pour l'ajout d'un partenaire à un programme."""

    pass


class ProgramPartnerUpdate(BaseModel):
    """Schéma pour la mise à jour d'un partenariat."""

    partnership_type: str | None = Field(None, max_length=100)


class ProgramPartnerRead(ProgramPartnerBase):
    """Schéma pour la lecture d'un partenariat."""

    program_id: str

    model_config = {"from_attributes": True}


# =============================================================================
# PROGRAM
# =============================================================================


class ProgramBase(BaseModel):
    """Schéma de base pour les programmes."""

    code: str = Field(..., min_length=1, max_length=30, description="Code unique du programme")
    title: str = Field(..., min_length=1, max_length=255, description="Titre du programme")
    subtitle: str | None = Field(None, max_length=255, description="Sous-titre")
    slug: str = Field(..., min_length=1, max_length=255, description="Slug URL")
    description: str | None = Field(None, description="Description du programme")
    teaching_methods: str | None = Field(None, description="Méthodes pédagogiques")
    cover_image_external_id: str | None = Field(None, description="ID de l'image de couverture")
    sector_external_id: str | None = Field(None, description="ID du secteur")
    campus_external_id: str | None = Field(None, description="ID du campus")
    service_external_id: str | None = Field(None, description="ID du service")
    coordinator_external_id: str | None = Field(None, description="ID du coordinateur")
    field_id: str | None = Field(None, description="ID du champ disciplinaire (certificats)")
    type: ProgramType = Field(..., description="Type de programme")
    duration_months: int | None = Field(None, ge=1, description="Durée en mois")
    credits: int | None = Field(None, ge=0, description="Crédits ECTS")
    degree_awarded: str | None = Field(None, max_length=255, description="Diplôme délivré")
    required_degree: str | None = Field(None, description="Diplôme requis pour l'admission")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class ProgramCreate(ProgramBase):
    """Schéma pour la création d'un programme."""

    status: PublicationStatus = Field(
        PublicationStatus.DRAFT, description="Statut de publication"
    )
    is_featured: bool = Field(False, description="Formation mise à la une")


class ProgramUpdate(BaseModel):
    """Schéma pour la mise à jour d'un programme."""

    code: str | None = Field(None, min_length=1, max_length=30)
    title: str | None = Field(None, min_length=1, max_length=255)
    subtitle: str | None = Field(None, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    teaching_methods: str | None = None
    cover_image_external_id: str | None = None
    sector_external_id: str | None = None
    campus_external_id: str | None = None
    service_external_id: str | None = None
    coordinator_external_id: str | None = None
    field_id: str | None = None
    type: ProgramType | None = None
    duration_months: int | None = Field(None, ge=1)
    credits: int | None = Field(None, ge=0)
    degree_awarded: str | None = Field(None, max_length=255)
    required_degree: str | None = None
    status: PublicationStatus | None = None
    is_featured: bool | None = None
    display_order: int | None = Field(None, ge=0)


class ProgramRead(ProgramBase):
    """Schéma pour la lecture d'un programme."""

    id: str
    status: PublicationStatus
    is_featured: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProgramWithDetails(ProgramRead):
    """Schéma pour un programme avec tous ses détails."""

    semesters: list[ProgramSemesterWithCourses] = []
    skills: list[ProgramSkillRead] = []
    career_opportunities: list[ProgramCareerOpportunityRead] = []


class ProgramPublic(BaseModel):
    """Schéma pour l'affichage public d'un programme."""

    id: str
    code: str
    title: str
    subtitle: str | None
    slug: str
    description: str | None
    teaching_methods: str | None
    cover_image_external_id: str | None
    sector_external_id: str | None
    field_id: str | None = None
    field_name: str | None = None
    type: ProgramType
    duration_months: int | None
    credits: int | None
    degree_awarded: str | None
    required_degree: str | None
    is_featured: bool

    model_config = {"from_attributes": True}


class ProgramPublicWithDetails(ProgramPublic):
    """Schéma pour l'affichage public d'un programme avec détails."""

    semesters: list[ProgramSemesterWithCourses] = []
    skills: list[ProgramSkillRead] = []
    career_opportunities: list[ProgramCareerOpportunityRead] = []


class ProgramReorder(BaseModel):
    """Schéma pour le réordonnancement des programmes."""

    program_ids: list[str] = Field(..., min_length=1, description="Liste ordonnée des IDs")


class ProgramDuplicate(BaseModel):
    """Schéma pour la duplication d'un programme."""

    new_code: str = Field(..., min_length=1, max_length=30, description="Nouveau code")
    new_title: str = Field(..., min_length=1, max_length=255, description="Nouveau titre")
    new_slug: str = Field(..., min_length=1, max_length=255, description="Nouveau slug")
