"""
Router Admin - Abonnés Newsletter
==================================

Endpoints CRUD pour la gestion des abonnés à la newsletter.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.newsletter import NewsletterSubscriber
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.newsletter import (
    BulkImportResult,
    BulkSubscriberImport,
    SubscriberCreate,
    SubscriberRead,
    SubscriberUpdate,
)
from app.services.newsletter_service import NewsletterService

router = APIRouter(prefix="/subscribers", tags=["Newsletter Subscribers"])


@router.get("", response_model=dict)
async def list_subscribers(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur email ou nom"),
    active: bool | None = Query(None, description="Filtrer par statut actif"),
    source: str | None = Query(None, description="Filtrer par source"),
    _: bool = Depends(PermissionChecker("newsletter.view")),
) -> dict:
    """Liste les abonnés avec pagination et filtres."""
    service = NewsletterService(db)
    query = await service.get_subscribers(
        search=search,
        active=active,
        source=source,
    )
    return await paginate(db, query, pagination, NewsletterSubscriber)


@router.get("/{subscriber_id}", response_model=SubscriberRead)
async def get_subscriber(
    subscriber_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.view")),
) -> NewsletterSubscriber:
    """Récupère un abonné par son ID."""
    service = NewsletterService(db)
    subscriber = await service.get_subscriber_by_id(subscriber_id)
    if not subscriber:
        raise NotFoundException("Abonné non trouvé")
    return subscriber


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_subscriber(
    data: SubscriberCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.create")),
) -> IdResponse:
    """Crée un nouvel abonné."""
    service = NewsletterService(db)
    subscriber = await service.subscribe(**data.model_dump(exclude_unset=True))
    return IdResponse(id=subscriber.id)


@router.put("/{subscriber_id}", response_model=SubscriberRead)
async def update_subscriber(
    subscriber_id: str,
    data: SubscriberUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.edit")),
) -> NewsletterSubscriber:
    """Met à jour un abonné."""
    service = NewsletterService(db)
    return await service.update_subscriber(
        subscriber_id, **data.model_dump(exclude_unset=True)
    )


@router.delete("/{subscriber_id}", response_model=MessageResponse)
async def delete_subscriber(
    subscriber_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.delete")),
) -> MessageResponse:
    """Supprime définitivement un abonné."""
    service = NewsletterService(db)
    await service.delete_subscriber(subscriber_id)
    return MessageResponse(message="Abonné supprimé avec succès")


@router.post("/{subscriber_id}/unsubscribe", response_model=SubscriberRead)
async def unsubscribe(
    subscriber_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.edit")),
) -> NewsletterSubscriber:
    """Désabonne un abonné (le marque comme inactif)."""
    service = NewsletterService(db)
    return await service.unsubscribe(subscriber_id)


@router.post("/import", response_model=BulkImportResult)
async def import_subscribers(
    data: BulkSubscriberImport,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("newsletter.create")),
) -> BulkImportResult:
    """Importe des abonnés en masse."""
    service = NewsletterService(db)
    result = await service.import_subscribers(
        [s.model_dump() for s in data.subscribers],
        source=data.source,
    )
    return BulkImportResult(**result)
