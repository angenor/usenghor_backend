"""
Router Admin - Permissions
===========================

Endpoints CRUD pour la gestion des permissions.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.pagination import PaginationParams, paginate
from app.models.identity import Permission, RolePermission
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.identity import (
    PermissionCreate,
    PermissionMatrix,
    PermissionMatrixUpdate,
    PermissionRead,
    PermissionUpdate,
    RoleRead,
)
from app.services.identity_service import IdentityService

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("", response_model=dict)
async def list_permissions(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur code ou nom"),
    category: str | None = Query(None, description="Filtrer par catégorie"),
    _: bool = Depends(PermissionChecker("users.view")),
) -> dict:
    """Liste les permissions avec pagination et filtres."""
    service = IdentityService(db)
    query = await service.get_permissions(search=search, category=category)
    return await paginate(db, query, pagination, Permission)


@router.get("/matrix", response_model=PermissionMatrix)
async def get_permissions_matrix(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.view")),
) -> dict:
    """Récupère la matrice permissions/rôles."""
    service = IdentityService(db)
    return await service.get_permissions_matrix()


@router.put("/matrix", response_model=MessageResponse)
async def update_permissions_matrix(
    matrix_data: PermissionMatrixUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.roles")),
) -> MessageResponse:
    """Met à jour la matrice permissions/rôles."""
    from sqlalchemy import delete

    service = IdentityService(db)
    count = 0

    for update in matrix_data.updates:
        role_id = update.get("role_id")
        permission_id = update.get("permission_id")
        granted = update.get("granted", False)

        if not role_id or not permission_id:
            continue

        # Vérifier que le rôle et la permission existent
        role = await service.get_role_by_id(role_id)
        perm = await service.get_permission_by_id(permission_id)

        if not role or not perm:
            continue

        if granted:
            # Ajouter la permission au rôle si elle n'existe pas
            existing = any(p.id == permission_id for p in role.permissions)
            if not existing:
                role_perm = RolePermission(role_id=role_id, permission_id=permission_id)
                db.add(role_perm)
                count += 1
        else:
            # Retirer la permission du rôle
            await db.execute(
                delete(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id,
                )
            )
            count += 1

    return MessageResponse(message=f"{count} modification(s) effectuée(s)")


@router.get("/{permission_id}", response_model=PermissionRead)
async def get_permission(
    permission_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.view")),
) -> Permission:
    """Récupère une permission par son ID."""
    service = IdentityService(db)
    perm = await service.get_permission_by_id(permission_id)
    if not perm:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Permission non trouvée")
    return perm


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    perm_data: PermissionCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.roles")),
) -> IdResponse:
    """Crée une nouvelle permission."""
    service = IdentityService(db)
    perm = await service.create_permission(
        code=perm_data.code,
        name_fr=perm_data.name_fr,
        description=perm_data.description,
        category=perm_data.category,
    )
    return IdResponse(id=perm.id, message="Permission créée avec succès")


@router.put("/{permission_id}", response_model=PermissionRead)
async def update_permission(
    permission_id: str,
    perm_data: PermissionUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.roles")),
) -> Permission:
    """Met à jour une permission."""
    service = IdentityService(db)
    update_dict = perm_data.model_dump(exclude_unset=True)
    return await service.update_permission(permission_id, **update_dict)


@router.get("/{permission_id}/roles", response_model=list[RoleRead])
async def get_permission_roles(
    permission_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.view")),
) -> list:
    """Récupère les rôles ayant une permission."""
    service = IdentityService(db)
    return await service.get_permission_roles(permission_id)
