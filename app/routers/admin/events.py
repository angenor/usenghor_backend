"""
Router Admin - Événements
=========================

Endpoints CRUD pour la gestion des événements.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.base import PublicationStatus
from app.models.content import Event, EventType
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.content import (
    EventCreate,
    EventRead,
    EventUpdate,
    EventWithRegistrations,
)
from app.services.content_service import ContentService

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=dict)
async def list_events(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur titre ou description"),
    status: PublicationStatus | None = Query(None, description="Filtrer par statut"),
    event_type: EventType | None = Query(None, description="Filtrer par type"),
    from_date: datetime | None = Query(None, description="Date de début"),
    to_date: datetime | None = Query(None, description="Date de fin"),
    campus_id: str | None = Query(None, description="Filtrer par campus"),
    _: bool = Depends(PermissionChecker("events.view")),
) -> dict:
    """Liste les événements avec pagination et filtres."""
    service = ContentService(db)
    query = await service.get_events(
        search=search,
        status=status,
        event_type=event_type.value if event_type else None,
        from_date=from_date,
        to_date=to_date,
        campus_id=campus_id,
    )
    return await paginate(db, query, pagination, Event, schema_class=EventRead)


@router.get("/{event_id}", response_model=EventWithRegistrations)
async def get_event(
    event_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("events.view")),
) -> dict:
    """Récupère un événement par son ID."""
    service = ContentService(db)
    event = await service.get_event_by_id(event_id)
    if not event:
        raise NotFoundException("Événement non trouvé")

    # Calculer le nombre d'inscriptions
    registrations_count = len(event.registrations) if event.registrations else 0

    return {
        **event.__dict__,
        "registrations": event.registrations,
        "registrations_count": registrations_count,
    }


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("events.create")),
) -> IdResponse:
    """Crée un nouvel événement."""
    service = ContentService(db)
    event = await service.create_event(
        title=event_data.title,
        slug=event_data.slug,
        description=event_data.description,
        content=event_data.content,
        type=event_data.type,
        type_other=event_data.type_other,
        start_date=event_data.start_date,
        end_date=event_data.end_date,
        venue=event_data.venue,
        address=event_data.address,
        city=event_data.city,
        latitude=event_data.latitude,
        longitude=event_data.longitude,
        is_online=event_data.is_online,
        video_conference_link=event_data.video_conference_link,
        registration_required=event_data.registration_required,
        registration_link=event_data.registration_link,
        max_attendees=event_data.max_attendees,
        cover_image_external_id=event_data.cover_image_external_id,
        country_external_id=event_data.country_external_id,
        campus_external_id=event_data.campus_external_id,
        sector_external_id=event_data.sector_external_id,
        project_external_id=event_data.project_external_id,
        organizer_external_id=event_data.organizer_external_id,
        album_external_id=event_data.album_external_id,
        status=event_data.status,
    )
    return IdResponse(id=event.id, message="Événement créé avec succès")


@router.put("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: str,
    event_data: EventUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("events.edit")),
) -> Event:
    """Met à jour un événement."""
    service = ContentService(db)
    update_dict = event_data.model_dump(exclude_unset=True)
    return await service.update_event(event_id, **update_dict)


@router.delete("/{event_id}", response_model=MessageResponse)
async def delete_event(
    event_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("events.delete")),
) -> MessageResponse:
    """Supprime un événement."""
    service = ContentService(db)
    await service.delete_event(event_id)
    return MessageResponse(message="Événement supprimé avec succès")


@router.post("/{event_id}/publish", response_model=EventRead)
async def publish_event(
    event_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("events.edit")),
) -> Event:
    """Publie un événement."""
    service = ContentService(db)
    return await service.publish_event(event_id)


@router.post("/{event_id}/cancel", response_model=EventRead)
async def cancel_event(
    event_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("events.edit")),
) -> Event:
    """Annule un événement."""
    service = ContentService(db)
    return await service.cancel_event(event_id)


@router.post("/{event_id}/duplicate", response_model=IdResponse)
async def duplicate_event(
    event_id: str,
    new_slug: str = Query(..., description="Nouveau slug"),
    db: DbSession = None,
    current_user: CurrentUser = None,
    _: bool = Depends(PermissionChecker("events.create")),
) -> IdResponse:
    """Duplique un événement."""
    service = ContentService(db)
    event = await service.duplicate_event(event_id, new_slug)
    return IdResponse(id=event.id, message="Événement dupliqué avec succès")
