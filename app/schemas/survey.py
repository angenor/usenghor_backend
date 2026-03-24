"""
Schémas Survey
==============

Schémas Pydantic pour les campagnes de sondage.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.base import SurveyCampaignStatus


# =============================================================================
# SURVEY CAMPAIGNS
# =============================================================================


class SurveyCampaignCreate(BaseModel):
    """Création d'une campagne."""

    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title_fr: str = Field(..., min_length=1, max_length=255)
    title_en: str | None = Field(None, max_length=255)
    title_ar: str | None = Field(None, max_length=255)
    description_fr: str | None = None
    description_en: str | None = None
    description_ar: str | None = None
    survey_json: dict = Field(default_factory=dict)
    confirmation_email_enabled: bool = False
    confirmation_email_field: str | None = Field(None, max_length=100)
    closes_at: datetime | None = None


class SurveyCampaignUpdate(BaseModel):
    """Mise à jour d'une campagne (partial update)."""

    slug: str | None = Field(None, min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title_fr: str | None = Field(None, min_length=1, max_length=255)
    title_en: str | None = Field(None, max_length=255)
    title_ar: str | None = Field(None, max_length=255)
    description_fr: str | None = None
    description_en: str | None = None
    description_ar: str | None = None
    survey_json: dict | None = None
    confirmation_email_enabled: bool | None = None
    confirmation_email_field: str | None = None
    closes_at: datetime | None = None


class SurveyCampaignRead(BaseModel):
    """Lecture d'une campagne."""

    id: str
    slug: str
    title_fr: str
    title_en: str | None = None
    title_ar: str | None = None
    description_fr: str | None = None
    description_en: str | None = None
    description_ar: str | None = None
    survey_json: dict
    status: SurveyCampaignStatus
    confirmation_email_enabled: bool
    confirmation_email_field: str | None = None
    closes_at: datetime | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SurveyCampaignReadWithStats(SurveyCampaignRead):
    """Lecture d'une campagne avec statistiques agrégées."""

    response_count: int = 0
    last_response_at: datetime | None = None


class SurveyCampaignPublic(BaseModel):
    """Campagne visible publiquement (pour le rendu du formulaire)."""

    id: str
    slug: str
    title_fr: str
    title_en: str | None = None
    title_ar: str | None = None
    description_fr: str | None = None
    description_en: str | None = None
    description_ar: str | None = None
    survey_json: dict
    status: SurveyCampaignStatus
    confirmation_email_enabled: bool = False
    cover_image_external_id: str | None = None

    model_config = {"from_attributes": True}


class SurveyCampaignListPublic(BaseModel):
    """Campagne en liste publique (sans survey_json)."""

    id: str
    slug: str
    title_fr: str
    title_en: str | None = None
    title_ar: str | None = None
    description_fr: str | None = None
    description_en: str | None = None
    description_ar: str | None = None

    model_config = {"from_attributes": True}


# =============================================================================
# SURVEY RESPONSES
# =============================================================================


class SurveySubmitRequest(BaseModel):
    """Soumission d'une réponse publique."""

    response_data: dict
    honeypot: str = ""


class SurveyResponseRead(BaseModel):
    """Lecture d'une réponse individuelle."""

    id: str
    response_data: dict
    submitted_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# SURVEY STATS
# =============================================================================


class QuestionStats(BaseModel):
    """Statistiques d'une question."""

    name: str
    type: str
    title: str
    stats: dict


class SurveyStatsResponse(BaseModel):
    """Statistiques agrégées d'une campagne."""

    total_responses: int
    first_response_at: datetime | None = None
    last_response_at: datetime | None = None
    questions: list[QuestionStats] = []


# =============================================================================
# SURVEY ASSOCIATIONS
# =============================================================================


class SurveyAssociationCreate(BaseModel):
    """Création d'une association."""

    entity_type: str = Field(..., pattern=r"^(event|application_call|program)$")
    entity_id: str


class SurveyAssociationRead(BaseModel):
    """Lecture d'une association."""

    id: str
    campaign_id: str
    entity_type: str
    entity_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# DUPLICATE
# =============================================================================


class SurveyDuplicateRequest(BaseModel):
    """Duplication d'une campagne."""

    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
