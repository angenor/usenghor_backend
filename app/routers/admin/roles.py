"""
Router Admin - Rôles
=====================

Endpoints CRUD pour la gestion des rôles.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.pagination import PaginationParams, paginate
from app.models.identity import Role
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.identity import (
    RoleCreate,
    RoleDuplicate,
    RolePermissionsUpdate,
    RoleRead,
    RoleUpdate,
    RoleWithPermissions,
    UserRead,
)
from app.services.identity_service import IdentityService

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=dict)
async def list_roles(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur code ou nom"),
    active: bool | None = Query(None, description="Filtrer par statut actif"),
    _: bool = Depends(PermissionChecker("users.view")),
) -> dict:
    """Liste les rôles avec pagination et filtres."""
    service = IdentityService(db)
    query = await service.get_roles(search=search, active=active)
    return await paginate(db, query, pagination, Role)


@router.get("/{role_id}", response_model=RoleWithPermissions)
async def get_role(
    role_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.view")),
) -> Role:
    """Récupère un rôle par son ID."""
    service = IdentityService(db)
    role = await service.get_role_by_id(role_id)
    if not role:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Rôle non trouvé")
    return role


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.roles")),
) -> IdResponse:
    """Crée un nouveau rôle."""
    service = IdentityService(db)
    role = await service.create_role(
        code=role_data.code,
        name_fr=role_data.name_fr,
        description=role_data.description,
        hierarchy_level=role_data.hierarchy_level,
        active=role_data.active,
    )
    return IdResponse(id=role.id, message="Rôle créé avec succès")


@router.put("/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.roles")),
) -> Role:
    """Met à jour un rôle."""
    service = IdentityService(db)
    update_dict = role_data.model_dump(exclude_unset=True)
    return await service.update_role(role_id, **update_dict)


@router.delete("/{role_id}", response_model=MessageResponse)
async def delete_role(
    role_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.roles")),
) -> MessageResponse:
    """Supprime un rôle."""
    service = IdentityService(db)
    await service.delete_role(role_id)
    return MessageResponse(message="Rôle supprimé avec succès")


@router.post("/{role_id}/duplicate", response_model=RoleWithPermissions)
async def duplicate_role(
    role_id: str,
    duplicate_data: RoleDuplicate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.roles")),
) -> Role:
    """Duplique un rôle avec ses permissions."""
    service = IdentityService(db)
    return await service.duplicate_role(
        role_id, duplicate_data.new_code, duplicate_data.new_name
    )


@router.post("/{role_id}/toggle-active", response_model=RoleRead)
async def toggle_role_active(
    role_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.roles")),
) -> Role:
    """Bascule le statut actif d'un rôle."""
    service = IdentityService(db)
    return await service.toggle_role_active(role_id)


@router.get("/{role_id}/permissions", response_model=list)
async def get_role_permissions(
    role_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.view")),
) -> list:
    """Récupère les permissions d'un rôle."""
    service = IdentityService(db)
    role = await service.get_role_by_id(role_id)
    if not role:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Rôle non trouvé")
    return [
        {"id": p.id, "code": p.code, "name_fr": p.name_fr, "category": p.category}
        for p in role.permissions
    ]


@router.put("/{role_id}/permissions", response_model=RoleWithPermissions)
async def update_role_permissions(
    role_id: str,
    permissions_data: RolePermissionsUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.roles")),
) -> Role:
    """Met à jour les permissions d'un rôle."""
    service = IdentityService(db)
    return await service.set_role_permissions(role_id, permissions_data.permission_ids)


@router.get("/{role_id}/users", response_model=list[UserRead])
async def get_role_users(
    role_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.view")),
) -> list:
    """Récupère les utilisateurs ayant un rôle."""
    service = IdentityService(db)
    return await service.get_role_users(role_id)


@router.get("/compare", response_model=dict)
async def compare_roles(
    db: DbSession,
    current_user: CurrentUser,
    role_ids: str = Query(..., description="IDs des rôles séparés par des virgules"),
    _: bool = Depends(PermissionChecker("users.view")),
) -> dict:
    """Compare les permissions de plusieurs rôles."""
    service = IdentityService(db)
    ids = [r.strip() for r in role_ids.split(",")]

    comparison = {}
    roles_info = []

    for role_id in ids:
        role = await service.get_role_by_id(role_id)
        if role:
            roles_info.append({
                "id": role.id,
                "code": role.code,
                "name_fr": role.name_fr,
            })
            for perm in role.permissions:
                if perm.code not in comparison:
                    comparison[perm.code] = {
                        "name_fr": perm.name_fr,
                        "category": perm.category,
                        "roles": {},
                    }
                comparison[perm.code]["roles"][role.code] = True

    return {
        "roles": roles_info,
        "permissions": comparison,
    }
