"""
Router Admin - Actualités
=========================

Endpoints CRUD pour la gestion des actualités.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.base import PublicationStatus
from app.models.content import News, NewsHighlightStatus
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.content import (
    NewsCreate,
    NewsPublish,
    NewsRead,
    NewsUpdate,
    NewsWithTags,
)
from app.services.content_service import ContentService

router = APIRouter(prefix="/news", tags=["News"])


@router.get("", response_model=dict)
async def list_news(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur titre ou résumé"),
    status: PublicationStatus | None = Query(None, description="Filtrer par statut"),
    highlight_status: NewsHighlightStatus | None = Query(
        None, description="Filtrer par mise en avant"
    ),
    tag_id: str | None = Query(None, description="Filtrer par tag"),
    campus_id: str | None = Query(None, description="Filtrer par campus"),
    from_date: datetime | None = Query(None, description="Date de début"),
    to_date: datetime | None = Query(None, description="Date de fin"),
    _: bool = Depends(PermissionChecker("news.view")),
) -> dict:
    """Liste les actualités avec pagination et filtres."""
    service = ContentService(db)
    query = await service.get_news(
        search=search,
        status=status,
        highlight_status=highlight_status.value if highlight_status else None,
        tag_id=tag_id,
        campus_id=campus_id,
        from_date=from_date,
        to_date=to_date,
    )
    return await paginate(db, query, pagination, News, NewsWithTags)


@router.get("/{news_id}", response_model=NewsWithTags)
async def get_news(
    news_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("news.view")),
) -> News:
    """Récupère une actualité par son ID."""
    service = ContentService(db)
    news = await service.get_news_by_id(news_id)
    if not news:
        raise NotFoundException("Actualité non trouvée")
    return news


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_news(
    news_data: NewsCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("news.create")),
) -> IdResponse:
    """Crée une nouvelle actualité."""
    service = ContentService(db)
    news = await service.create_news(
        title=news_data.title,
        slug=news_data.slug,
        summary=news_data.summary,
        content=news_data.content,
        video_url=news_data.video_url,
        highlight_status=news_data.highlight_status,
        cover_image_external_id=news_data.cover_image_external_id,
        campus_external_id=news_data.campus_external_id,
        department_external_id=news_data.department_external_id,
        service_external_id=news_data.service_external_id,
        event_external_id=news_data.event_external_id,
        project_external_id=news_data.project_external_id,
        author_external_id=news_data.author_external_id,
        status=news_data.status,
        published_at=news_data.published_at,
        visible_from=news_data.visible_from,
        tag_ids=news_data.tag_ids,
    )
    return IdResponse(id=news.id, message="Actualité créée avec succès")


@router.put("/{news_id}", response_model=NewsWithTags)
async def update_news(
    news_id: str,
    news_data: NewsUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("news.edit")),
) -> News:
    """Met à jour une actualité."""
    service = ContentService(db)
    update_dict = news_data.model_dump(exclude_unset=True)
    tag_ids = update_dict.pop("tag_ids", None)
    return await service.update_news(news_id, tag_ids=tag_ids, **update_dict)


@router.delete("/{news_id}", response_model=MessageResponse)
async def delete_news(
    news_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("news.delete")),
) -> MessageResponse:
    """Supprime une actualité."""
    service = ContentService(db)
    await service.delete_news(news_id)
    return MessageResponse(message="Actualité supprimée avec succès")


@router.post("/{news_id}/publish", response_model=NewsWithTags)
async def publish_news(
    news_id: str,
    publish_data: NewsPublish,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("news.edit")),
) -> News:
    """Publie une actualité."""
    service = ContentService(db)
    return await service.publish_news(news_id, publish_data.published_at)


@router.post("/{news_id}/unpublish", response_model=NewsWithTags)
async def unpublish_news(
    news_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("news.edit")),
) -> News:
    """Dépublie une actualité."""
    service = ContentService(db)
    return await service.unpublish_news(news_id)


@router.post("/{news_id}/duplicate", response_model=IdResponse)
async def duplicate_news(
    news_id: str,
    new_slug: str = Query(..., description="Nouveau slug"),
    db: DbSession = None,
    current_user: CurrentUser = None,
    _: bool = Depends(PermissionChecker("news.create")),
) -> IdResponse:
    """Duplique une actualité."""
    service = ContentService(db)
    news = await service.duplicate_news(news_id, new_slug)
    return IdResponse(id=news.id, message="Actualité dupliquée avec succès")
