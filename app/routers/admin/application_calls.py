"""
Router Admin - Appels à candidature
===================================

Endpoints CRUD pour la gestion des appels à candidature.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.application import ApplicationCall, CallStatus, CallType
from app.models.base import PublicationStatus
from app.schemas.application import (
    ApplicationCallCreate,
    ApplicationCallRead,
    ApplicationCallUpdate,
    ApplicationCallWithDetails,
    CallCoverageCreate,
    CallCoverageRead,
    CallCoverageUpdate,
    CallEligibilityCriteriaCreate,
    CallEligibilityCriteriaRead,
    CallEligibilityCriteriaUpdate,
    CallRequiredDocumentCreate,
    CallRequiredDocumentRead,
    CallRequiredDocumentUpdate,
    CallScheduleCreate,
    CallScheduleRead,
    CallScheduleUpdate,
)
from app.schemas.common import IdResponse, MessageResponse
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/application-calls", tags=["Application Calls"])


# =============================================================================
# APPLICATION CALLS CRUD
# =============================================================================


@router.get("", response_model=dict)
async def list_calls(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur titre ou description"),
    call_type: CallType | None = Query(None, description="Filtrer par type"),
    call_status: CallStatus | None = Query(None, description="Filtrer par statut"),
    publication_status: PublicationStatus | None = Query(None, description="Filtrer par statut de publication"),
    program_id: str | None = Query(None, description="Filtrer par programme"),
    campus_external_id: str | None = Query(None, description="Filtrer par campus"),
    _: bool = Depends(PermissionChecker("applications.view")),
) -> dict:
    """Liste les appels à candidature avec pagination et filtres."""
    service = ApplicationService(db)
    query = await service.get_calls(
        search=search,
        call_type=call_type,
        call_status=call_status,
        publication_status=publication_status,
        program_id=program_id,
        campus_id=campus_external_id,
    )
    return await paginate(db, query, pagination, ApplicationCall, ApplicationCallRead)


@router.get("/{call_id}", response_model=ApplicationCallWithDetails)
async def get_call(
    call_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.view")),
) -> ApplicationCall:
    """Récupère un appel par son ID."""
    service = ApplicationService(db)
    call = await service.get_call_by_id(call_id)
    if not call:
        raise NotFoundException("Appel non trouvé")
    return call


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_call(
    call_data: ApplicationCallCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.create")),
) -> IdResponse:
    """Crée un nouvel appel à candidature."""
    service = ApplicationService(db)
    data = call_data.model_dump(exclude_unset=True)
    data["created_by_external_id"] = current_user.id
    call = await service.create_call(data)
    return IdResponse(id=call.id, message="Appel créé avec succès")


@router.put("/{call_id}", response_model=ApplicationCallRead)
async def update_call(
    call_id: str,
    call_data: ApplicationCallUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> ApplicationCall:
    """Met à jour un appel à candidature."""
    service = ApplicationService(db)
    data = call_data.model_dump(exclude_unset=True)
    return await service.update_call(call_id, data)


@router.delete("/{call_id}", response_model=MessageResponse)
async def delete_call(
    call_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.delete")),
) -> MessageResponse:
    """Supprime un appel à candidature."""
    service = ApplicationService(db)
    await service.delete_call(call_id)
    return MessageResponse(message="Appel supprimé avec succès")


@router.post("/{call_id}/toggle-publication", response_model=ApplicationCallRead)
async def toggle_publication(
    call_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> ApplicationCall:
    """Bascule le statut de publication d'un appel."""
    service = ApplicationService(db)
    return await service.toggle_call_publication(call_id)


@router.post("/{call_id}/status", response_model=ApplicationCallRead)
async def update_status(
    call_id: str,
    new_status: CallStatus,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> ApplicationCall:
    """Met à jour le statut d'un appel (ongoing, closed, upcoming)."""
    service = ApplicationService(db)
    return await service.update_call_status(call_id, new_status)


# =============================================================================
# ELIGIBILITY CRITERIA
# =============================================================================


@router.get("/{call_id}/criteria", response_model=list[CallEligibilityCriteriaRead])
async def list_criteria(
    call_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.view")),
) -> list:
    """Liste les critères d'éligibilité d'un appel."""
    service = ApplicationService(db)
    call = await service.get_call_by_id(call_id)
    if not call:
        raise NotFoundException("Appel non trouvé")
    return call.eligibility_criteria


@router.post(
    "/{call_id}/criteria",
    response_model=CallEligibilityCriteriaRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_criterion(
    call_id: str,
    criterion_data: CallEligibilityCriteriaCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> CallEligibilityCriteriaRead:
    """Ajoute un critère d'éligibilité à un appel."""
    service = ApplicationService(db)
    return await service.create_criterion(call_id, criterion_data.model_dump())


@router.put("/{call_id}/criteria/{criterion_id}", response_model=CallEligibilityCriteriaRead)
async def update_criterion(
    call_id: str,
    criterion_id: str,
    criterion_data: CallEligibilityCriteriaUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> CallEligibilityCriteriaRead:
    """Met à jour un critère d'éligibilité."""
    service = ApplicationService(db)
    data = criterion_data.model_dump(exclude_unset=True)
    return await service.update_criterion(criterion_id, data)


@router.delete("/{call_id}/criteria/{criterion_id}", response_model=MessageResponse)
async def delete_criterion(
    call_id: str,
    criterion_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> MessageResponse:
    """Supprime un critère d'éligibilité."""
    service = ApplicationService(db)
    await service.delete_criterion(criterion_id)
    return MessageResponse(message="Critère supprimé avec succès")


# =============================================================================
# COVERAGE
# =============================================================================


@router.get("/{call_id}/coverage", response_model=list[CallCoverageRead])
async def list_coverage(
    call_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.view")),
) -> list:
    """Liste les prises en charge d'un appel."""
    service = ApplicationService(db)
    call = await service.get_call_by_id(call_id)
    if not call:
        raise NotFoundException("Appel non trouvé")
    return call.coverage


@router.post(
    "/{call_id}/coverage",
    response_model=CallCoverageRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_coverage(
    call_id: str,
    coverage_data: CallCoverageCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> CallCoverageRead:
    """Ajoute une prise en charge à un appel."""
    service = ApplicationService(db)
    return await service.create_coverage(call_id, coverage_data.model_dump())


@router.put("/{call_id}/coverage/{coverage_id}", response_model=CallCoverageRead)
async def update_coverage(
    call_id: str,
    coverage_id: str,
    coverage_data: CallCoverageUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> CallCoverageRead:
    """Met à jour une prise en charge."""
    service = ApplicationService(db)
    data = coverage_data.model_dump(exclude_unset=True)
    return await service.update_coverage(coverage_id, data)


@router.delete("/{call_id}/coverage/{coverage_id}", response_model=MessageResponse)
async def delete_coverage(
    call_id: str,
    coverage_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> MessageResponse:
    """Supprime une prise en charge."""
    service = ApplicationService(db)
    await service.delete_coverage(coverage_id)
    return MessageResponse(message="Prise en charge supprimée avec succès")


# =============================================================================
# REQUIRED DOCUMENTS
# =============================================================================


@router.get("/{call_id}/required-documents", response_model=list[CallRequiredDocumentRead])
async def list_required_documents(
    call_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.view")),
) -> list:
    """Liste les documents requis d'un appel."""
    service = ApplicationService(db)
    call = await service.get_call_by_id(call_id)
    if not call:
        raise NotFoundException("Appel non trouvé")
    return call.required_documents


@router.post(
    "/{call_id}/required-documents",
    response_model=CallRequiredDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_required_document(
    call_id: str,
    document_data: CallRequiredDocumentCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> CallRequiredDocumentRead:
    """Ajoute un document requis à un appel."""
    service = ApplicationService(db)
    return await service.create_required_document(call_id, document_data.model_dump())


@router.put("/{call_id}/required-documents/{document_id}", response_model=CallRequiredDocumentRead)
async def update_required_document(
    call_id: str,
    document_id: str,
    document_data: CallRequiredDocumentUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> CallRequiredDocumentRead:
    """Met à jour un document requis."""
    service = ApplicationService(db)
    data = document_data.model_dump(exclude_unset=True)
    return await service.update_required_document(document_id, data)


@router.delete("/{call_id}/required-documents/{document_id}", response_model=MessageResponse)
async def delete_required_document(
    call_id: str,
    document_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> MessageResponse:
    """Supprime un document requis."""
    service = ApplicationService(db)
    await service.delete_required_document(document_id)
    return MessageResponse(message="Document requis supprimé avec succès")


# =============================================================================
# SCHEDULE
# =============================================================================


@router.get("/{call_id}/schedule", response_model=list[CallScheduleRead])
async def list_schedule(
    call_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.view")),
) -> list:
    """Liste le calendrier d'un appel."""
    service = ApplicationService(db)
    call = await service.get_call_by_id(call_id)
    if not call:
        raise NotFoundException("Appel non trouvé")
    return call.schedule


@router.post(
    "/{call_id}/schedule",
    response_model=CallScheduleRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_schedule(
    call_id: str,
    schedule_data: CallScheduleCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> CallScheduleRead:
    """Ajoute une étape au calendrier d'un appel."""
    service = ApplicationService(db)
    return await service.create_schedule(call_id, schedule_data.model_dump())


@router.put("/{call_id}/schedule/{schedule_id}", response_model=CallScheduleRead)
async def update_schedule(
    call_id: str,
    schedule_id: str,
    schedule_data: CallScheduleUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> CallScheduleRead:
    """Met à jour une étape du calendrier."""
    service = ApplicationService(db)
    data = schedule_data.model_dump(exclude_unset=True)
    return await service.update_schedule(schedule_id, data)


@router.delete("/{call_id}/schedule/{schedule_id}", response_model=MessageResponse)
async def delete_schedule(
    call_id: str,
    schedule_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> MessageResponse:
    """Supprime une étape du calendrier."""
    service = ApplicationService(db)
    await service.delete_schedule(schedule_id)
    return MessageResponse(message="Étape supprimée avec succès")


# =============================================================================
# MEDIA LIBRARY
# =============================================================================


@router.get("/{call_id}/media-library", response_model=list[str])
async def get_call_media_library(
    call_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.view")),
) -> list[str]:
    """Récupère les IDs des albums associés à un appel."""
    service = ApplicationService(db)
    return await service.get_call_albums(call_id)


@router.post(
    "/{call_id}/media-library",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_album_to_call(
    call_id: str,
    album_external_id: str = Query(..., description="ID de l'album à associer"),
    db: DbSession = None,
    current_user: CurrentUser = None,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> MessageResponse:
    """Associe un album à un appel."""
    service = ApplicationService(db)
    await service.add_album_to_call(call_id, album_external_id)
    return MessageResponse(message="Album associé avec succès")


@router.delete("/{call_id}/media-library/{album_id}", response_model=MessageResponse)
async def remove_album_from_call(
    call_id: str,
    album_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> MessageResponse:
    """Supprime l'association d'un album à un appel."""
    service = ApplicationService(db)
    await service.remove_album_from_call(call_id, album_id)
    return MessageResponse(message="Album dissocié avec succès")
