"""
Router Public - Événements
==========================

Endpoints publics pour les événements.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.base import PublicationStatus
from app.models.content import Event
from app.schemas.content import EventPublic, EventRegistrationCreate, EventRegistrationRead
from app.services.content_service import ContentService

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=dict)
async def list_events(
    db: DbSession,
    pagination: PaginationParams = Depends(),
    from_date: datetime | None = Query(None, description="Date de début"),
    to_date: datetime | None = Query(None, description="Date de fin"),
    campus_id: str | None = Query(None, description="Filtrer par campus"),
    upcoming: bool = Query(False, description="Seulement les événements à venir"),
) -> dict:
    """Liste les événements publiés."""
    service = ContentService(db)

    # Si upcoming, filtrer à partir de maintenant
    if upcoming:
        from_date = datetime.now()

    query = await service.get_events(
        status=PublicationStatus.PUBLISHED,
        from_date=from_date,
        to_date=to_date,
        campus_id=campus_id,
    )
    return await paginate(db, query, pagination, Event, schema_class=EventPublic)


@router.get("/{slug}", response_model=EventPublic)
async def get_event_by_slug(
    slug: str,
    db: DbSession,
) -> Event:
    """Récupère un événement publié par son slug."""
    service = ContentService(db)
    event = await service.get_event_by_slug(slug)
    if not event or event.status != PublicationStatus.PUBLISHED:
        raise NotFoundException("Événement non trouvé")
    return event


@router.post("/{event_id}/register", response_model=EventRegistrationRead)
async def register_to_event(
    event_id: str,
    registration_data: EventRegistrationCreate,
    db: DbSession,
):
    """S'inscrit à un événement."""
    service = ContentService(db)

    # Vérifier que l'événement existe et est publié
    event = await service.get_event_by_id(event_id)
    if not event or event.status != PublicationStatus.PUBLISHED:
        raise NotFoundException("Événement non trouvé")

    if not event.registration_required:
        from app.core.exceptions import ValidationException
        raise ValidationException("Cet événement n'accepte pas les inscriptions")

    return await service.register_to_event(
        event_id=event_id,
        email=registration_data.email,
        last_name=registration_data.last_name,
        first_name=registration_data.first_name,
        phone=registration_data.phone,
        organization=registration_data.organization,
        user_external_id=registration_data.user_external_id,
    )
