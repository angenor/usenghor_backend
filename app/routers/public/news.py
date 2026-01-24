"""
Router Public - Actualités
==========================

Endpoints publics pour les actualités.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.base import PublicationStatus
from app.models.content import News
from app.schemas.content import NewsPublic, NewsWithTags
from app.services.content_service import ContentService

router = APIRouter(prefix="/news", tags=["News"])


@router.get("", response_model=dict)
async def list_news(
    db: DbSession,
    pagination: PaginationParams = Depends(),
    tag_id: str | None = Query(None, description="Filtrer par tag"),
    campus_id: str | None = Query(None, description="Filtrer par campus"),
) -> dict:
    """Liste les actualités publiées."""
    service = ContentService(db)
    query = await service.get_news(
        status=PublicationStatus.PUBLISHED,
        tag_id=tag_id,
        campus_id=campus_id,
    )
    return await paginate(db, query, pagination, News)


@router.get("/{slug}", response_model=NewsWithTags)
async def get_news_by_slug(
    slug: str,
    db: DbSession,
) -> News:
    """Récupère une actualité publiée par son slug."""
    service = ContentService(db)
    news = await service.get_news_by_slug(slug)
    if not news or news.status != PublicationStatus.PUBLISHED:
        raise NotFoundException("Actualité non trouvée")

    # Vérifier la date de visibilité
    if news.visible_from and news.visible_from > datetime.now():
        raise NotFoundException("Actualité non trouvée")

    return news
