"""
Schémas Editorial
=================

Schémas Pydantic pour la gestion des contenus éditoriaux.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.editorial import EditorialValueType


# =============================================================================
# CATEGORIES
# =============================================================================


class CategoryBase(BaseModel):
    """Schéma de base pour les catégories."""

    code: str = Field(..., min_length=1, max_length=50, description="Code unique")
    name: str = Field(..., min_length=1, max_length=100, description="Nom de la catégorie")
    description: str | None = Field(None, description="Description")


class CategoryCreate(CategoryBase):
    """Schéma pour la création d'une catégorie."""

    pass


class CategoryUpdate(BaseModel):
    """Schéma pour la mise à jour d'une catégorie."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None


class CategoryRead(CategoryBase):
    """Schéma pour la lecture d'une catégorie."""

    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryWithContentsCount(CategoryRead):
    """Schéma de catégorie avec le nombre de contenus."""

    contents_count: int = 0


# =============================================================================
# CONTENTS
# =============================================================================


class ContentBase(BaseModel):
    """Schéma de base pour les contenus."""

    key: str = Field(..., min_length=1, max_length=100, description="Clé unique")
    value: str | None = Field(None, description="Valeur")
    value_type: EditorialValueType = Field(
        EditorialValueType.TEXT, description="Type de valeur"
    )
    description: str | None = Field(None, description="Description du contenu")


class ContentCreate(ContentBase):
    """Schéma pour la création d'un contenu."""

    category_id: str | None = Field(None, description="ID de la catégorie")
    year: int | None = Field(None, ge=2000, le=2100, description="Année associée")
    admin_editable: bool = Field(True, description="Modifiable par les admins")


class ContentUpdate(BaseModel):
    """Schéma pour la mise à jour d'un contenu."""

    value: str | None = None
    value_type: EditorialValueType | None = None
    category_id: str | None = None
    year: int | None = Field(None, ge=2000, le=2100)
    description: str | None = None
    admin_editable: bool | None = None


class ContentRead(ContentBase):
    """Schéma pour la lecture d'un contenu."""

    id: str
    category_id: str | None
    year: int | None
    admin_editable: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContentWithCategory(ContentRead):
    """Schéma de contenu avec la catégorie associée."""

    category: CategoryRead | None = None


class ContentPublic(BaseModel):
    """Schéma public pour un contenu (sans infos admin)."""

    key: str
    value: str | None
    value_type: EditorialValueType
    year: int | None

    model_config = {"from_attributes": True}


# =============================================================================
# HISTORY
# =============================================================================


class HistoryRead(BaseModel):
    """Schéma pour la lecture d'un historique de modification."""

    id: str
    content_id: str
    old_value: str | None
    new_value: str | None
    modified_by_external_id: str | None
    modified_at: datetime

    model_config = {"from_attributes": True}


class ContentWithHistory(ContentRead):
    """Schéma de contenu avec son historique."""

    history: list[HistoryRead] = []


# =============================================================================
# BULK OPERATIONS
# =============================================================================


class BulkContentCreate(BaseModel):
    """Schéma pour la création en masse de contenus."""

    contents: list[ContentCreate]


class BulkContentUpdate(BaseModel):
    """Schéma pour la mise à jour en masse de contenus par clé."""

    key: str
    value: str


class BulkUpdateRequest(BaseModel):
    """Schéma pour la mise à jour en masse."""

    updates: list[BulkContentUpdate]


class BulkUpdateResult(BaseModel):
    """Résultat d'une mise à jour en masse."""

    total: int
    updated: int
    errors: int
    not_found: int


# =============================================================================
# SEARCH & FILTERS
# =============================================================================


class ContentFilter(BaseModel):
    """Filtres pour la recherche de contenus."""

    category_id: str | None = None
    category_code: str | None = None
    value_type: EditorialValueType | None = None
    year: int | None = None
    admin_editable: bool | None = None
    search: str | None = None
