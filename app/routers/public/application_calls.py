"""
Router Public - Appels à candidature
====================================

Endpoints publics pour consulter les appels à candidature.
"""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.application import ApplicationCall, CallStatus, CallType
from app.models.base import PublicationStatus
from app.schemas.application import (
    ApplicationCallPublic,
    ApplicationCallPublicWithDetails,
    ApplicationCreate,
)
from app.schemas.common import IdResponse
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/application-calls", tags=["Application Calls"])


@router.get("", response_model=dict)
async def list_calls(
    db: DbSession,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur titre ou description"),
    call_type: CallType | None = Query(None, description="Filtrer par type"),
    call_status: CallStatus | None = Query(None, description="Filtrer par statut"),
    program_id: str | None = Query(None, description="Filtrer par programme"),
) -> dict:
    """Liste les appels à candidature publiés avec pagination et filtres."""
    service = ApplicationService(db)
    query = await service.get_published_calls(
        search=search,
        call_type=call_type,
        call_status=call_status,
        program_id=program_id,
    )
    return await paginate(db, query, pagination, ApplicationCall, ApplicationCallPublic)


@router.get("/ongoing", response_model=list[ApplicationCallPublic])
async def list_ongoing_calls(
    db: DbSession,
    call_type: CallType | None = Query(None, description="Filtrer par type"),
) -> list[ApplicationCall]:
    """Liste les appels à candidature en cours."""
    service = ApplicationService(db)
    query = await service.get_published_calls(
        call_type=call_type,
        call_status=CallStatus.ONGOING,
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/upcoming", response_model=list[ApplicationCallPublic])
async def list_upcoming_calls(
    db: DbSession,
    call_type: CallType | None = Query(None, description="Filtrer par type"),
) -> list[ApplicationCall]:
    """Liste les appels à candidature à venir."""
    service = ApplicationService(db)
    query = await service.get_published_calls(
        call_type=call_type,
        call_status=CallStatus.UPCOMING,
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/by-type/{call_type}", response_model=list[ApplicationCallPublic])
async def list_calls_by_type(
    call_type: CallType,
    db: DbSession,
) -> list[ApplicationCall]:
    """Liste les appels à candidature publiés d'un type donné."""
    service = ApplicationService(db)
    query = await service.get_published_calls(call_type=call_type)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{slug}", response_model=ApplicationCallPublicWithDetails)
async def get_call_by_slug(
    slug: str,
    db: DbSession,
) -> ApplicationCall:
    """Récupère un appel à candidature publié par son slug."""
    service = ApplicationService(db)
    call = await service.get_call_by_slug(slug)
    if not call:
        raise NotFoundException("Appel à candidature non trouvé")

    # Vérifier que l'appel est publié
    if call.publication_status != PublicationStatus.PUBLISHED:
        raise NotFoundException("Appel à candidature non trouvé")

    return call


@router.post("/{slug}/apply", response_model=IdResponse)
async def submit_application(
    slug: str,
    application_data: ApplicationCreate,
    db: DbSession,
) -> IdResponse:
    """
    Soumet une candidature pour un appel à candidature.

    Cette route permet aux candidats de soumettre leur candidature
    via le formulaire interne.
    """
    service = ApplicationService(db)

    # Récupérer l'appel
    call = await service.get_call_by_slug(slug)
    if not call:
        raise NotFoundException("Appel à candidature non trouvé")

    # Vérifier que l'appel est publié et ouvert
    if call.publication_status != PublicationStatus.PUBLISHED:
        raise NotFoundException("Appel à candidature non trouvé")

    if call.status != CallStatus.ONGOING:
        raise NotFoundException("Cet appel n'accepte pas de candidatures actuellement")

    if not call.use_internal_form:
        raise NotFoundException("Cet appel utilise un formulaire externe")

    # Créer la candidature
    data = application_data.model_dump(exclude_unset=True)
    data["call_id"] = call.id
    if call.program_external_id:
        data["program_external_id"] = call.program_external_id

    application = await service.create_application(data)
    return IdResponse(id=application.id, message="Candidature soumise avec succès")
