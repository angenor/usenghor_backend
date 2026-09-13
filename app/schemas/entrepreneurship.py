"""
Schémas Entrepreneuriat (PEI)
=============================

Schémas Pydantic du Pôle Entrepreneuriat et Innovation (admin + public).

Spec : specs/021-pei-entrepreneurship-core/contracts/admin-api.md et public-api.md,
specs/022-pei-laureates-partners/contracts/ (portraits et partenaires du pôle)
Convention trilingue additive : ``title`` (FR), ``title_en``, ``title_ar`` ;
rich text ``content_html`` / ``content_md`` + ``content_en_html``…
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    HttpUrl,
    TypeAdapter,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)

from app.models.entrepreneurship import (
    PeiCohortType,
    PeiLaureateType,
    PeiPartnerFamily,
    PeiProgramPhase,
    PeiResourceType,
)

__all__ = [
    "PeiProgramPhase",
    "PeiCohortType",
    "PeiResourceType",
    "PeiLaureateType",
    "PeiPartnerFamily",
    "PeiColor",
]

# ---------------------------------------------------------------------------
# Types et validateurs communs
# ---------------------------------------------------------------------------

PeiColor = Literal["blue", "blue_dark", "red", "amber", "teal"]

CODE_PATTERN = r"^[a-z0-9][a-z0-9-]*$"

MSG_DOCUMENT_REQUIRED = "Un document de la médiathèque est requis pour le type document"
MSG_URL_REQUIRED = "Une URL est requise pour le type lien ou vidéo"
MSG_URL_INVALID = "URL invalide : saisissez une adresse complète commençant par http:// ou https://"

_HTTP_URL_ADAPTER = TypeAdapter(HttpUrl)


def _blank_to_none(value):
    """Convertit une chaîne vide (ou composée d'espaces) en ``None``."""
    if isinstance(value, str) and not value.strip():
        return None
    return value


def _check_uuid(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Identifiant de média invalide (UUID attendu)") from exc


def _check_http_url(value: str | None) -> str | None:
    """Valide une URL http(s) via ``HttpUrl`` et renvoie la chaîne saisie."""
    if value is None:
        return None
    value = value.strip()
    if len(value) > 500:
        raise ValueError("URL trop longue (500 caractères maximum)")
    try:
        _HTTP_URL_ADAPTER.validate_python(value)
    except ValidationError as exc:
        raise ValueError(MSG_URL_INVALID) from exc
    return value


MediaUuid = Annotated[
    str | None, BeforeValidator(_blank_to_none), AfterValidator(_check_uuid)
]
HttpUrlStr = Annotated[
    str | None, BeforeValidator(_blank_to_none), AfterValidator(_check_http_url)
]


def _reject_explicit_nulls(model: BaseModel, fields: tuple[str, ...]) -> None:
    """Refuse ``null`` explicite sur les colonnes NOT NULL d'un schéma de mise à jour."""
    for name in fields:
        if name in model.model_fields_set and getattr(model, name) is None:
            raise ValueError(f"Le champ « {name} » ne peut pas être vide")


# ---------------------------------------------------------------------------
# Schémas transverses
# ---------------------------------------------------------------------------


class ReorderRequest(BaseModel):
    """Liste complète des identifiants dans l'ordre voulu."""

    ids: list[str] = Field(..., min_length=1)


class ReorderResponse(BaseModel):
    updated: int


class PeiLaureateReorderRequest(BaseModel):
    """Tous les portraits d'une cohorte, dans l'ordre voulu."""

    cohort_id: str
    ids: list[str] = Field(..., min_length=1)


class PeiPartnerReorderRequest(BaseModel):
    """Tous les partenaires rattachés à une famille, dans l'ordre voulu."""

    family: PeiPartnerFamily
    ids: list[str] = Field(..., min_length=1)


class ActiveRequest(BaseModel):
    active: bool


class ActiveStatus(BaseModel):
    id: str
    active: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublishRequest(BaseModel):
    is_published: bool


class PublishStatus(BaseModel):
    id: str
    is_published: bool
    published_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeaturedRequest(BaseModel):
    is_featured: bool


class FeaturedStatus(BaseModel):
    id: str
    is_featured: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PeiActiveCount(BaseModel):
    active: int
    total: int


class PeiPublishedCount(BaseModel):
    published: int
    total: int


class PeiDdeService(BaseModel):
    id: str | None = None
    name: str | None = None


class PeiDashboardStats(BaseModel):
    programs: PeiActiveCount
    cohorts: PeiActiveCount
    resources: PeiPublishedCount
    dde_service: PeiDdeService
    laureates: PeiPublishedCount
    partners: PeiActiveCount


class PeiTranslateMissingResponse(BaseModel):
    programs: int
    cohorts: int
    resources: int
    laureates: int = 0
    # Faux si le budget de temps est épuisé avant la fin : relancer l'action.
    complete: bool = True


# ---------------------------------------------------------------------------
# Dispositifs (pei_programs)
# ---------------------------------------------------------------------------


class PeiProgramCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=60, pattern=CODE_PATTERN)
    sigle: str | None = Field(None, max_length=30)
    title: str = Field(..., min_length=3, max_length=200)
    title_en: str | None = Field(None, max_length=200)
    title_ar: str | None = Field(None, max_length=200)
    phase: PeiProgramPhase
    tagline: str | None = None
    tagline_en: str | None = None
    tagline_ar: str | None = None
    content_md: str | None = None
    content_html: str | None = None
    content_en_md: str | None = None
    content_en_html: str | None = None
    content_ar_md: str | None = None
    content_ar_html: str | None = None
    highlight: str | None = Field(None, max_length=120)
    highlight_en: str | None = Field(None, max_length=120)
    highlight_ar: str | None = Field(None, max_length=120)
    color: PeiColor = "blue"
    cover_image_external_id: MediaUuid = None
    active: bool = True


class PeiProgramUpdate(BaseModel):
    code: str | None = Field(None, min_length=1, max_length=60, pattern=CODE_PATTERN)
    sigle: str | None = Field(None, max_length=30)
    title: str | None = Field(None, min_length=3, max_length=200)
    title_en: str | None = Field(None, max_length=200)
    title_ar: str | None = Field(None, max_length=200)
    phase: PeiProgramPhase | None = None
    tagline: str | None = None
    tagline_en: str | None = None
    tagline_ar: str | None = None
    content_md: str | None = None
    content_html: str | None = None
    content_en_md: str | None = None
    content_en_html: str | None = None
    content_ar_md: str | None = None
    content_ar_html: str | None = None
    highlight: str | None = Field(None, max_length=120)
    highlight_en: str | None = Field(None, max_length=120)
    highlight_ar: str | None = Field(None, max_length=120)
    color: PeiColor | None = None
    cover_image_external_id: MediaUuid = None
    active: bool | None = None

    @model_validator(mode="after")
    def _no_null_on_required(self):
        _reject_explicit_nulls(self, ("code", "title", "phase", "color", "active"))
        return self


class PeiProgramAdmin(BaseModel):
    id: str
    code: str
    sigle: str | None
    title: str
    title_en: str | None
    title_ar: str | None
    phase: PeiProgramPhase
    tagline: str | None
    tagline_en: str | None
    tagline_ar: str | None
    content_md: str | None
    content_html: str | None
    content_en_md: str | None
    content_en_html: str | None
    content_ar_md: str | None
    content_ar_html: str | None
    highlight: str | None
    highlight_en: str | None
    highlight_ar: str | None
    color: str
    cover_image_external_id: str | None
    cover_image_url: str | None = None
    display_order: int
    active: bool
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    model_config = ConfigDict(from_attributes=True)


class PeiProgramsAdminPage(BaseModel):
    items: list[PeiProgramAdmin]
    total: int
    page: int
    page_size: int


class PeiProgramPublic(BaseModel):
    """Dispositif public : sans ``*_md`` ni UUID de média."""

    id: str
    code: str
    sigle: str | None
    phase: PeiProgramPhase
    title: str
    title_en: str | None
    title_ar: str | None
    tagline: str | None
    tagline_en: str | None
    tagline_ar: str | None
    content_html: str | None
    content_en_html: str | None
    content_ar_html: str | None
    highlight: str | None
    highlight_en: str | None
    highlight_ar: str | None
    color: str
    cover_image_url: str | None = None
    display_order: int

    model_config = ConfigDict(from_attributes=True)


class PeiProgramTranslateRequest(BaseModel):
    title: str | None = None
    tagline: str | None = None
    highlight: str | None = None
    content_md: str | None = None
    content_html: str | None = None


class PeiProgramTranslateResponse(BaseModel):
    title_en: str | None = None
    title_ar: str | None = None
    tagline_en: str | None = None
    tagline_ar: str | None = None
    highlight_en: str | None = None
    highlight_ar: str | None = None
    content_en_md: str | None = None
    content_ar_md: str | None = None
    content_en_html: str | None = None
    content_ar_html: str | None = None


# ---------------------------------------------------------------------------
# Cohortes (pei_cohorts)
# ---------------------------------------------------------------------------


class PeiCohortCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=60, pattern=CODE_PATTERN)
    label: str = Field(..., min_length=1, max_length=200)
    label_en: str | None = Field(None, max_length=200)
    label_ar: str | None = Field(None, max_length=200)
    year: int = Field(..., ge=2000, le=2100)
    type: PeiCohortType
    focus: str | None = None
    focus_en: str | None = None
    focus_ar: str | None = None
    summary_md: str | None = None
    summary_html: str | None = None
    summary_en_md: str | None = None
    summary_en_html: str | None = None
    summary_ar_md: str | None = None
    summary_ar_html: str | None = None
    active: bool = True


class PeiCohortUpdate(BaseModel):
    code: str | None = Field(None, min_length=1, max_length=60, pattern=CODE_PATTERN)
    label: str | None = Field(None, min_length=1, max_length=200)
    label_en: str | None = Field(None, max_length=200)
    label_ar: str | None = Field(None, max_length=200)
    year: int | None = Field(None, ge=2000, le=2100)
    type: PeiCohortType | None = None
    focus: str | None = None
    focus_en: str | None = None
    focus_ar: str | None = None
    summary_md: str | None = None
    summary_html: str | None = None
    summary_en_md: str | None = None
    summary_en_html: str | None = None
    summary_ar_md: str | None = None
    summary_ar_html: str | None = None
    active: bool | None = None

    @model_validator(mode="after")
    def _no_null_on_required(self):
        _reject_explicit_nulls(self, ("code", "label", "year", "type", "active"))
        return self


class PeiCohortAdmin(BaseModel):
    id: str
    code: str
    label: str
    label_en: str | None
    label_ar: str | None
    year: int
    type: PeiCohortType
    focus: str | None
    focus_en: str | None
    focus_ar: str | None
    summary_md: str | None
    summary_html: str | None
    summary_en_md: str | None
    summary_en_html: str | None
    summary_ar_md: str | None
    summary_ar_html: str | None
    display_order: int
    active: bool
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    model_config = ConfigDict(from_attributes=True)


class PeiCohortsAdminPage(BaseModel):
    items: list[PeiCohortAdmin]
    total: int
    page: int
    page_size: int


class PeiCohortPublic(BaseModel):
    """Cohorte publique : sans ``*_md``."""

    id: str
    code: str
    label: str
    label_en: str | None
    label_ar: str | None
    year: int
    type: PeiCohortType
    focus: str | None
    focus_en: str | None
    focus_ar: str | None
    summary_html: str | None
    summary_en_html: str | None
    summary_ar_html: str | None
    display_order: int

    model_config = ConfigDict(from_attributes=True)


class PeiCohortTranslateRequest(BaseModel):
    label: str | None = None
    focus: str | None = None
    summary_md: str | None = None
    summary_html: str | None = None


class PeiCohortTranslateResponse(BaseModel):
    label_en: str | None = None
    label_ar: str | None = None
    focus_en: str | None = None
    focus_ar: str | None = None
    summary_en_md: str | None = None
    summary_ar_md: str | None = None
    summary_en_html: str | None = None
    summary_ar_html: str | None = None


# ---------------------------------------------------------------------------
# Ressources (pei_resources)
# ---------------------------------------------------------------------------


class PeiResourceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    title_en: str | None = Field(None, max_length=200)
    title_ar: str | None = Field(None, max_length=200)
    description: str | None = None
    description_en: str | None = None
    description_ar: str | None = None
    type: PeiResourceType
    media_external_id: MediaUuid = None
    url: HttpUrlStr = None
    category: str | None = Field(None, max_length=120)
    category_en: str | None = Field(None, max_length=120)
    category_ar: str | None = Field(None, max_length=120)
    is_published: bool = False

    @model_validator(mode="after")
    def _check_source(self):
        if self.type == PeiResourceType.DOCUMENT and not self.media_external_id:
            raise ValueError(MSG_DOCUMENT_REQUIRED)
        if self.type in (PeiResourceType.LINK, PeiResourceType.VIDEO) and not self.url:
            raise ValueError(MSG_URL_REQUIRED)
        return self


class PeiResourceUpdate(BaseModel):
    """Tous champs optionnels ; la cohérence type/source est revérifiée par le
    service sur l'objet fusionné."""

    title: str | None = Field(None, min_length=1, max_length=200)
    title_en: str | None = Field(None, max_length=200)
    title_ar: str | None = Field(None, max_length=200)
    description: str | None = None
    description_en: str | None = None
    description_ar: str | None = None
    type: PeiResourceType | None = None
    media_external_id: MediaUuid = None
    url: HttpUrlStr = None
    category: str | None = Field(None, max_length=120)
    category_en: str | None = Field(None, max_length=120)
    category_ar: str | None = Field(None, max_length=120)
    is_published: bool | None = None

    @model_validator(mode="after")
    def _no_null_on_required(self):
        _reject_explicit_nulls(self, ("title", "type", "is_published"))
        return self


class PeiResourceAdmin(BaseModel):
    id: str
    title: str
    title_en: str | None
    title_ar: str | None
    description: str | None
    description_en: str | None
    description_ar: str | None
    type: PeiResourceType
    media_external_id: str | None
    media_url: str | None = None
    url: str | None
    category: str | None
    category_en: str | None
    category_ar: str | None
    display_order: int
    is_published: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    model_config = ConfigDict(from_attributes=True)


class PeiResourcesAdminPage(BaseModel):
    items: list[PeiResourceAdmin]
    total: int
    page: int
    page_size: int


class PeiResourcePublic(BaseModel):
    """Ressource publique : ``media_url`` résolu, sans ``media_external_id``."""

    id: str
    title: str
    title_en: str | None
    title_ar: str | None
    description: str | None
    description_en: str | None
    description_ar: str | None
    type: PeiResourceType
    media_url: str | None = None
    url: str | None
    category: str | None
    category_en: str | None
    category_ar: str | None
    display_order: int

    model_config = ConfigDict(from_attributes=True)


class PeiResourceTranslateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None


class PeiResourceTranslateResponse(BaseModel):
    title_en: str | None = None
    title_ar: str | None = None
    description_en: str | None = None
    description_ar: str | None = None
    category_en: str | None = None
    category_ar: str | None = None


# ---------------------------------------------------------------------------
# Portraits : lauréats FSE et étudiants-entrepreneurs (pei_laureates)
# ---------------------------------------------------------------------------

QUOTE_MAX_LEN = 600
MSG_QUOTE_TOO_LONG = f"Le verbatim ne doit pas dépasser {QUOTE_MAX_LEN} caractères"
_LAUREATE_URL_FIELDS = (
    "website_url",
    "linkedin_url",
    "instagram_url",
    "facebook_url",
    "video_url",
)
_LAUREATE_QUOTE_FIELDS = ("quote", "quote_en", "quote_ar")


class _LaureateValidators(BaseModel):
    """Validateurs partagés par la création et la mise à jour d'un portrait."""

    @field_validator(*_LAUREATE_URL_FIELDS, mode="before", check_fields=False)
    @classmethod
    def _check_urls(cls, value, info: ValidationInfo):
        value = _blank_to_none(value)
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"Adresse web invalide : {info.field_name}")
        try:
            return _check_http_url(value)
        except ValueError as exc:
            raise ValueError(f"Adresse web invalide : {info.field_name}") from exc

    @field_validator(*_LAUREATE_QUOTE_FIELDS, mode="after", check_fields=False)
    @classmethod
    def _check_quote_len(cls, value: str | None):
        if value is not None and len(value) > QUOTE_MAX_LEN:
            raise ValueError(MSG_QUOTE_TOO_LONG)
        return value


class PeiLaureateCreate(_LaureateValidators):
    cohort_id: str
    type: PeiLaureateType
    full_name: str = Field(..., min_length=2, max_length=200)
    project_name: str = Field(..., min_length=2, max_length=200)
    department_label: str | None = Field(None, max_length=200)
    department_label_en: str | None = Field(None, max_length=200)
    department_label_ar: str | None = Field(None, max_length=200)
    quote: str | None = None
    quote_en: str | None = None
    quote_ar: str | None = None
    photo_external_id: MediaUuid = None
    website_url: str | None = None
    linkedin_url: str | None = None
    instagram_url: str | None = None
    facebook_url: str | None = None
    video_url: str | None = None
    grant_amount: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=2)
    is_featured: bool = False
    is_published: bool = False


class PeiLaureateUpdate(_LaureateValidators):
    """Tous champs optionnels ; la cohérence type / cohorte est revérifiée par le
    service sur les valeurs fusionnées."""

    cohort_id: str | None = None
    type: PeiLaureateType | None = None
    full_name: str | None = Field(None, min_length=2, max_length=200)
    project_name: str | None = Field(None, min_length=2, max_length=200)
    department_label: str | None = Field(None, max_length=200)
    department_label_en: str | None = Field(None, max_length=200)
    department_label_ar: str | None = Field(None, max_length=200)
    quote: str | None = None
    quote_en: str | None = None
    quote_ar: str | None = None
    photo_external_id: MediaUuid = None
    website_url: str | None = None
    linkedin_url: str | None = None
    instagram_url: str | None = None
    facebook_url: str | None = None
    video_url: str | None = None
    grant_amount: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=2)
    is_featured: bool | None = None
    is_published: bool | None = None

    @model_validator(mode="after")
    def _no_null_on_required(self):
        _reject_explicit_nulls(
            self,
            ("cohort_id", "type", "full_name", "project_name", "is_featured", "is_published"),
        )
        return self


class PeiLaureateCohortRef(BaseModel):
    id: str
    code: str
    label: str
    type: PeiCohortType
    year: int
    active: bool


class PeiLaureateAdmin(BaseModel):
    id: str
    cohort_id: str
    type: PeiLaureateType
    full_name: str
    project_name: str
    department_label: str | None
    department_label_en: str | None
    department_label_ar: str | None
    quote: str | None
    quote_en: str | None
    quote_ar: str | None
    photo_external_id: str | None
    photo_url: str | None = None
    website_url: str | None
    linkedin_url: str | None
    instagram_url: str | None
    facebook_url: str | None
    video_url: str | None
    # Chaîne décimale (« 5000.00 ») pour éviter toute perte de précision côté client
    grant_amount: str | None
    is_featured: bool
    is_published: bool
    published_at: datetime | None
    display_order: int
    cohort: PeiLaureateCohortRef
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None


class PeiLaureatesAdminPage(BaseModel):
    items: list[PeiLaureateAdmin]
    total: int
    page: int
    page_size: int


class PeiLaureateTranslateRequest(BaseModel):
    department_label: str | None = None
    quote: str | None = None


class PeiLaureateTranslateResponse(BaseModel):
    department_label_en: str | None = None
    department_label_ar: str | None = None
    quote_en: str | None = None
    quote_ar: str | None = None


class PeiLaureatePublic(BaseModel):
    """Portrait public : photo résolue, sans montant individuel ni auteurs."""

    id: str
    type: PeiLaureateType
    full_name: str
    project_name: str
    department_label: str | None
    department_label_en: str | None
    department_label_ar: str | None
    quote: str | None
    quote_en: str | None
    quote_ar: str | None
    photo_url: str | None = None
    website_url: str | None
    linkedin_url: str | None
    instagram_url: str | None
    facebook_url: str | None
    video_url: str | None
    is_featured: bool
    cohort_label: str
    cohort_label_en: str | None
    cohort_label_ar: str | None
    display_order: int


class PeiLaureateGroupPublic(BaseModel):
    cohort: PeiCohortPublic
    laureates: list[PeiLaureatePublic]


class PeiLaureateStatsPublic(BaseModel):
    laureates: int
    cohorts: int
    max_grant_amount: str | None = None


class PeiLaureatesPublic(BaseModel):
    groups: list[PeiLaureateGroupPublic]
    stats: PeiLaureateStatsPublic


# ---------------------------------------------------------------------------
# Partenaires du pôle (pei_partners)
# ---------------------------------------------------------------------------


class PeiPartnerLinkCreate(BaseModel):
    partner_id: str
    family: PeiPartnerFamily


class PeiPartnerLinkUpdate(BaseModel):
    family: PeiPartnerFamily


class PeiPartnerEmbedded(BaseModel):
    id: str
    name: str
    type: str
    active: bool
    website: str | None
    logo_url: str | None = None
    description: str | None


class PeiPartnerLinkAdmin(BaseModel):
    partner_id: str
    family: PeiPartnerFamily
    display_order: int
    created_at: datetime
    updated_at: datetime
    partner: PeiPartnerEmbedded


class PeiPartnerAvailable(BaseModel):
    id: str
    name: str
    type: str
    active: bool
    logo_url: str | None = None


class PeiPartnerPublic(BaseModel):
    """Partenaire public : logo résolu, sans UUID de média ni réseau social."""

    id: str
    name: str
    description: str | None
    description_en: str | None
    description_ar: str | None
    website: str | None
    logo_url: str | None = None
    type: str
    display_order: int


class PeiPartnerFamilyPublic(BaseModel):
    family: PeiPartnerFamily
    partners: list[PeiPartnerPublic]
