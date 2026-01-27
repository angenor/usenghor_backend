"""
Router Admin - Départements
===========================

Endpoints CRUD pour la gestion des départements.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.organization import Department
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.organization import (
    DepartmentCreate,
    DepartmentRead,
    DepartmentReorder,
    DepartmentUpdate,
    DepartmentWithServices,
    ServiceRead,
)
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=dict)
async def list_departments(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur code ou nom"),
    active: bool | None = Query(None, description="Filtrer par statut actif"),
    _: bool = Depends(PermissionChecker("organization.view")),
) -> dict:
    """Liste les départements avec pagination et filtres."""
    service = OrganizationService(db)
    query = await service.get_departments(search=search, active=active)
    return await paginate(db, query, pagination, Department, DepartmentRead)


@router.get("/{department_id}", response_model=DepartmentWithServices)
async def get_department(
    department_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> Department:
    """Récupère un département par son ID."""
    service = OrganizationService(db)
    department = await service.get_department_by_id(department_id)
    if not department:
        raise NotFoundException("Département non trouvé")
    return department


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_data: DepartmentCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> IdResponse:
    """Crée un nouveau département."""
    service = OrganizationService(db)
    department = await service.create_department(
        code=department_data.code,
        name=department_data.name,
        description=department_data.description,
        mission=department_data.mission,
        icon_external_id=department_data.icon_external_id,
        cover_image_external_id=department_data.cover_image_external_id,
        head_external_id=department_data.head_external_id,
        display_order=department_data.display_order,
        active=department_data.active,
    )
    return IdResponse(id=department.id, message="Département créé avec succès")


@router.put("/{department_id}", response_model=DepartmentRead)
async def update_department(
    department_id: str,
    department_data: DepartmentUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> Department:
    """Met à jour un département."""
    service = OrganizationService(db)
    update_dict = department_data.model_dump(exclude_unset=True)
    return await service.update_department(department_id, **update_dict)


@router.delete("/{department_id}", response_model=MessageResponse)
async def delete_department(
    department_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> MessageResponse:
    """Supprime un département."""
    service = OrganizationService(db)
    await service.delete_department(department_id)
    return MessageResponse(message="Département supprimé avec succès")


@router.post("/{department_id}/toggle-active", response_model=DepartmentRead)
async def toggle_department_active(
    department_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> Department:
    """Bascule le statut actif d'un département."""
    service = OrganizationService(db)
    return await service.toggle_department_active(department_id)


@router.put("/reorder", response_model=list[DepartmentRead])
async def reorder_departments(
    reorder_data: DepartmentReorder,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.edit")),
) -> list[Department]:
    """Réordonne les départements."""
    service = OrganizationService(db)
    return await service.reorder_departments(reorder_data.department_ids)


@router.get("/{department_id}/services", response_model=list[ServiceRead])
async def get_department_services(
    department_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("organization.view")),
) -> list:
    """Récupère les services d'un département."""
    service = OrganizationService(db)
    return await service.get_department_services(department_id)
