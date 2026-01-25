"""
Schémas Application
===================

Schémas Pydantic pour la gestion des appels à candidature et candidatures.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.models.application import (
    CallStatus,
    CallType,
    EmploymentStatus,
    ExperienceDuration,
    MaritalStatus,
    SubmittedApplicationStatus,
)
from app.models.base import PublicationStatus, Salutation


# =============================================================================
# CALL ELIGIBILITY CRITERIA
# =============================================================================


class CallEligibilityCriteriaBase(BaseModel):
    """Schéma de base pour les critères d'éligibilité."""

    criterion: str = Field(..., min_length=1, description="Critère d'éligibilité")
    is_mandatory: bool = Field(True, description="Critère obligatoire")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class CallEligibilityCriteriaCreate(CallEligibilityCriteriaBase):
    """Schéma pour la création d'un critère."""

    pass


class CallEligibilityCriteriaUpdate(BaseModel):
    """Schéma pour la mise à jour d'un critère."""

    criterion: str | None = Field(None, min_length=1)
    is_mandatory: bool | None = None
    display_order: int | None = Field(None, ge=0)


class CallEligibilityCriteriaRead(CallEligibilityCriteriaBase):
    """Schéma pour la lecture d'un critère."""

    id: str
    call_id: str

    model_config = {"from_attributes": True}


# =============================================================================
# CALL COVERAGE
# =============================================================================


class CallCoverageBase(BaseModel):
    """Schéma de base pour les prises en charge."""

    item: str = Field(..., min_length=1, max_length=255, description="Élément pris en charge")
    description: str | None = Field(None, description="Description")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class CallCoverageCreate(CallCoverageBase):
    """Schéma pour la création d'une prise en charge."""

    pass


class CallCoverageUpdate(BaseModel):
    """Schéma pour la mise à jour d'une prise en charge."""

    item: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    display_order: int | None = Field(None, ge=0)


class CallCoverageRead(CallCoverageBase):
    """Schéma pour la lecture d'une prise en charge."""

    id: str
    call_id: str

    model_config = {"from_attributes": True}


# =============================================================================
# CALL REQUIRED DOCUMENT
# =============================================================================


class CallRequiredDocumentBase(BaseModel):
    """Schéma de base pour les documents requis."""

    document_name: str = Field(..., min_length=1, max_length=255, description="Nom du document")
    description: str | None = Field(None, description="Description")
    is_mandatory: bool = Field(True, description="Document obligatoire")
    accepted_formats: str | None = Field(None, max_length=100, description="Formats acceptés (ex: pdf,doc)")
    max_size_mb: int | None = Field(None, ge=1, description="Taille max en Mo")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class CallRequiredDocumentCreate(CallRequiredDocumentBase):
    """Schéma pour la création d'un document requis."""

    pass


class CallRequiredDocumentUpdate(BaseModel):
    """Schéma pour la mise à jour d'un document requis."""

    document_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_mandatory: bool | None = None
    accepted_formats: str | None = Field(None, max_length=100)
    max_size_mb: int | None = Field(None, ge=1)
    display_order: int | None = Field(None, ge=0)


class CallRequiredDocumentRead(CallRequiredDocumentBase):
    """Schéma pour la lecture d'un document requis."""

    id: str
    call_id: str

    model_config = {"from_attributes": True}


# =============================================================================
# CALL SCHEDULE
# =============================================================================


class CallScheduleBase(BaseModel):
    """Schéma de base pour le calendrier."""

    step: str = Field(..., min_length=1, max_length=255, description="Étape du calendrier")
    start_date: date | None = Field(None, description="Date de début")
    end_date: date | None = Field(None, description="Date de fin")
    description: str | None = Field(None, description="Description")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class CallScheduleCreate(CallScheduleBase):
    """Schéma pour la création d'une étape."""

    pass


class CallScheduleUpdate(BaseModel):
    """Schéma pour la mise à jour d'une étape."""

    step: str | None = Field(None, min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    display_order: int | None = Field(None, ge=0)


class CallScheduleRead(CallScheduleBase):
    """Schéma pour la lecture d'une étape."""

    id: str
    call_id: str

    model_config = {"from_attributes": True}


# =============================================================================
# APPLICATION CALL
# =============================================================================


class ApplicationCallBase(BaseModel):
    """Schéma de base pour les appels à candidature."""

    title: str = Field(..., min_length=1, max_length=255, description="Titre de l'appel")
    slug: str = Field(..., min_length=1, max_length=255, description="Slug URL")
    description: str | None = Field(None, description="Description")
    cover_image_external_id: str | None = Field(None, description="ID de l'image de couverture")
    program_external_id: str | None = Field(None, description="ID du programme associé")
    campus_external_id: str | None = Field(None, description="ID du campus")
    type: CallType = Field(..., description="Type d'appel")
    status: CallStatus = Field(CallStatus.UPCOMING, description="Statut de l'appel")
    opening_date: date | None = Field(None, description="Date d'ouverture")
    deadline: datetime | None = Field(None, description="Date limite")
    program_start_date: date | None = Field(None, description="Début du programme")
    program_end_date: date | None = Field(None, description="Fin du programme")
    target_audience: str | None = Field(None, description="Public cible")
    registration_fee: Decimal | None = Field(None, ge=0, description="Frais d'inscription")
    currency: str = Field("EUR", max_length=10, description="Devise")
    external_form_url: str | None = Field(None, max_length=500, description="URL formulaire externe")
    use_internal_form: bool = Field(True, description="Utiliser le formulaire interne")


class ApplicationCallCreate(ApplicationCallBase):
    """Schéma pour la création d'un appel."""

    publication_status: PublicationStatus = Field(
        PublicationStatus.DRAFT, description="Statut de publication"
    )
    created_by_external_id: str | None = Field(None, description="ID du créateur")


class ApplicationCallUpdate(BaseModel):
    """Schéma pour la mise à jour d'un appel."""

    title: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    cover_image_external_id: str | None = None
    program_external_id: str | None = None
    campus_external_id: str | None = None
    type: CallType | None = None
    status: CallStatus | None = None
    opening_date: date | None = None
    deadline: datetime | None = None
    program_start_date: date | None = None
    program_end_date: date | None = None
    target_audience: str | None = None
    registration_fee: Decimal | None = Field(None, ge=0)
    currency: str | None = Field(None, max_length=10)
    external_form_url: str | None = Field(None, max_length=500)
    use_internal_form: bool | None = None
    publication_status: PublicationStatus | None = None


class ApplicationCallRead(ApplicationCallBase):
    """Schéma pour la lecture d'un appel."""

    id: str
    created_by_external_id: str | None
    publication_status: PublicationStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationCallWithDetails(ApplicationCallRead):
    """Schéma pour un appel avec tous ses détails."""

    eligibility_criteria: list[CallEligibilityCriteriaRead] = []
    coverage: list[CallCoverageRead] = []
    required_documents: list[CallRequiredDocumentRead] = []
    schedule: list[CallScheduleRead] = []


class ApplicationCallPublic(BaseModel):
    """Schéma pour l'affichage public d'un appel."""

    id: str
    title: str
    slug: str
    description: str | None
    cover_image_external_id: str | None
    program_external_id: str | None
    campus_external_id: str | None
    type: CallType
    status: CallStatus
    opening_date: date | None
    deadline: datetime | None
    program_start_date: date | None
    program_end_date: date | None
    target_audience: str | None
    registration_fee: Decimal | None
    currency: str
    external_form_url: str | None
    use_internal_form: bool

    model_config = {"from_attributes": True}


class ApplicationCallPublicWithDetails(ApplicationCallPublic):
    """Schéma pour l'affichage public d'un appel avec détails."""

    eligibility_criteria: list[CallEligibilityCriteriaRead] = []
    coverage: list[CallCoverageRead] = []
    required_documents: list[CallRequiredDocumentRead] = []
    schedule: list[CallScheduleRead] = []


# =============================================================================
# APPLICATION DEGREE
# =============================================================================


class ApplicationDegreeBase(BaseModel):
    """Schéma de base pour les diplômes."""

    title: str = Field(..., min_length=1, max_length=255, description="Intitulé du diplôme")
    year: int | None = Field(None, ge=1900, le=2100, description="Année d'obtention")
    institution: str | None = Field(None, max_length=255, description="Établissement")
    city: str | None = Field(None, max_length=100, description="Ville")
    country_external_id: str | None = Field(None, description="ID du pays")
    specialization: str | None = Field(None, max_length=255, description="Spécialisation")
    honors: str | None = Field(None, max_length=50, description="Mention")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")


class ApplicationDegreeCreate(ApplicationDegreeBase):
    """Schéma pour la création d'un diplôme."""

    pass


class ApplicationDegreeUpdate(BaseModel):
    """Schéma pour la mise à jour d'un diplôme."""

    title: str | None = Field(None, min_length=1, max_length=255)
    year: int | None = Field(None, ge=1900, le=2100)
    institution: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    country_external_id: str | None = None
    specialization: str | None = Field(None, max_length=255)
    honors: str | None = Field(None, max_length=50)
    display_order: int | None = Field(None, ge=0)


class ApplicationDegreeRead(ApplicationDegreeBase):
    """Schéma pour la lecture d'un diplôme."""

    id: str
    application_id: str

    model_config = {"from_attributes": True}


# =============================================================================
# APPLICATION DOCUMENT
# =============================================================================


class ApplicationDocumentBase(BaseModel):
    """Schéma de base pour les documents soumis."""

    document_name: str = Field(..., min_length=1, max_length=255, description="Nom du document")
    required_document_id: str | None = Field(None, description="ID du document requis associé")
    media_external_id: str | None = Field(None, description="ID du média")


class ApplicationDocumentCreate(ApplicationDocumentBase):
    """Schéma pour la création d'un document."""

    pass


class ApplicationDocumentUpdate(BaseModel):
    """Schéma pour la mise à jour d'un document."""

    document_name: str | None = Field(None, min_length=1, max_length=255)
    media_external_id: str | None = None
    is_valid: bool | None = None
    validation_comment: str | None = None


class ApplicationDocumentRead(ApplicationDocumentBase):
    """Schéma pour la lecture d'un document."""

    id: str
    application_id: str
    is_valid: bool | None
    validation_comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# APPLICATION
# =============================================================================


class ApplicationBase(BaseModel):
    """Schéma de base pour les candidatures."""

    call_id: str | None = Field(None, description="ID de l'appel")
    program_external_id: str | None = Field(None, description="ID du programme")

    # Informations personnelles
    salutation: Salutation | None = Field(None, description="Civilité")
    last_name: str = Field(..., min_length=1, max_length=100, description="Nom")
    first_name: str = Field(..., min_length=1, max_length=100, description="Prénom")
    birth_date: date | None = Field(None, description="Date de naissance")
    birth_city: str | None = Field(None, max_length=100, description="Ville de naissance")
    birth_country_external_id: str | None = Field(None, description="ID pays de naissance")
    nationality_external_id: str | None = Field(None, description="ID nationalité")
    country_external_id: str | None = Field(None, description="ID pays de résidence")
    marital_status: MaritalStatus | None = Field(None, description="Situation familiale")
    employment_status: EmploymentStatus | None = Field(None, description="Situation professionnelle")
    employment_status_other: str | None = Field(None, max_length=255, description="Autre situation")

    # Coordonnées
    address: str | None = Field(None, description="Adresse")
    city: str | None = Field(None, max_length=100, description="Ville")
    postal_code: str | None = Field(None, max_length=20, description="Code postal")
    phone: str | None = Field(None, max_length=30, description="Téléphone")
    phone_whatsapp: str | None = Field(None, max_length=30, description="WhatsApp")
    email: EmailStr = Field(..., description="Email")

    # Informations professionnelles
    has_work_experience: bool = Field(False, description="Expérience professionnelle")
    current_job: str | None = Field(None, max_length=255, description="Poste actuel")
    job_title: str | None = Field(None, max_length=255, description="Intitulé du poste")
    employer_name: str | None = Field(None, max_length=255, description="Employeur")
    employer_address: str | None = Field(None, description="Adresse employeur")
    employer_city: str | None = Field(None, max_length=100, description="Ville employeur")
    employer_country_external_id: str | None = Field(None, description="ID pays employeur")
    employer_phone: str | None = Field(None, max_length=30, description="Tél employeur")
    employer_email: EmailStr | None = Field(None, description="Email employeur")
    experience_duration: ExperienceDuration | None = Field(None, description="Durée d'expérience")

    # Formation académique
    highest_degree_level: str | None = Field(None, max_length=100, description="Niveau du plus haut diplôme")
    highest_degree_title: str | None = Field(None, max_length=255, description="Intitulé du diplôme")
    degree_date: date | None = Field(None, description="Date d'obtention")
    degree_location: str | None = Field(None, max_length=255, description="Lieu d'obtention")


class ApplicationCreate(ApplicationBase):
    """Schéma pour la création d'une candidature."""

    user_external_id: str | None = Field(None, description="ID de l'utilisateur")
    degrees: list[ApplicationDegreeCreate] = Field([], description="Diplômes")
    documents: list[ApplicationDocumentCreate] = Field([], description="Documents")


class ApplicationUpdate(BaseModel):
    """Schéma pour la mise à jour d'une candidature."""

    # Informations personnelles
    salutation: Salutation | None = None
    last_name: str | None = Field(None, min_length=1, max_length=100)
    first_name: str | None = Field(None, min_length=1, max_length=100)
    birth_date: date | None = None
    birth_city: str | None = Field(None, max_length=100)
    birth_country_external_id: str | None = None
    nationality_external_id: str | None = None
    country_external_id: str | None = None
    marital_status: MaritalStatus | None = None
    employment_status: EmploymentStatus | None = None
    employment_status_other: str | None = Field(None, max_length=255)

    # Coordonnées
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    postal_code: str | None = Field(None, max_length=20)
    phone: str | None = Field(None, max_length=30)
    phone_whatsapp: str | None = Field(None, max_length=30)
    email: EmailStr | None = None

    # Informations professionnelles
    has_work_experience: bool | None = None
    current_job: str | None = Field(None, max_length=255)
    job_title: str | None = Field(None, max_length=255)
    employer_name: str | None = Field(None, max_length=255)
    employer_address: str | None = None
    employer_city: str | None = Field(None, max_length=100)
    employer_country_external_id: str | None = None
    employer_phone: str | None = Field(None, max_length=30)
    employer_email: EmailStr | None = None
    experience_duration: ExperienceDuration | None = None

    # Formation académique
    highest_degree_level: str | None = Field(None, max_length=100)
    highest_degree_title: str | None = Field(None, max_length=255)
    degree_date: date | None = None
    degree_location: str | None = Field(None, max_length=255)


class ApplicationStatusUpdate(BaseModel):
    """Schéma pour la mise à jour du statut d'une candidature."""

    status: SubmittedApplicationStatus = Field(..., description="Nouveau statut")
    review_notes: str | None = Field(None, description="Notes de révision")
    review_score: Decimal | None = Field(None, ge=0, le=100, description="Score")
    reviewer_external_id: str | None = Field(None, description="ID du réviseur")


class ApplicationRead(ApplicationBase):
    """Schéma pour la lecture d'une candidature."""

    id: str
    reference_number: str
    user_external_id: str | None
    reviewer_external_id: str | None
    status: SubmittedApplicationStatus
    submitted_at: datetime
    reviewed_at: datetime | None
    review_notes: str | None
    review_score: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationWithDetails(ApplicationRead):
    """Schéma pour une candidature avec tous ses détails."""

    degrees: list[ApplicationDegreeRead] = []
    documents: list[ApplicationDocumentRead] = []


class ApplicationListItem(BaseModel):
    """Schéma pour la liste des candidatures."""

    id: str
    reference_number: str
    call_id: str | None
    last_name: str
    first_name: str
    email: str
    status: SubmittedApplicationStatus
    submitted_at: datetime
    review_score: Decimal | None

    model_config = {"from_attributes": True}


class ApplicationStatistics(BaseModel):
    """Statistiques des candidatures."""

    total: int = 0
    submitted: int = 0
    under_review: int = 0
    accepted: int = 0
    rejected: int = 0
    waitlisted: int = 0
    incomplete: int = 0


# =============================================================================
# STATISTIQUES ÉTENDUES
# =============================================================================


class TimelineDataPoint(BaseModel):
    """Point de données pour l'évolution temporelle."""

    period: str  # Format "YYYY-MM" ou "YYYY-MM-DD"
    count: int


class ProgramStatistics(BaseModel):
    """Statistiques par programme/appel."""

    program_id: str
    program_title: str
    total: int
    accepted: int
    acceptance_rate: float


class CallStatistics(BaseModel):
    """Statistiques détaillées par appel."""

    call_id: str
    call_title: str
    total: int
    submitted: int
    under_review: int
    accepted: int
    rejected: int
    waitlisted: int
    incomplete: int


class ExtendedApplicationStatistics(BaseModel):
    """Statistiques étendues des candidatures."""

    # KPIs
    total: int
    pending: int  # submitted + under_review
    acceptance_rate: float  # accepted / (accepted + rejected + waitlisted) * 100
    completion_rate: float  # (total - incomplete) / total * 100

    # Par statut
    by_status: dict[str, int]

    # Détails
    timeline: list[TimelineDataPoint]
    by_program: list[ProgramStatistics]
    by_call: list[CallStatistics]
