"""
Router Admin - FAQ
==================

Endpoints CRUD pour les catégories et entrées de la FAQ trilingue.
Toutes les mutations sont auditées via `audit_logs`.
"""

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.schemas.faq import (
    CategoriesReorderRequest,
    EntriesReorderRequest,
    FaqCategoriesAdminList,
    FaqCategoryAdmin,
    FaqCategoryCreate,
    FaqCategoryUpdate,
    FaqEntriesAdminPage,
    FaqEntryAdminFull,
    FaqEntryCreate,
    FaqEntryPublishStatus,
    FaqEntryUpdate,
    PublishRequest,
    ReorderResponse,
)
from app.services.faq_service import FaqService

router = APIRouter(prefix="/faq", tags=["FAQ Admin"])


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua


# ---------------------------------------------------------------------------
# Catégories — routes statiques AVANT les routes dynamiques
# ---------------------------------------------------------------------------


@router.get("/categories", response_model=FaqCategoriesAdminList)
async def list_categories(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("faq.view")),
) -> FaqCategoriesAdminList:
    """Liste toutes les catégories (avec entry_count)."""
    return await FaqService(db).list_categories()


@router.post(
    "/categories",
    response_model=FaqCategoryAdmin,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    data: FaqCategoryCreate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("faq.create")),
) -> FaqCategoryAdmin:
    """Crée une catégorie FAQ."""
    ip, ua = _client_meta(request)
    return await FaqService(db).create_category(
        data, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.patch("/categories/reorder", response_model=ReorderResponse)
async def reorder_categories(
    payload: CategoriesReorderRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("faq.edit")),
) -> ReorderResponse:
    """Réordonne les catégories en lot."""
    ip, ua = _client_meta(request)
    return await FaqService(db).reorder_categories(
        payload, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.patch("/categories/{category_id}", response_model=FaqCategoryAdmin)
async def update_category(
    category_id: str,
    data: FaqCategoryUpdate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("faq.edit")),
) -> FaqCategoryAdmin:
    """Met à jour une catégorie."""
    ip, ua = _client_meta(request)
    return await FaqService(db).update_category(
        category_id, data, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.delete(
    "/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_category(
    category_id: str,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("faq.delete")),
) -> None:
    """Supprime une catégorie (refusée si non vide ou si code='general')."""
    ip, ua = _client_meta(request)
    await FaqService(db).delete_category(
        category_id, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


# ---------------------------------------------------------------------------
# Entrées — routes statiques AVANT les routes dynamiques
# ---------------------------------------------------------------------------


@router.get("/entries", response_model=FaqEntriesAdminPage)
async def list_entries(
    db: DbSession,
    current_user: CurrentUser,
    category_id: str | None = Query(None),
    is_published: bool | None = Query(None),
    q: str | None = Query(None, description="Recherche sur question_fr"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: bool = Depends(PermissionChecker("faq.view")),
) -> FaqEntriesAdminPage:
    """Liste paginée des entrées avec filtres."""
    return await FaqService(db).list_entries(
        category_id=category_id,
        is_published=is_published,
        q=q,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/entries",
    response_model=FaqEntryAdminFull,
    status_code=status.HTTP_201_CREATED,
)
async def create_entry(
    data: FaqEntryCreate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("faq.create")),
) -> FaqEntryAdminFull:
    """Crée une entrée FAQ (statut initial = brouillon)."""
    ip, ua = _client_meta(request)
    return await FaqService(db).create_entry(
        data, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.patch("/entries/reorder", response_model=ReorderResponse)
async def reorder_entries(
    payload: EntriesReorderRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("faq.edit")),
) -> ReorderResponse:
    """Réordonne les entrées au sein d'une catégorie."""
    ip, ua = _client_meta(request)
    return await FaqService(db).reorder_entries(
        payload, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.get("/entries/{entry_id}", response_model=FaqEntryAdminFull)
async def get_entry(
    entry_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("faq.view")),
) -> FaqEntryAdminFull:
    """Récupère une entrée complète."""
    return await FaqService(db).get_entry(entry_id)


@router.patch("/entries/{entry_id}", response_model=FaqEntryAdminFull)
async def update_entry(
    entry_id: str,
    data: FaqEntryUpdate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("faq.edit")),
) -> FaqEntryAdminFull:
    """Met à jour une entrée."""
    ip, ua = _client_meta(request)
    return await FaqService(db).update_entry(
        entry_id, data, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: str,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("faq.delete")),
) -> None:
    """Supprime définitivement une entrée."""
    ip, ua = _client_meta(request)
    await FaqService(db).delete_entry(
        entry_id, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.patch("/entries/{entry_id}/publish", response_model=FaqEntryPublishStatus)
async def set_entry_published(
    entry_id: str,
    payload: PublishRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("faq.edit")),
) -> FaqEntryPublishStatus:
    """Bascule le statut de publication d'une entrée."""
    ip, ua = _client_meta(request)
    return await FaqService(db).set_published(
        entry_id,
        payload.is_published,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )
