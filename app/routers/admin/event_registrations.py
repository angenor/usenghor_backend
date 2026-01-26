"""
Router Admin - Inscriptions événements
======================================

Endpoints pour la gestion des inscriptions aux événements.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.models.content import RegistrationStatus
from app.schemas.common import MessageResponse
from app.schemas.content import (
    EventRegistrationBulkAction,
    EventRegistrationCreate,
    EventRegistrationRead,
    EventRegistrationUpdate,
)
from app.services.content_service import ContentService

router = APIRouter(prefix="/event-registrations", tags=["Event Registrations"])


@router.get("", response_model=list[EventRegistrationRead])
async def list_event_registrations(
    db: DbSession,
    current_user: CurrentUser,
    event_id: str | None = Query(None, description="ID de l'événement (optionnel)"),
    status: RegistrationStatus | None = Query(None, description="Filtrer par statut"),
    _: bool = Depends(PermissionChecker("events.view")),
) -> list:
    """Liste les inscriptions, optionnellement filtrées par événement."""
    service = ContentService(db)
    return await service.get_event_registrations(event_id, status)


@router.get("/{registration_id}", response_model=EventRegistrationRead)
async def get_registration(
    registration_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("events.view")),
):
    """Récupère une inscription par son ID."""
    from sqlalchemy import select
    from app.models.content import EventRegistration

    result = await db.execute(
        select(EventRegistration).where(EventRegistration.id == registration_id)
    )
    registration = result.scalar_one_or_none()
    if not registration:
        raise NotFoundException("Inscription non trouvée")
    return registration


@router.post("", response_model=EventRegistrationRead, status_code=status.HTTP_201_CREATED)
async def create_registration(
    event_id: str,
    registration_data: EventRegistrationCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("events.edit")),
):
    """Crée une inscription à un événement."""
    service = ContentService(db)
    return await service.register_to_event(
        event_id=event_id,
        email=registration_data.email,
        last_name=registration_data.last_name,
        first_name=registration_data.first_name,
        phone=registration_data.phone,
        organization=registration_data.organization,
        user_external_id=registration_data.user_external_id,
    )


@router.put("/{registration_id}", response_model=EventRegistrationRead)
async def update_registration(
    registration_id: str,
    registration_data: EventRegistrationUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("events.edit")),
):
    """Met à jour une inscription."""
    service = ContentService(db)
    update_dict = registration_data.model_dump(exclude_unset=True)
    return await service.update_registration(registration_id, **update_dict)


@router.delete("/{registration_id}", response_model=MessageResponse)
async def delete_registration(
    registration_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("events.edit")),
) -> MessageResponse:
    """Supprime une inscription."""
    service = ContentService(db)
    await service.delete_registration(registration_id)
    return MessageResponse(message="Inscription supprimée avec succès")


@router.post("/{registration_id}/confirm", response_model=EventRegistrationRead)
async def confirm_registration(
    registration_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("events.edit")),
):
    """Confirme une inscription."""
    service = ContentService(db)
    return await service.confirm_registration(registration_id)


@router.post("/{registration_id}/cancel", response_model=EventRegistrationRead)
async def cancel_registration(
    registration_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("events.edit")),
):
    """Annule une inscription."""
    service = ContentService(db)
    return await service.cancel_registration(registration_id)


@router.post("/bulk-action", response_model=MessageResponse)
async def bulk_action_registrations(
    bulk_data: EventRegistrationBulkAction,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("events.edit")),
) -> MessageResponse:
    """Effectue une action en masse sur les inscriptions."""
    service = ContentService(db)
    count = await service.bulk_action_registrations(
        bulk_data.registration_ids, bulk_data.action
    )
    action_fr = "confirmée(s)" if bulk_data.action == "confirm" else "annulée(s)"
    return MessageResponse(message=f"{count} inscription(s) {action_fr}")
