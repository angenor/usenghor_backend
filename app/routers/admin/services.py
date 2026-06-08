"""
Router Admin - Services
=======================

Endpoints CRUD pour la gestion des services de secteur.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.organization import Service
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.organization import (
    ServiceAchievementCreate,
    ServiceAchievementRead,
    ServiceAchievementTranslateRequest,
    ServiceAchievementTranslateResponse,
    ServiceAchievementUpdate,
    ServiceCreate,
    ServiceObjectiveCreate,
    ServiceObjectiveRead,
    ServiceObjectiveTranslateRequest,
    ServiceObjectiveTranslateResponse,
    ServiceObjectiveUpdate,
    ServiceProjectCreate,
    ServiceProjectRead,
    ServiceProjectTranslateRequest,
    ServiceProjectTranslateResponse,
    ServiceProjectUpdate,
    ServiceRead,
    ServiceReorder,
    ServiceTeamCreate,
    ServiceTeamRead,
    ServiceTeamUpdate,
    ServiceTranslateRequest,
    ServiceTranslateResponse,
    ServiceUpdate,
    ServiceWithDetails,
)
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/services", tags=["Services"])


# =============================================================================
# TRADUCTION AUTO FR → EN/AR (routes STATIQUES — déclarées avant /{service_id})
# =============================================================================


@router.post("/translate", response_model=ServiceTranslateResponse)
async def translate_service_fields(
    data: ServiceTranslateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> ServiceTranslateResponse:
    """Traduit les champs FR d'un service en EN/AR (sans persistance)."""
    return await OrganizationService(db).translate_service_fields(data)


@router.post("/objectives/translate", response_model=ServiceObjectiveTranslateResponse)
async def translate_objective_fields(
    data: ServiceObjectiveTranslateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> ServiceObjectiveTranslateResponse:
    """Traduit les champs FR d'un objectif en EN/AR (sans persistance)."""
    return await OrganizationService(db).translate_objective_fields(data)


@router.post("/achievements/translate", response_model=ServiceAchievementTranslateResponse)
async def translate_achievement_fields(
    data: ServiceAchievementTranslateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> ServiceAchievementTranslateResponse:
    """Traduit les champs FR d'une réalisation en EN/AR (sans persistance)."""
    return await OrganizationService(db).translate_achievement_fields(data)


@router.post("/projects/translate", response_model=ServiceProjectTranslateResponse)
async def translate_service_project_fields(
    data: ServiceProjectTranslateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> ServiceProjectTranslateResponse:
    """Traduit les champs FR d'un projet de service en EN/AR (sans persistance)."""
    return await OrganizationService(db).translate_service_project_fields(data)


# =============================================================================
# SERVICES CRUD
# =============================================================================


@router.get("", response_model=dict)
async def list_services(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur nom ou description"),
    sector_id: str | None = Query(None, description="Filtrer par secteur"),
    active: bool | None = Query(None, description="Filtrer par statut actif"),
    _: bool = Depends(PermissionChecker("organization.view")),
) -> dict:
    """Liste les services avec pagination et filtres."""
    service = OrganizationService(db)
    query = await service.get_services(
        search=search, sector_id=sector_id, active=active
    )
    return await paginate(db, query, pagination, Service, ServiceRead)


# NOTE: /reorder DOIT être avant /{service_id} pour éviter que FastAPI
# ne matche "reorder" comme un service_id dynamique.
@router.put("/reorder", response_model=list[ServiceRead])
async def reorder_services(
    reorder_data: ServiceReorder,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> list[Service]:
    """Réordonne les services."""
    org_service = OrganizationService(db)
    return await org_service.reorder_services(reorder_data.service_ids)


@router.get("/{service_id}", response_model=ServiceWithDetails)
async def get_service(
    service_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> Service:
    """Récupère un service par son ID."""
    org_service = OrganizationService(db)
    svc = await org_service.get_service_by_id(service_id)
    if not svc:
        raise NotFoundException("Service non trouvé")
    return svc


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> IdResponse:
    """Crée un nouveau service."""
    org_service = OrganizationService(db)
    # model_dump : forwarde aussi sigle/color et les champs de traduction _en/_ar
    # (édités via le bouton « Traduire ») ; name/sector_id mappent les params nommés.
    svc = await org_service.create_service(**service_data.model_dump(exclude_unset=True))
    return IdResponse(id=svc.id, message="Service créé avec succès")


@router.put("/{service_id}", response_model=ServiceRead)
async def update_service(
    service_id: str,
    service_data: ServiceUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> Service:
    """Met à jour un service."""
    org_service = OrganizationService(db)
    update_dict = service_data.model_dump(exclude_unset=True)
    return await org_service.update_service(service_id, **update_dict)


@router.delete("/{service_id}", response_model=MessageResponse)
async def delete_service(
    service_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> MessageResponse:
    """Supprime un service."""
    org_service = OrganizationService(db)
    await org_service.delete_service(service_id)
    return MessageResponse(message="Service supprimé avec succès")


@router.post("/{service_id}/toggle-active", response_model=ServiceRead)
async def toggle_service_active(
    service_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> Service:
    """Bascule le statut actif d'un service."""
    org_service = OrganizationService(db)
    return await org_service.toggle_service_active(service_id)


@router.post("/{service_id}/duplicate", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_service(
    service_id: str,
    db: DbSession,
    current_user: CurrentUser,
    new_name: str = Query(..., description="Nom pour le nouveau service"),
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> IdResponse:
    """Duplique un service avec un nouveau nom."""
    org_service = OrganizationService(db)
    svc = await org_service.duplicate_service(service_id, new_name)
    return IdResponse(id=svc.id, message="Service dupliqué avec succès")


# =============================================================================
# SERVICE OBJECTIVES
# =============================================================================


@router.get("/{service_id}/objectives", response_model=list[ServiceObjectiveRead])
async def get_service_objectives(
    service_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> list:
    """Récupère les objectifs d'un service."""
    org_service = OrganizationService(db)
    return await org_service.get_service_objectives(service_id)


@router.post(
    "/{service_id}/objectives",
    response_model=ServiceObjectiveRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_service_objective(
    service_id: str,
    objective_data: ServiceObjectiveCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
):
    """Crée un objectif pour un service."""
    org_service = OrganizationService(db)
    # model_dump : forwarde aussi les traductions _en/_ar éditées dans le sous-formulaire.
    return await org_service.create_service_objective(
        service_id=service_id,
        **objective_data.model_dump(exclude_unset=True),
    )


@router.put(
    "/{service_id}/objectives/{objective_id}", response_model=ServiceObjectiveRead
)
async def update_service_objective(
    service_id: str,
    objective_id: str,
    objective_data: ServiceObjectiveUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
):
    """Met à jour un objectif."""
    org_service = OrganizationService(db)
    update_dict = objective_data.model_dump(exclude_unset=True)
    return await org_service.update_service_objective(objective_id, **update_dict)


@router.delete("/{service_id}/objectives/{objective_id}", response_model=MessageResponse)
async def delete_service_objective(
    service_id: str,
    objective_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> MessageResponse:
    """Supprime un objectif."""
    org_service = OrganizationService(db)
    await org_service.delete_service_objective(objective_id)
    return MessageResponse(message="Objectif supprimé avec succès")


# =============================================================================
# SERVICE ACHIEVEMENTS
# =============================================================================


@router.get("/{service_id}/achievements", response_model=list[ServiceAchievementRead])
async def get_service_achievements(
    service_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> list:
    """Récupère les réalisations d'un service."""
    org_service = OrganizationService(db)
    return await org_service.get_service_achievements(service_id)


@router.post(
    "/{service_id}/achievements",
    response_model=ServiceAchievementRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_service_achievement(
    service_id: str,
    achievement_data: ServiceAchievementCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
):
    """Crée une réalisation pour un service."""
    org_service = OrganizationService(db)
    # model_dump : forwarde aussi les traductions _en/_ar éditées dans le sous-formulaire.
    return await org_service.create_service_achievement(
        service_id=service_id,
        **achievement_data.model_dump(exclude_unset=True),
    )


@router.put(
    "/{service_id}/achievements/{achievement_id}", response_model=ServiceAchievementRead
)
async def update_service_achievement(
    service_id: str,
    achievement_id: str,
    achievement_data: ServiceAchievementUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
):
    """Met à jour une réalisation."""
    org_service = OrganizationService(db)
    update_dict = achievement_data.model_dump(exclude_unset=True)
    return await org_service.update_service_achievement(achievement_id, **update_dict)


@router.delete(
    "/{service_id}/achievements/{achievement_id}", response_model=MessageResponse
)
async def delete_service_achievement(
    service_id: str,
    achievement_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> MessageResponse:
    """Supprime une réalisation."""
    org_service = OrganizationService(db)
    await org_service.delete_service_achievement(achievement_id)
    return MessageResponse(message="Réalisation supprimée avec succès")


# =============================================================================
# SERVICE PROJECTS
# =============================================================================


@router.get("/{service_id}/projects", response_model=list[ServiceProjectRead])
async def get_service_projects(
    service_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> list:
    """Récupère les projets d'un service."""
    org_service = OrganizationService(db)
    return await org_service.get_service_projects(service_id)


@router.post(
    "/{service_id}/projects",
    response_model=ServiceProjectRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_service_project(
    service_id: str,
    project_data: ServiceProjectCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
):
    """Crée un projet pour un service."""
    org_service = OrganizationService(db)
    # model_dump : forwarde aussi les traductions _en/_ar éditées dans le sous-formulaire.
    return await org_service.create_service_project(
        service_id=service_id,
        **project_data.model_dump(exclude_unset=True),
    )


@router.put("/{service_id}/projects/{project_id}", response_model=ServiceProjectRead)
async def update_service_project(
    service_id: str,
    project_id: str,
    project_data: ServiceProjectUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
):
    """Met à jour un projet."""
    org_service = OrganizationService(db)
    update_dict = project_data.model_dump(exclude_unset=True)
    return await org_service.update_service_project(project_id, **update_dict)


@router.delete("/{service_id}/projects/{project_id}", response_model=MessageResponse)
async def delete_service_project(
    service_id: str,
    project_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> MessageResponse:
    """Supprime un projet."""
    org_service = OrganizationService(db)
    await org_service.delete_service_project(project_id)
    return MessageResponse(message="Projet supprimé avec succès")


# =============================================================================
# SERVICE MEDIA LIBRARY
# =============================================================================


@router.get("/{service_id}/albums", response_model=list[str])
async def get_service_albums(
    service_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> list[str]:
    """Récupère les IDs d'albums associés à un service."""
    org_service = OrganizationService(db)
    return await org_service.get_service_albums(service_id)


@router.post("/{service_id}/albums/{album_id}", response_model=MessageResponse)
async def add_album_to_service(
    service_id: str,
    album_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> MessageResponse:
    """Ajoute un album à la médiathèque d'un service."""
    org_service = OrganizationService(db)
    await org_service.add_album_to_service(service_id, album_id)
    return MessageResponse(message="Album ajouté au service avec succès")


@router.delete("/{service_id}/albums/{album_id}", response_model=MessageResponse)
async def remove_album_from_service(
    service_id: str,
    album_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> MessageResponse:
    """Retire un album de la médiathèque d'un service."""
    org_service = OrganizationService(db)
    await org_service.remove_album_from_service(service_id, album_id)
    return MessageResponse(message="Album retiré du service avec succès")


# =============================================================================
# SERVICE TEAM
# =============================================================================


@router.get("/team/user/{user_id}", response_model=list[ServiceTeamRead])
async def get_user_service_affectations(
    user_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> list:
    """Récupère les affectations service d'un utilisateur."""
    org_service = OrganizationService(db)
    return await org_service.get_user_service_affectations(user_id)


@router.get("/{service_id}/team", response_model=list[ServiceTeamRead])
async def get_service_team(
    service_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> list:
    """Récupère les membres de l'équipe d'un service."""
    org_service = OrganizationService(db)
    return await org_service.get_service_team(service_id)


@router.post(
    "/{service_id}/team",
    response_model=ServiceTeamRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_service_team_member(
    service_id: str,
    member_data: ServiceTeamCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
):
    """Ajoute un membre à l'équipe d'un service."""
    org_service = OrganizationService(db)
    return await org_service.create_service_team_member(
        service_id=service_id,
        user_external_id=member_data.user_external_id,
        position=member_data.position,
        display_order=member_data.display_order,
        start_date=member_data.start_date,
        end_date=member_data.end_date,
        active=member_data.active,
    )


@router.put("/{service_id}/team/{member_id}", response_model=ServiceTeamRead)
async def update_service_team_member(
    service_id: str,
    member_id: str,
    member_data: ServiceTeamUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
):
    """Met à jour un membre de l'équipe."""
    org_service = OrganizationService(db)
    update_dict = member_data.model_dump(exclude_unset=True)
    return await org_service.update_service_team_member(member_id, **update_dict)


@router.delete("/{service_id}/team/{member_id}", response_model=MessageResponse)
async def delete_service_team_member(
    service_id: str,
    member_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> MessageResponse:
    """Supprime un membre de l'équipe."""
    org_service = OrganizationService(db)
    await org_service.delete_service_team_member(member_id)
    return MessageResponse(message="Membre supprimé avec succès")
