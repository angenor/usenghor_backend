"""
Router Admin - Entrepreneuriat (PEI)
====================================

Endpoints d'administration du Pôle Entrepreneuriat et Innovation :
tableau de bord, dispositifs, cohortes et ressources (boîte à outils).

Permissions : ``entrepreneurship.view|create|edit|delete``.
Toutes les écritures sont auditées explicitement par le service.
Routes statiques (``/dashboard``, ``/translate-missing``, ``/reorder``,
``/translate``, ``/categories``) déclarées AVANT les routes ``/{id}``.

Spec : specs/021-pei-entrepreneurship-core/contracts/admin-api.md
"""

import ipaddress

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.models.entrepreneurship import PeiCohortType, PeiProgramPhase, PeiResourceType
from app.schemas.entrepreneurship import (
    ActiveRequest,
    ActiveStatus,
    PeiCohortAdmin,
    PeiCohortCreate,
    PeiCohortsAdminPage,
    PeiCohortTranslateRequest,
    PeiCohortTranslateResponse,
    PeiCohortUpdate,
    PeiDashboardStats,
    PeiProgramAdmin,
    PeiProgramCreate,
    PeiProgramsAdminPage,
    PeiProgramTranslateRequest,
    PeiProgramTranslateResponse,
    PeiProgramUpdate,
    PeiResourceAdmin,
    PeiResourceCreate,
    PeiResourcesAdminPage,
    PeiResourceTranslateRequest,
    PeiResourceTranslateResponse,
    PeiResourceUpdate,
    PeiTranslateMissingResponse,
    PublishRequest,
    PublishStatus,
    ReorderRequest,
    ReorderResponse,
)
from app.services.entrepreneurship_service import EntrepreneurshipService

router = APIRouter(prefix="/entrepreneurship", tags=["Entrepreneurship Admin"])

VIEW = "entrepreneurship.view"
CREATE = "entrepreneurship.create"
EDIT = "entrepreneurship.edit"
DELETE = "entrepreneurship.delete"


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    """IP (``x-forwarded-for`` sinon ``request.client.host``) et user-agent."""
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else None
    if not ip and request.client:
        ip = request.client.host
    # La colonne audit_logs.ip_address est de type INET : on écarte les valeurs invalides.
    if ip:
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            ip = None
    return ip, request.headers.get("user-agent")


# ===========================================================================
# Transversal
# ===========================================================================


@router.get("/dashboard", response_model=PeiDashboardStats)
async def get_dashboard(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(VIEW)),
) -> PeiDashboardStats:
    """Compteurs du pôle et service DDE identifié par la clé éditoriale."""
    return await EntrepreneurshipService(db).get_dashboard_stats()


@router.post("/translate-missing", response_model=PeiTranslateMissingResponse)
async def translate_missing(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> PeiTranslateMissingResponse:
    """Complète les champs EN/AR vides des trois tables (rejouable)."""
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).translate_missing(
        user_id=current_user.id, ip_address=ip, user_agent=ua
    )


# ===========================================================================
# Dispositifs
# ===========================================================================


@router.get("/programs", response_model=PeiProgramsAdminPage)
async def list_programs(
    db: DbSession,
    current_user: CurrentUser,
    q: str | None = Query(None, description="Recherche sur le titre FR"),
    phase: PeiProgramPhase | None = Query(None),
    active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    _: bool = Depends(PermissionChecker(VIEW)),
) -> PeiProgramsAdminPage:
    return await EntrepreneurshipService(db).list_programs(
        q=q, phase=phase, active=active, page=page, page_size=page_size
    )


@router.post(
    "/programs", response_model=PeiProgramAdmin, status_code=status.HTTP_201_CREATED
)
async def create_program(
    data: PeiProgramCreate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(CREATE)),
) -> PeiProgramAdmin:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).create_program(
        data, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.patch("/programs/reorder", response_model=ReorderResponse)
async def reorder_programs(
    payload: ReorderRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> ReorderResponse:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).reorder_programs(
        payload.ids, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.post("/programs/translate", response_model=PeiProgramTranslateResponse)
async def translate_program(
    data: PeiProgramTranslateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(VIEW)),
) -> PeiProgramTranslateResponse:
    """Traduit FR → EN/AR sans persistance."""
    return await EntrepreneurshipService(db).translate_program_fields(data)


@router.get("/programs/{program_id}", response_model=PeiProgramAdmin)
async def get_program(
    program_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(VIEW)),
) -> PeiProgramAdmin:
    return await EntrepreneurshipService(db).get_program(program_id)


@router.patch("/programs/{program_id}", response_model=PeiProgramAdmin)
async def update_program(
    program_id: str,
    data: PeiProgramUpdate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> PeiProgramAdmin:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).update_program(
        program_id, data, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.delete("/programs/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(
    program_id: str,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(DELETE)),
) -> None:
    ip, ua = _client_meta(request)
    await EntrepreneurshipService(db).delete_program(
        program_id, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.patch("/programs/{program_id}/active", response_model=ActiveStatus)
async def set_program_active(
    program_id: str,
    payload: ActiveRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> ActiveStatus:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).set_program_active(
        program_id, payload.active, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


# ===========================================================================
# Cohortes
# ===========================================================================


@router.get("/cohorts", response_model=PeiCohortsAdminPage)
async def list_cohorts(
    db: DbSession,
    current_user: CurrentUser,
    q: str | None = Query(None, description="Recherche sur le libellé FR"),
    type: PeiCohortType | None = Query(None),  # noqa: A002
    active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    _: bool = Depends(PermissionChecker(VIEW)),
) -> PeiCohortsAdminPage:
    return await EntrepreneurshipService(db).list_cohorts(
        q=q, type=type, active=active, page=page, page_size=page_size
    )


@router.post(
    "/cohorts", response_model=PeiCohortAdmin, status_code=status.HTTP_201_CREATED
)
async def create_cohort(
    data: PeiCohortCreate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(CREATE)),
) -> PeiCohortAdmin:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).create_cohort(
        data, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.patch("/cohorts/reorder", response_model=ReorderResponse)
async def reorder_cohorts(
    payload: ReorderRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> ReorderResponse:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).reorder_cohorts(
        payload.ids, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.post("/cohorts/translate", response_model=PeiCohortTranslateResponse)
async def translate_cohort(
    data: PeiCohortTranslateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(VIEW)),
) -> PeiCohortTranslateResponse:
    """Traduit FR → EN/AR sans persistance."""
    return await EntrepreneurshipService(db).translate_cohort_fields(data)


@router.get("/cohorts/{cohort_id}", response_model=PeiCohortAdmin)
async def get_cohort(
    cohort_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(VIEW)),
) -> PeiCohortAdmin:
    return await EntrepreneurshipService(db).get_cohort(cohort_id)


@router.patch("/cohorts/{cohort_id}", response_model=PeiCohortAdmin)
async def update_cohort(
    cohort_id: str,
    data: PeiCohortUpdate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> PeiCohortAdmin:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).update_cohort(
        cohort_id, data, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.delete("/cohorts/{cohort_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cohort(
    cohort_id: str,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(DELETE)),
) -> None:
    """Supprime une cohorte (409 réservé à la feature 022 : lauréats rattachés)."""
    ip, ua = _client_meta(request)
    await EntrepreneurshipService(db).delete_cohort(
        cohort_id, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.patch("/cohorts/{cohort_id}/active", response_model=ActiveStatus)
async def set_cohort_active(
    cohort_id: str,
    payload: ActiveRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> ActiveStatus:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).set_cohort_active(
        cohort_id, payload.active, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


# ===========================================================================
# Ressources (boîte à outils)
# ===========================================================================


@router.get("/resources", response_model=PeiResourcesAdminPage)
async def list_resources(
    db: DbSession,
    current_user: CurrentUser,
    q: str | None = Query(None, description="Recherche sur le titre FR"),
    type: PeiResourceType | None = Query(None),  # noqa: A002
    category: str | None = Query(None, description="Catégorie FR exacte"),
    is_published: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    _: bool = Depends(PermissionChecker(VIEW)),
) -> PeiResourcesAdminPage:
    return await EntrepreneurshipService(db).list_resources(
        q=q,
        type=type,
        category=category,
        is_published=is_published,
        page=page,
        page_size=page_size,
    )


@router.get("/resources/categories", response_model=list[str])
async def list_resource_categories(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(VIEW)),
) -> list[str]:
    """Catégories FR distinctes (pour les filtres et l'autocomplétion)."""
    return await EntrepreneurshipService(db).list_resource_categories()


@router.post(
    "/resources", response_model=PeiResourceAdmin, status_code=status.HTTP_201_CREATED
)
async def create_resource(
    data: PeiResourceCreate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(CREATE)),
) -> PeiResourceAdmin:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).create_resource(
        data, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.patch("/resources/reorder", response_model=ReorderResponse)
async def reorder_resources(
    payload: ReorderRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> ReorderResponse:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).reorder_resources(
        payload.ids, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.post("/resources/translate", response_model=PeiResourceTranslateResponse)
async def translate_resource(
    data: PeiResourceTranslateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(VIEW)),
) -> PeiResourceTranslateResponse:
    """Traduit FR → EN/AR sans persistance."""
    return await EntrepreneurshipService(db).translate_resource_fields(data)


@router.get("/resources/{resource_id}", response_model=PeiResourceAdmin)
async def get_resource(
    resource_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(VIEW)),
) -> PeiResourceAdmin:
    return await EntrepreneurshipService(db).get_resource(resource_id)


@router.patch("/resources/{resource_id}", response_model=PeiResourceAdmin)
async def update_resource(
    resource_id: str,
    data: PeiResourceUpdate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> PeiResourceAdmin:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).update_resource(
        resource_id, data, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: str,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(DELETE)),
) -> None:
    ip, ua = _client_meta(request)
    await EntrepreneurshipService(db).delete_resource(
        resource_id, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.patch("/resources/{resource_id}/publish", response_model=PublishStatus)
async def set_resource_published(
    resource_id: str,
    payload: PublishRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> PublishStatus:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).set_resource_published(
        resource_id,
        payload.is_published,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )
