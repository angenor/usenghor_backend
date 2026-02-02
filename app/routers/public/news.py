"""
Router Public - Actualités
==========================

Endpoints publics pour les actualités.
"""

from datetime import datetime
from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams
from app.models.base import PublicationStatus
from app.models.content import News
from app.schemas.content import NewsPublicEnriched, NewsWithTags
from app.services.content_service import ContentService

router = APIRouter(prefix="/news", tags=["News"])


@router.get("", response_model=dict)
async def list_news(
    db: DbSession,
    pagination: PaginationParams = Depends(),
    tag_id: str | None = Query(None, description="Filtrer par tag"),
    campus_id: str | None = Query(None, description="Filtrer par campus"),
    sector_id: str | None = Query(None, description="Filtrer par secteur"),
    service_id: str | None = Query(None, description="Filtrer par service"),
    project_id: str | None = Query(None, description="Filtrer par projet"),
    event_id: str | None = Query(None, description="Filtrer par événement"),
) -> dict:
    """Liste les actualités publiées avec les noms des entités associées résolus."""
    service = ContentService(db)
    query = await service.get_news(
        status=PublicationStatus.PUBLISHED,
        tag_id=tag_id,
        campus_id=campus_id,
        sector_id=sector_id,
        service_id=service_id,
        project_id=project_id,
        event_id=event_id,
    )

    # Compter le total
    count_query = select(func.count()).select_from(News).where(News.status == PublicationStatus.PUBLISHED)
    if tag_id:
        from app.models.content import NewsTag
        count_query = count_query.join(NewsTag).where(NewsTag.tag_id == tag_id)
    if campus_id:
        count_query = count_query.where(News.campus_external_id == campus_id)
    if sector_id:
        count_query = count_query.where(News.sector_external_id == sector_id)
    if service_id:
        count_query = count_query.where(News.service_external_id == service_id)
    if project_id:
        count_query = count_query.where(News.project_external_id == project_id)
    if event_id:
        count_query = count_query.where(News.event_external_id == event_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Appliquer la pagination
    offset = (pagination.page - 1) * pagination.limit
    query = query.offset(offset).limit(pagination.limit)

    # Exécuter la requête
    result = await db.execute(query)
    news_list = result.scalars().all()

    # Enrichir avec les noms des entités associées
    enriched_items = await service.enrich_news_with_names(list(news_list))

    # Valider avec le schéma Pydantic
    items = [NewsPublicEnriched.model_validate(item) for item in enriched_items]

    # Calculer le nombre de pages
    pages = ceil(total / pagination.limit) if pagination.limit > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit,
        "pages": pages,
    }


@router.get("/{slug}", response_model=NewsPublicEnriched)
async def get_news_by_slug(
    slug: str,
    db: DbSession,
) -> NewsPublicEnriched:
    """Récupère une actualité publiée par son slug avec les noms des entités associées."""
    service = ContentService(db)
    news = await service.get_news_by_slug(slug)
    if not news or news.status != PublicationStatus.PUBLISHED:
        raise NotFoundException("Actualité non trouvée")

    # Vérifier la date de visibilité
    if news.visible_from and news.visible_from > datetime.now():
        raise NotFoundException("Actualité non trouvée")

    # Enrichir avec les noms des entités associées
    enriched_list = await service.enrich_news_with_names([news])
    return NewsPublicEnriched.model_validate(enriched_list[0])
