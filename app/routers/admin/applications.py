"""
Router Admin - Candidatures
===========================

Endpoints CRUD pour la gestion des candidatures.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.application import Application, SubmittedApplicationStatus
from app.schemas.application import (
    ApplicationCreate,
    ApplicationDegreeCreate,
    ApplicationDegreeRead,
    ApplicationDegreeUpdate,
    ApplicationDocumentCreate,
    ApplicationDocumentRead,
    ApplicationDocumentUpdate,
    ApplicationListItem,
    ApplicationRead,
    ApplicationStatistics,
    ApplicationStatusUpdate,
    ApplicationUpdate,
    ApplicationWithDetails,
)
from app.schemas.common import IdResponse, MessageResponse
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["Applications"])


# =============================================================================
# APPLICATIONS CRUD
# =============================================================================


@router.get("", response_model=dict)
async def list_applications(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur nom, prénom, email ou référence"),
    call_id: str | None = Query(None, description="Filtrer par appel"),
    status: SubmittedApplicationStatus | None = Query(None, description="Filtrer par statut"),
    program_id: str | None = Query(None, description="Filtrer par programme"),
    _: bool = Depends(PermissionChecker("applications.view")),
) -> dict:
    """Liste les candidatures avec pagination et filtres."""
    service = ApplicationService(db)
    query = await service.get_applications(
        search=search,
        call_id=call_id,
        status=status,
        program_id=program_id,
    )
    return await paginate(db, query, pagination, Application)


@router.get("/statistics", response_model=ApplicationStatistics)
async def get_statistics(
    db: DbSession,
    current_user: CurrentUser,
    call_id: str | None = Query(None, description="Filtrer par appel"),
    _: bool = Depends(PermissionChecker("applications.view")),
) -> ApplicationStatistics:
    """Récupère les statistiques des candidatures."""
    service = ApplicationService(db)
    stats = await service.get_application_statistics(call_id)
    return ApplicationStatistics(**stats)


@router.get("/{application_id}", response_model=ApplicationWithDetails)
async def get_application(
    application_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.view")),
) -> Application:
    """Récupère une candidature par son ID."""
    service = ApplicationService(db)
    application = await service.get_application_by_id(application_id)
    if not application:
        raise NotFoundException("Candidature non trouvée")
    return application


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    application_data: ApplicationCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.create")),
) -> IdResponse:
    """Crée une nouvelle candidature (mode admin)."""
    service = ApplicationService(db)
    data = application_data.model_dump(exclude_unset=True)
    application = await service.create_application(data)
    return IdResponse(id=application.id)


@router.put("/{application_id}", response_model=ApplicationRead)
async def update_application(
    application_id: str,
    application_data: ApplicationUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> Application:
    """Met à jour une candidature."""
    service = ApplicationService(db)
    data = application_data.model_dump(exclude_unset=True)
    return await service.update_application(application_id, data)


@router.delete("/{application_id}", response_model=MessageResponse)
async def delete_application(
    application_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.delete")),
) -> MessageResponse:
    """Supprime une candidature."""
    service = ApplicationService(db)
    await service.delete_application(application_id)
    return MessageResponse(message="Candidature supprimée avec succès")


@router.post("/{application_id}/status", response_model=ApplicationRead)
async def update_status(
    application_id: str,
    status_data: ApplicationStatusUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> Application:
    """Met à jour le statut d'une candidature (évaluation)."""
    service = ApplicationService(db)
    return await service.update_application_status(
        application_id,
        status=status_data.status,
        review_notes=status_data.review_notes,
        review_score=status_data.review_score,
        reviewer_id=status_data.reviewer_external_id or current_user.id,
    )


# =============================================================================
# APPLICATION DEGREES
# =============================================================================


@router.get("/{application_id}/degrees", response_model=list[ApplicationDegreeRead])
async def list_degrees(
    application_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.view")),
) -> list:
    """Liste les diplômes d'une candidature."""
    service = ApplicationService(db)
    application = await service.get_application_by_id(application_id)
    if not application:
        raise NotFoundException("Candidature non trouvée")
    return application.degrees


@router.post(
    "/{application_id}/degrees",
    response_model=ApplicationDegreeRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_degree(
    application_id: str,
    degree_data: ApplicationDegreeCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> ApplicationDegreeRead:
    """Ajoute un diplôme à une candidature."""
    service = ApplicationService(db)
    return await service.add_degree(application_id, degree_data.model_dump())


@router.put("/{application_id}/degrees/{degree_id}", response_model=ApplicationDegreeRead)
async def update_degree(
    application_id: str,
    degree_id: str,
    degree_data: ApplicationDegreeUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> ApplicationDegreeRead:
    """Met à jour un diplôme."""
    service = ApplicationService(db)
    data = degree_data.model_dump(exclude_unset=True)
    return await service.update_degree(degree_id, data)


@router.delete("/{application_id}/degrees/{degree_id}", response_model=MessageResponse)
async def delete_degree(
    application_id: str,
    degree_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> MessageResponse:
    """Supprime un diplôme."""
    service = ApplicationService(db)
    await service.delete_degree(degree_id)
    return MessageResponse(message="Diplôme supprimé avec succès")


# =============================================================================
# APPLICATION DOCUMENTS
# =============================================================================


@router.get("/{application_id}/documents", response_model=list[ApplicationDocumentRead])
async def list_documents(
    application_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.view")),
) -> list:
    """Liste les documents d'une candidature."""
    service = ApplicationService(db)
    application = await service.get_application_by_id(application_id)
    if not application:
        raise NotFoundException("Candidature non trouvée")
    return application.documents


@router.post(
    "/{application_id}/documents",
    response_model=ApplicationDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_document(
    application_id: str,
    document_data: ApplicationDocumentCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> ApplicationDocumentRead:
    """Ajoute un document à une candidature."""
    service = ApplicationService(db)
    return await service.add_document(application_id, document_data.model_dump())


@router.put("/{application_id}/documents/{document_id}", response_model=ApplicationDocumentRead)
async def update_document(
    application_id: str,
    document_id: str,
    document_data: ApplicationDocumentUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> ApplicationDocumentRead:
    """Met à jour un document."""
    service = ApplicationService(db)
    data = document_data.model_dump(exclude_unset=True)
    return await service.update_document(document_id, data)


@router.post("/{application_id}/documents/{document_id}/validate", response_model=ApplicationDocumentRead)
async def validate_document(
    application_id: str,
    document_id: str,
    is_valid: bool = Query(..., description="Document valide ou non"),
    comment: str | None = Query(None, description="Commentaire de validation"),
    db: DbSession = None,
    current_user: CurrentUser = None,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> ApplicationDocumentRead:
    """Valide ou invalide un document."""
    service = ApplicationService(db)
    return await service.validate_document(document_id, is_valid, comment)


@router.delete("/{application_id}/documents/{document_id}", response_model=MessageResponse)
async def delete_document(
    application_id: str,
    document_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("applications.edit")),
) -> MessageResponse:
    """Supprime un document."""
    service = ApplicationService(db)
    await service.delete_document(document_id)
    return MessageResponse(message="Document supprimé avec succès")
