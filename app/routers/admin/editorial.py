"""
Router Admin - Editorial
========================

Endpoints CRUD pour la gestion des contenus éditoriaux.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.editorial import EditorialCategory, EditorialContent, EditorialValueType
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.editorial import (
    BulkUpdateRequest,
    BulkUpdateResult,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    CategoryWithContentsCount,
    ContentCreate,
    ContentRead,
    ContentUpdate,
    ContentWithCategory,
    ContentWithHistory,
    HistoryRead,
)
from app.services.editorial_service import EditorialService

router = APIRouter(prefix="/editorial", tags=["Editorial"])


# =============================================================================
# CATEGORIES
# =============================================================================


@router.get("/categories", response_model=dict)
async def list_categories(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur code ou nom"),
    _: bool = Depends(PermissionChecker("editorial.view")),
) -> dict:
    """Liste les catégories avec pagination et filtres."""
    service = EditorialService(db)
    query = await service.get_categories(search=search)
    return await paginate(db, query, pagination, EditorialCategory)


@router.get("/categories/with-count", response_model=list[CategoryWithContentsCount])
async def list_categories_with_count(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("editorial.view")),
) -> list[CategoryWithContentsCount]:
    """Liste les catégories avec le nombre de contenus."""
    service = EditorialService(db)
    results = await service.get_categories_with_count()
    return [
        CategoryWithContentsCount(
            **CategoryRead.model_validate(r["category"]).model_dump(),
            contents_count=r["contents_count"],
        )
        for r in results
    ]


@router.get("/categories/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("editorial.view")),
) -> EditorialCategory:
    """Récupère une catégorie par son ID."""
    service = EditorialService(db)
    category = await service.get_category_by_id(category_id)
    if not category:
        raise NotFoundException("Catégorie non trouvée")
    return category


@router.post(
    "/categories", response_model=IdResponse, status_code=status.HTTP_201_CREATED
)
async def create_category(
    data: CategoryCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("editorial.create")),
) -> IdResponse:
    """Crée une nouvelle catégorie."""
    service = EditorialService(db)
    category = await service.create_category(**data.model_dump(exclude_unset=True))
    return IdResponse(id=category.id)


@router.put("/categories/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: str,
    data: CategoryUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("editorial.edit")),
) -> EditorialCategory:
    """Met à jour une catégorie."""
    service = EditorialService(db)
    return await service.update_category(
        category_id, **data.model_dump(exclude_unset=True)
    )


@router.delete("/categories/{category_id}", response_model=MessageResponse)
async def delete_category(
    category_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("editorial.delete")),
) -> MessageResponse:
    """Supprime une catégorie."""
    service = EditorialService(db)
    await service.delete_category(category_id)
    return MessageResponse(message="Catégorie supprimée avec succès")


# =============================================================================
# CONTENTS
# =============================================================================


@router.get("/contents", response_model=dict)
async def list_contents(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur clé ou description"),
    category_id: str | None = Query(None, description="Filtrer par catégorie"),
    category_code: str | None = Query(None, description="Filtrer par code catégorie"),
    value_type: EditorialValueType | None = Query(None, description="Filtrer par type"),
    year: int | None = Query(None, description="Filtrer par année"),
    admin_editable: bool | None = Query(None, description="Filtrer par modifiable"),
    _: bool = Depends(PermissionChecker("editorial.view")),
) -> dict:
    """Liste les contenus avec pagination et filtres."""
    service = EditorialService(db)
    query = await service.get_contents(
        search=search,
        category_id=category_id,
        category_code=category_code,
        value_type=value_type,
        year=year,
        admin_editable=admin_editable,
    )
    return await paginate(db, query, pagination, EditorialContent)


@router.get("/contents/{content_id}", response_model=ContentWithCategory)
async def get_content(
    content_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("editorial.view")),
) -> EditorialContent:
    """Récupère un contenu par son ID."""
    service = EditorialService(db)
    content = await service.get_content_by_id(content_id)
    if not content:
        raise NotFoundException("Contenu non trouvé")
    return content


@router.get("/contents/by-key/{key}", response_model=ContentWithCategory)
async def get_content_by_key(
    key: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("editorial.view")),
) -> EditorialContent:
    """Récupère un contenu par sa clé."""
    service = EditorialService(db)
    content = await service.get_content_by_key(key)
    if not content:
        raise NotFoundException("Contenu non trouvé")
    return content


@router.post(
    "/contents", response_model=IdResponse, status_code=status.HTTP_201_CREATED
)
async def create_content(
    data: ContentCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("editorial.create")),
) -> IdResponse:
    """Crée un nouveau contenu."""
    service = EditorialService(db)
    content = await service.create_content(
        **data.model_dump(exclude_unset=True),
        modified_by_external_id=current_user.id,
    )
    return IdResponse(id=content.id)


@router.put("/contents/{content_id}", response_model=ContentRead)
async def update_content(
    content_id: str,
    data: ContentUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("editorial.edit")),
) -> EditorialContent:
    """Met à jour un contenu."""
    service = EditorialService(db)
    return await service.update_content(
        content_id,
        **data.model_dump(exclude_unset=True),
        modified_by_external_id=current_user.id,
    )


@router.delete("/contents/{content_id}", response_model=MessageResponse)
async def delete_content(
    content_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("editorial.delete")),
) -> MessageResponse:
    """Supprime un contenu."""
    service = EditorialService(db)
    await service.delete_content(content_id)
    return MessageResponse(message="Contenu supprimé avec succès")


@router.post("/contents/bulk-update", response_model=BulkUpdateResult)
async def bulk_update_contents(
    data: BulkUpdateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("editorial.edit")),
) -> BulkUpdateResult:
    """Met à jour plusieurs contenus par leurs clés."""
    service = EditorialService(db)
    result = await service.bulk_update_contents(
        [u.model_dump() for u in data.updates],
        modified_by_external_id=current_user.id,
    )
    return BulkUpdateResult(**result)


# =============================================================================
# HISTORY
# =============================================================================


@router.get("/contents/{content_id}/history", response_model=list[HistoryRead])
async def get_content_history(
    content_id: str,
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(50, ge=1, le=100, description="Nombre de résultats"),
    _: bool = Depends(PermissionChecker("editorial.view")),
) -> list[HistoryRead]:
    """Récupère l'historique des modifications d'un contenu."""
    service = EditorialService(db)
    history = await service.get_content_history(content_id, limit=limit)
    return [HistoryRead.model_validate(h) for h in history]


@router.get("/history/recent", response_model=list[HistoryRead])
async def get_recent_history(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(50, ge=1, le=100, description="Nombre de résultats"),
    _: bool = Depends(PermissionChecker("editorial.view")),
) -> list[HistoryRead]:
    """Récupère les modifications récentes de tous les contenus."""
    service = EditorialService(db)
    history = await service.get_recent_history(limit=limit)
    return [HistoryRead.model_validate(h) for h in history]


@router.get("/contents/{content_id}/with-history", response_model=ContentWithHistory)
async def get_content_with_history(
    content_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("editorial.view")),
) -> ContentWithHistory:
    """Récupère un contenu avec son historique complet."""
    service = EditorialService(db)
    content = await service.get_content_by_id(content_id)
    if not content:
        raise NotFoundException("Contenu non trouvé")
    return ContentWithHistory.model_validate(content)
