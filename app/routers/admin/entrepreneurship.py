"""
Router Admin - Entrepreneuriat (PEI)
====================================

Endpoints d'administration du Pôle Entrepreneuriat et Innovation :
tableau de bord, dispositifs, cohortes, ressources (boîte à outils), portraits
(lauréats / étudiants-entrepreneurs) et partenaires du pôle.

Permissions : ``entrepreneurship.view|create|edit|delete``.
Toutes les écritures sont auditées explicitement par le service.
Routes statiques (``/dashboard``, ``/translate-missing``, ``/reorder``,
``/translate``, ``/categories``, ``/available``) déclarées AVANT les routes ``/{id}``.

Spec : specs/021-pei-entrepreneurship-core/contracts/admin-api.md,
specs/022-pei-laureates-partners/contracts/admin-api.md
"""

import ipaddress

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.models.entrepreneurship import (
    PeiCohortType,
    PeiLaureateType,
    PeiPartnerFamily,
    PeiProgramPhase,
    PeiResourceType,
)
from app.schemas.entrepreneurship import (
    ActiveRequest,
    ActiveStatus,
    FeaturedRequest,
    FeaturedStatus,
    PeiCohortAdmin,
    PeiCohortCreate,
    PeiCohortsAdminPage,
    PeiCohortTranslateRequest,
    PeiCohortTranslateResponse,
    PeiCohortUpdate,
    PeiDashboardStats,
    PeiLaureateAdmin,
    PeiLaureateCreate,
    PeiLaureateReorderRequest,
    PeiLaureatesAdminPage,
    PeiLaureateTranslateRequest,
    PeiLaureateTranslateResponse,
    PeiLaureateUpdate,
    PeiPartnerAvailable,
    PeiPartnerLinkAdmin,
    PeiPartnerLinkCreate,
    PeiPartnerLinkUpdate,
    PeiPartnerReorderRequest,
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
    """Supprime une cohorte (409 si des portraits y sont rattachés)."""
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


# ===========================================================================
# Portraits (lauréats FSE / étudiants-entrepreneurs)
# ===========================================================================


@router.get("/laureates", response_model=PeiLaureatesAdminPage)
async def list_laureates(
    db: DbSession,
    current_user: CurrentUser,
    q: str | None = Query(None, description="Recherche sur le nom ou le projet"),
    cohort_id: str | None = Query(None),
    type: PeiLaureateType | None = Query(None),  # noqa: A002
    is_published: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    _: bool = Depends(PermissionChecker(VIEW)),
) -> PeiLaureatesAdminPage:
    return await EntrepreneurshipService(db).list_laureates(
        q=q,
        cohort_id=cohort_id,
        type=type,
        is_published=is_published,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/laureates", response_model=PeiLaureateAdmin, status_code=status.HTTP_201_CREATED
)
async def create_laureate(
    data: PeiLaureateCreate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(CREATE)),
) -> PeiLaureateAdmin:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).create_laureate(
        data, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.patch("/laureates/reorder", response_model=ReorderResponse)
async def reorder_laureates(
    payload: PeiLaureateReorderRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> ReorderResponse:
    """Réordonne tous les portraits d'une cohorte."""
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).reorder_laureates(
        payload.cohort_id,
        payload.ids,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


@router.post("/laureates/translate", response_model=PeiLaureateTranslateResponse)
async def translate_laureate(
    data: PeiLaureateTranslateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(VIEW)),
) -> PeiLaureateTranslateResponse:
    """Traduit FR → EN/AR sans persistance."""
    return await EntrepreneurshipService(db).translate_laureate_fields(data)


@router.get("/laureates/{laureate_id}", response_model=PeiLaureateAdmin)
async def get_laureate(
    laureate_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(VIEW)),
) -> PeiLaureateAdmin:
    return await EntrepreneurshipService(db).get_laureate(laureate_id)


@router.patch("/laureates/{laureate_id}", response_model=PeiLaureateAdmin)
async def update_laureate(
    laureate_id: str,
    data: PeiLaureateUpdate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> PeiLaureateAdmin:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).update_laureate(
        laureate_id, data, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.delete("/laureates/{laureate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_laureate(
    laureate_id: str,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(DELETE)),
) -> None:
    ip, ua = _client_meta(request)
    await EntrepreneurshipService(db).delete_laureate(
        laureate_id, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.patch("/laureates/{laureate_id}/publish", response_model=PublishStatus)
async def set_laureate_published(
    laureate_id: str,
    payload: PublishRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> PublishStatus:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).set_laureate_published(
        laureate_id,
        payload.is_published,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


@router.patch("/laureates/{laureate_id}/featured", response_model=FeaturedStatus)
async def set_laureate_featured(
    laureate_id: str,
    payload: FeaturedRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> FeaturedStatus:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).set_laureate_featured(
        laureate_id,
        payload.is_featured,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


# ===========================================================================
# Partenaires du pôle (rattachement de partenaires existants)
# ===========================================================================


@router.get("/partners", response_model=list[PeiPartnerLinkAdmin])
async def list_partner_links(
    db: DbSession,
    current_user: CurrentUser,
    family: PeiPartnerFamily | None = Query(None),
    _: bool = Depends(PermissionChecker(VIEW)),
) -> list[PeiPartnerLinkAdmin]:
    return await EntrepreneurshipService(db).list_partner_links(family=family)


@router.post(
    "/partners", response_model=PeiPartnerLinkAdmin, status_code=status.HTTP_201_CREATED
)
async def link_partner(
    data: PeiPartnerLinkCreate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(CREATE)),
) -> PeiPartnerLinkAdmin:
    """Rattache un partenaire existant à une famille du pôle (aucune création)."""
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).link_partner(
        data, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.patch("/partners/reorder", response_model=ReorderResponse)
async def reorder_partner_links(
    payload: PeiPartnerReorderRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> ReorderResponse:
    """Réordonne tous les partenaires d'une famille."""
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).reorder_partner_links(
        payload.family,
        payload.ids,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


@router.get("/partners/available", response_model=list[PeiPartnerAvailable])
async def list_available_partners(
    db: DbSession,
    current_user: CurrentUser,
    q: str | None = Query(None, description="Recherche sur le nom ou la description"),
    limit: int = Query(20, ge=1, le=50),
    _: bool = Depends(PermissionChecker(VIEW)),
) -> list[PeiPartnerAvailable]:
    """Partenaires non rattachés au pôle (actifs d'abord)."""
    return await EntrepreneurshipService(db).list_available_partners(q=q, limit=limit)


@router.patch("/partners/{partner_id}", response_model=PeiPartnerLinkAdmin)
async def update_partner_family(
    partner_id: str,
    data: PeiPartnerLinkUpdate,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(EDIT)),
) -> PeiPartnerLinkAdmin:
    ip, ua = _client_meta(request)
    return await EntrepreneurshipService(db).update_partner_family(
        partner_id, data.family, user_id=current_user.id, ip_address=ip, user_agent=ua
    )


@router.delete("/partners/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_partner(
    partner_id: str,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker(DELETE)),
) -> None:
    """Retire le rattachement ; le partenaire reste dans le backoffice Partenaires."""
    ip, ua = _client_meta(request)
    await EntrepreneurshipService(db).unlink_partner(
        partner_id, user_id=current_user.id, ip_address=ip, user_agent=ua
    )
