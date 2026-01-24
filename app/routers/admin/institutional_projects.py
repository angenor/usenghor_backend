"""
Router Admin - Projets Institutionnels
======================================

Endpoints CRUD pour la gestion des projets institutionnels.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.base import PublicationStatus
from app.models.organization import ProjectStatus
from app.models.project import Project, ProjectCall, ProjectCallStatus, ProjectCategory
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.project import (
    ProjectCallCreate,
    ProjectCallRead,
    ProjectCallUpdate,
    ProjectCategoryCreate,
    ProjectCategoryRead,
    ProjectCategoryUpdate,
    ProjectCreate,
    ProjectMediaCreate,
    ProjectMediaRead,
    ProjectPartnerCreate,
    ProjectPartnerRead,
    ProjectPartnerUpdate,
    ProjectRead,
    ProjectReadWithRelations,
    ProjectStatistics,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Institutional Projects"])


# =============================================================================
# CATEGORIES
# =============================================================================


@router.get("/categories", response_model=dict)
async def list_categories(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche"),
    _: bool = Depends(PermissionChecker("project.view")),
) -> dict:
    """Liste les catégories de projets."""
    service = ProjectService(db)
    query = await service.get_categories(search=search)
    return await paginate(db, query, pagination, ProjectCategory)


@router.get("/categories/{category_id}", response_model=ProjectCategoryRead)
async def get_category(
    category_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.view")),
) -> ProjectCategory:
    """Récupère une catégorie par son ID."""
    service = ProjectService(db)
    category = await service.get_category_by_id(category_id)
    if not category:
        raise NotFoundException("Catégorie non trouvée")
    return category


@router.post(
    "/categories", response_model=IdResponse, status_code=status.HTTP_201_CREATED
)
async def create_category(
    data: ProjectCategoryCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.create")),
) -> IdResponse:
    """Crée une nouvelle catégorie."""
    service = ProjectService(db)
    category = await service.create_category(**data.model_dump(exclude_unset=True))
    return IdResponse(id=category.id)


@router.put("/categories/{category_id}", response_model=ProjectCategoryRead)
async def update_category(
    category_id: str,
    data: ProjectCategoryUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.edit")),
) -> ProjectCategory:
    """Met à jour une catégorie."""
    service = ProjectService(db)
    return await service.update_category(
        category_id, **data.model_dump(exclude_unset=True)
    )


@router.delete("/categories/{category_id}", response_model=MessageResponse)
async def delete_category(
    category_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.delete")),
) -> MessageResponse:
    """Supprime une catégorie."""
    service = ProjectService(db)
    await service.delete_category(category_id)
    return MessageResponse(message="Catégorie supprimée avec succès")


# =============================================================================
# PROJECTS
# =============================================================================


@router.get("", response_model=dict)
async def list_projects(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche"),
    status: ProjectStatus | None = Query(None, description="Statut"),
    publication_status: PublicationStatus | None = Query(
        None, description="Statut publication"
    ),
    category_id: str | None = Query(None, description="Catégorie"),
    department_external_id: str | None = Query(None, description="Département"),
    _: bool = Depends(PermissionChecker("project.view")),
) -> dict:
    """Liste les projets avec pagination et filtres."""
    service = ProjectService(db)
    query = await service.get_projects(
        search=search,
        status=status,
        publication_status=publication_status,
        category_id=category_id,
        department_external_id=department_external_id,
    )
    return await paginate(db, query, pagination, Project)


@router.get("/statistics", response_model=ProjectStatistics)
async def get_statistics(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.view")),
) -> ProjectStatistics:
    """Récupère les statistiques des projets."""
    service = ProjectService(db)
    stats = await service.get_statistics()
    return ProjectStatistics(**stats)


@router.get("/{project_id}", response_model=ProjectReadWithRelations)
async def get_project(
    project_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.view")),
) -> Project:
    """Récupère un projet par son ID."""
    service = ProjectService(db)
    project = await service.get_project_by_id(project_id)
    if not project:
        raise NotFoundException("Projet non trouvé")
    return project


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.create")),
) -> IdResponse:
    """Crée un nouveau projet."""
    service = ProjectService(db)
    project = await service.create_project(**data.model_dump(exclude_unset=True))
    return IdResponse(id=project.id)


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.edit")),
) -> Project:
    """Met à jour un projet."""
    service = ProjectService(db)
    return await service.update_project(
        project_id, **data.model_dump(exclude_unset=True)
    )


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.delete")),
) -> MessageResponse:
    """Supprime un projet."""
    service = ProjectService(db)
    await service.delete_project(project_id)
    return MessageResponse(message="Projet supprimé avec succès")


@router.post("/{project_id}/publish", response_model=ProjectRead)
async def publish_project(
    project_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.edit")),
) -> Project:
    """Publie un projet."""
    service = ProjectService(db)
    return await service.publish_project(project_id)


@router.post("/{project_id}/unpublish", response_model=ProjectRead)
async def unpublish_project(
    project_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.edit")),
) -> Project:
    """Dépublie un projet."""
    service = ProjectService(db)
    return await service.unpublish_project(project_id)


# =============================================================================
# PROJECT PARTNERS
# =============================================================================


@router.get("/{project_id}/partners", response_model=list[ProjectPartnerRead])
async def list_project_partners(
    project_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.view")),
) -> list[ProjectPartnerRead]:
    """Liste les partenaires d'un projet."""
    service = ProjectService(db)
    project = await service.get_project_by_id(project_id)
    if not project:
        raise NotFoundException("Projet non trouvé")
    partners = await service.get_project_partners(project_id)
    return [ProjectPartnerRead.model_validate(p) for p in partners]


@router.post(
    "/{project_id}/partners",
    response_model=ProjectPartnerRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_partner(
    project_id: str,
    data: ProjectPartnerCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.edit")),
) -> ProjectPartnerRead:
    """Ajoute un partenaire à un projet."""
    service = ProjectService(db)
    partner = await service.add_partner(
        project_id, data.partner_external_id, data.partner_role
    )
    return ProjectPartnerRead.model_validate(partner)


@router.put(
    "/{project_id}/partners/{partner_external_id}", response_model=ProjectPartnerRead
)
async def update_project_partner(
    project_id: str,
    partner_external_id: str,
    data: ProjectPartnerUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.edit")),
) -> ProjectPartnerRead:
    """Met à jour un partenaire de projet."""
    service = ProjectService(db)
    partner = await service.update_partner(
        project_id, partner_external_id, data.partner_role
    )
    return ProjectPartnerRead.model_validate(partner)


@router.delete(
    "/{project_id}/partners/{partner_external_id}", response_model=MessageResponse
)
async def remove_project_partner(
    project_id: str,
    partner_external_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.edit")),
) -> MessageResponse:
    """Retire un partenaire d'un projet."""
    service = ProjectService(db)
    await service.remove_partner(project_id, partner_external_id)
    return MessageResponse(message="Partenaire retiré avec succès")


# =============================================================================
# PROJECT CALLS
# =============================================================================


@router.get("/calls/all", response_model=dict)
async def list_all_calls(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    status: ProjectCallStatus | None = Query(None, description="Statut"),
    _: bool = Depends(PermissionChecker("project.view")),
) -> dict:
    """Liste tous les appels de projets."""
    service = ProjectService(db)
    query = await service.get_calls(status=status)
    return await paginate(db, query, pagination, ProjectCall)


@router.get("/{project_id}/calls", response_model=list[ProjectCallRead])
async def list_project_calls(
    project_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.view")),
) -> list[ProjectCallRead]:
    """Liste les appels d'un projet."""
    service = ProjectService(db)
    project = await service.get_project_by_id(project_id)
    if not project:
        raise NotFoundException("Projet non trouvé")
    return [ProjectCallRead.model_validate(c) for c in project.calls]


@router.post(
    "/{project_id}/calls",
    response_model=IdResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_call(
    project_id: str,
    data: ProjectCallCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.edit")),
) -> IdResponse:
    """Crée un nouvel appel pour un projet."""
    service = ProjectService(db)
    call = await service.create_call(
        project_id, **data.model_dump(exclude_unset=True)
    )
    return IdResponse(id=call.id)


@router.get("/calls/{call_id}", response_model=ProjectCallRead)
async def get_call(
    call_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.view")),
) -> ProjectCall:
    """Récupère un appel par son ID."""
    service = ProjectService(db)
    call = await service.get_call_by_id(call_id)
    if not call:
        raise NotFoundException("Appel non trouvé")
    return call


@router.put("/calls/{call_id}", response_model=ProjectCallRead)
async def update_call(
    call_id: str,
    data: ProjectCallUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.edit")),
) -> ProjectCall:
    """Met à jour un appel."""
    service = ProjectService(db)
    return await service.update_call(call_id, **data.model_dump(exclude_unset=True))


@router.delete("/calls/{call_id}", response_model=MessageResponse)
async def delete_call(
    call_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.delete")),
) -> MessageResponse:
    """Supprime un appel."""
    service = ProjectService(db)
    await service.delete_call(call_id)
    return MessageResponse(message="Appel supprimé avec succès")


# =============================================================================
# PROJECT MEDIA LIBRARY
# =============================================================================


@router.get("/{project_id}/media", response_model=list[ProjectMediaRead])
async def list_project_media(
    project_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.view")),
) -> list[ProjectMediaRead]:
    """Liste les albums de la médiathèque d'un projet."""
    service = ProjectService(db)
    project = await service.get_project_by_id(project_id)
    if not project:
        raise NotFoundException("Projet non trouvé")
    albums = await service.get_project_albums(project_id)
    return [ProjectMediaRead.model_validate(a) for a in albums]


@router.post(
    "/{project_id}/media",
    response_model=ProjectMediaRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_album(
    project_id: str,
    data: ProjectMediaCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.edit")),
) -> ProjectMediaRead:
    """Ajoute un album à la médiathèque d'un projet."""
    service = ProjectService(db)
    media = await service.add_album(project_id, data.album_external_id)
    return ProjectMediaRead.model_validate(media)


@router.delete(
    "/{project_id}/media/{album_external_id}", response_model=MessageResponse
)
async def remove_project_album(
    project_id: str,
    album_external_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("project.edit")),
) -> MessageResponse:
    """Retire un album de la médiathèque d'un projet."""
    service = ProjectService(db)
    await service.remove_album(project_id, album_external_id)
    return MessageResponse(message="Album retiré avec succès")
