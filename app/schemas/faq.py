"""
Schémas FAQ
===========

Schémas Pydantic pour la FAQ trilingue (admin + public).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Catégories
# ---------------------------------------------------------------------------


class FaqCategoryBase(BaseModel):
    label_fr: str = Field(..., min_length=1, max_length=120)
    label_en: str | None = Field(None, max_length=120)
    label_ar: str | None = Field(None, max_length=120)
    description_fr: str | None = None
    description_en: str | None = None
    description_ar: str | None = None
    is_active: bool = True


class FaqCategoryCreate(FaqCategoryBase):
    code: str = Field(..., min_length=1, max_length=60, pattern=r"^[a-z0-9_-]+$")


class FaqCategoryUpdate(BaseModel):
    label_fr: str | None = Field(None, min_length=1, max_length=120)
    label_en: str | None = Field(None, max_length=120)
    label_ar: str | None = Field(None, max_length=120)
    description_fr: str | None = None
    description_en: str | None = None
    description_ar: str | None = None
    is_active: bool | None = None


class FaqCategoryAdmin(BaseModel):
    """Catégorie admin avec compteur d'entrées."""

    id: str
    code: str
    label_fr: str
    label_en: str | None
    label_ar: str | None
    description_fr: str | None
    description_en: str | None
    description_ar: str | None
    display_order: int
    is_active: bool
    entry_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FaqCategoriesAdminList(BaseModel):
    categories: list[FaqCategoryAdmin]


# ---------------------------------------------------------------------------
# Entrées
# ---------------------------------------------------------------------------


class FaqEntryBase(BaseModel):
    category_id: str
    question_fr: str = Field(..., min_length=3, max_length=300)
    question_en: str | None = Field(None, max_length=300)
    question_ar: str | None = Field(None, max_length=300)
    answer_fr_md: str = Field(..., min_length=1)
    answer_fr_html: str = Field(..., min_length=1)
    answer_en_md: str | None = None
    answer_en_html: str | None = None
    answer_ar_md: str | None = None
    answer_ar_html: str | None = None


class FaqEntryCreate(FaqEntryBase):
    slug: str | None = Field(
        None, max_length=160, pattern=r"^[a-z0-9][a-z0-9-]*$"
    )


class FaqEntryUpdate(BaseModel):
    category_id: str | None = None
    slug: str | None = Field(
        None, max_length=160, pattern=r"^[a-z0-9][a-z0-9-]*$"
    )
    question_fr: str | None = Field(None, min_length=3, max_length=300)
    question_en: str | None = Field(None, max_length=300)
    question_ar: str | None = Field(None, max_length=300)
    answer_fr_md: str | None = Field(None, min_length=1)
    answer_fr_html: str | None = Field(None, min_length=1)
    answer_en_md: str | None = None
    answer_en_html: str | None = None
    answer_ar_md: str | None = None
    answer_ar_html: str | None = None


class FaqEntryAdminListItem(BaseModel):
    id: str
    category_id: str
    category_code: str
    slug: str
    question_fr: str
    question_en: str | None
    question_ar: str | None
    is_published: bool
    published_at: datetime | None
    display_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FaqEntryAdminFull(FaqEntryAdminListItem):
    answer_fr_md: str
    answer_fr_html: str
    answer_en_md: str | None
    answer_en_html: str | None
    answer_ar_md: str | None
    answer_ar_html: str | None
    created_by: str | None
    updated_by: str | None


class FaqEntriesAdminPage(BaseModel):
    items: list[FaqEntryAdminListItem]
    total: int
    page: int
    page_size: int


class FaqEntryPublishStatus(BaseModel):
    id: str
    is_published: bool
    published_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Public
# ---------------------------------------------------------------------------


class FaqEntryPublic(BaseModel):
    id: str
    slug: str
    question_fr: str
    question_en: str
    question_ar: str
    answer_fr_html: str
    answer_en_html: str
    answer_ar_html: str
    display_order: int
    published_at: datetime


class FaqCategoryPublic(BaseModel):
    id: str
    code: str
    label_fr: str
    label_en: str
    label_ar: str
    description_fr: str | None
    description_en: str | None
    description_ar: str | None
    display_order: int
    entries: list[FaqEntryPublic]


class FaqTreePublic(BaseModel):
    categories: list[FaqCategoryPublic]


# ---------------------------------------------------------------------------
# Réordonnancement & publication
# ---------------------------------------------------------------------------


class ReorderItem(BaseModel):
    id: str
    display_order: int


class CategoriesReorderRequest(BaseModel):
    items: list[ReorderItem]


class EntriesReorderRequest(BaseModel):
    category_id: str
    items: list[ReorderItem]


class ReorderResponse(BaseModel):
    updated: int


class PublishRequest(BaseModel):
    is_published: bool
