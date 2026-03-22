"""
Schémas Fundraising (Levées de fonds)
======================================

Schémas Pydantic pour les campagnes, contributeurs,
manifestations d'intérêt, sections éditoriales et médiathèque.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Fundraiser ───────────────────────────────────────────────────────

class FundraiserBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description_html: str | None = None
    description_md: str | None = None
    description_en_html: str | None = None
    description_en_md: str | None = None
    description_ar_html: str | None = None
    description_ar_md: str | None = None
    reason_html: str | None = None
    reason_md: str | None = None
    reason_en_html: str | None = None
    reason_en_md: str | None = None
    reason_ar_html: str | None = None
    reason_ar_md: str | None = None
    cover_image_external_id: str | None = None
    goal_amount: float = Field(..., gt=0)
    status: str = Field("draft", pattern="^(draft|active|completed)$")


class FundraiserCreate(FundraiserBase):
    pass


class FundraiserUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    description_html: str | None = None
    description_md: str | None = None
    description_en_html: str | None = None
    description_en_md: str | None = None
    description_ar_html: str | None = None
    description_ar_md: str | None = None
    reason_html: str | None = None
    reason_md: str | None = None
    reason_en_html: str | None = None
    reason_en_md: str | None = None
    reason_ar_html: str | None = None
    reason_ar_md: str | None = None
    cover_image_external_id: str | None = None
    goal_amount: float | None = Field(None, gt=0)
    status: str | None = Field(None, pattern="^(draft|active|completed)$")


class FundraiserRead(FundraiserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FundraiserPublic(BaseModel):
    """Vue publique d'une campagne (liste)."""

    id: str
    title: str
    slug: str
    cover_image_url: str | None = None
    goal_amount: float
    total_raised: float = 0
    progress_percentage: float = 0
    contributor_count: int = 0
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FundraiserPublicDetail(BaseModel):
    """Vue publique détaillée d'une campagne."""

    id: str
    title: str
    slug: str
    description_html: str | None = None
    description_en_html: str | None = None
    description_ar_html: str | None = None
    reason_html: str | None = None
    reason_en_html: str | None = None
    reason_ar_html: str | None = None
    cover_image_url: str | None = None
    goal_amount: float
    total_raised: float = 0
    progress_percentage: float = 0
    contributor_count: int = 0
    status: str
    contributors: list["ContributorPublic"] = []
    media: list["FundraiserMediaRead"] = []
    news: list["FundraiserNewsPublic"] = []

    model_config = {"from_attributes": True}


# ── Contributor ──────────────────────────────────────────────────────

class ContributorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    name_en: str | None = Field(None, max_length=255)
    name_ar: str | None = Field(None, max_length=255)
    category: str = Field(..., pattern="^(state_organization|foundation_philanthropist|company)$")
    amount: float = Field(0, ge=0)
    show_amount_publicly: bool = False
    logo_external_id: str | None = None
    display_order: int = Field(0, ge=0)


class ContributorCreate(ContributorBase):
    pass


class ContributorUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    name_en: str | None = Field(None, max_length=255)
    name_ar: str | None = Field(None, max_length=255)
    category: str | None = Field(None, pattern="^(state_organization|foundation_philanthropist|company)$")
    amount: float | None = Field(None, ge=0)
    show_amount_publicly: bool | None = None
    logo_external_id: str | None = None
    display_order: int | None = Field(None, ge=0)


class ContributorRead(ContributorBase):
    id: str
    fundraiser_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContributorPublic(BaseModel):
    """Vue publique d'un contributeur. amount est None si non consenti."""

    id: str
    name: str
    name_en: str | None = None
    name_ar: str | None = None
    category: str
    amount: float | None = None
    logo_url: str | None = None
    display_order: int = 0

    model_config = {"from_attributes": True}


# ── All Contributors (agrégation globale) ────────────────────────────

class AllContributorsItem(BaseModel):
    """Contributeur agrégé toutes campagnes confondues."""

    name: str
    category: str
    total_amount: float | None = None
    show_amount_publicly: bool = False
    logo_url: str | None = None
    campaigns_count: int = 0

    model_config = {"from_attributes": True}


# ── Interest Expression ──────────────────────────────────────────────

class InterestExpressionCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    message: str | None = Field(None, max_length=2000)
    honeypot: str = ""
    challenge_token: str = ""
    form_opened_at: int = 0


class InterestExpressionRead(BaseModel):
    id: str
    fundraiser_id: str
    fundraiser_title: str | None = None
    full_name: str
    email: str
    message: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InterestExpressionStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(new|contacted)$")


# ── Editorial Section ────────────────────────────────────────────────

class EditorialItemBase(BaseModel):
    icon: str = Field(..., min_length=1, max_length=100)
    title_fr: str = Field(..., min_length=1, max_length=255)
    title_en: str | None = Field(None, max_length=255)
    title_ar: str | None = Field(None, max_length=255)
    description_fr: str = Field(..., min_length=1)
    description_en: str | None = None
    description_ar: str | None = None
    display_order: int = Field(0, ge=0)
    is_active: bool = True


class EditorialItemCreate(EditorialItemBase):
    pass


class EditorialItemUpdate(BaseModel):
    icon: str | None = Field(None, min_length=1, max_length=100)
    title_fr: str | None = Field(None, min_length=1, max_length=255)
    title_en: str | None = Field(None, max_length=255)
    title_ar: str | None = Field(None, max_length=255)
    description_fr: str | None = None
    description_en: str | None = None
    description_ar: str | None = None
    display_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class EditorialItemRead(EditorialItemBase):
    id: str
    section_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EditorialItemPublic(BaseModel):
    """Item éditorial dans la langue demandée."""

    icon: str
    title: str
    description: str

    model_config = {"from_attributes": True}


class EditorialSectionUpdate(BaseModel):
    title_fr: str | None = Field(None, min_length=1, max_length=255)
    title_en: str | None = Field(None, max_length=255)
    title_ar: str | None = Field(None, max_length=255)
    display_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class EditorialSectionRead(BaseModel):
    id: str
    slug: str
    title_fr: str
    title_en: str | None = None
    title_ar: str | None = None
    display_order: int
    is_active: bool
    items: list[EditorialItemRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EditorialSectionPublic(BaseModel):
    """Section éditoriale dans la langue demandée."""

    slug: str
    title: str
    items: list[EditorialItemPublic] = []

    model_config = {"from_attributes": True}


# ── Fundraiser Media ─────────────────────────────────────────────────

class FundraiserMediaCreate(BaseModel):
    media_external_id: str
    caption_fr: str | None = Field(None, max_length=500)
    caption_en: str | None = Field(None, max_length=500)
    caption_ar: str | None = Field(None, max_length=500)
    display_order: int = Field(0, ge=0)


class FundraiserMediaUpdate(BaseModel):
    caption_fr: str | None = Field(None, max_length=500)
    caption_en: str | None = Field(None, max_length=500)
    caption_ar: str | None = Field(None, max_length=500)
    display_order: int | None = Field(None, ge=0)


class FundraiserMediaRead(BaseModel):
    id: str
    fundraiser_id: str
    media_external_id: str
    media_url: str | None = None
    caption_fr: str | None = None
    caption_en: str | None = None
    caption_ar: str | None = None
    display_order: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Fundraiser News (public) ─────────────────────────────────────────

class FundraiserNewsPublic(BaseModel):
    """Actualité associée à une campagne (vue publique)."""

    id: str
    title: str
    slug: str
    cover_image_url: str | None = None
    published_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Global Stats ─────────────────────────────────────────────────────

class GlobalStats(BaseModel):
    """Statistiques agrégées pour la page principale."""

    total_raised_all_campaigns: float = 0
    total_contributors: int = 0
    active_campaigns_count: int = 0
    completed_campaigns_count: int = 0


class FundraiserStatistics(BaseModel):
    """Statistiques pour le dashboard admin."""

    total_campaigns: int = 0
    active_campaigns: int = 0
    completed_campaigns: int = 0
    draft_campaigns: int = 0
    total_raised: float = 0
    total_contributors: int = 0
    total_interest_expressions: int = 0
    new_interest_expressions: int = 0
