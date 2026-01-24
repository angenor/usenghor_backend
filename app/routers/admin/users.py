"""
Router Admin - Utilisateurs
============================

Endpoints CRUD pour la gestion des utilisateurs.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.pagination import PaginationParams, paginate
from app.models.identity import User
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.identity import (
    PasswordResetResponse,
    UserBulkAction,
    UserCreate,
    UserRead,
    UserRolesUpdate,
    UserUpdate,
    UserWithRoles,
)
from app.services.identity_service import IdentityService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=dict)
async def list_users(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur email, nom, prénom"),
    active: bool | None = Query(None, description="Filtrer par statut actif"),
    role_id: str | None = Query(None, description="Filtrer par rôle"),
    _: bool = Depends(PermissionChecker("users.view")),
) -> dict:
    """Liste les utilisateurs avec pagination et filtres."""
    service = IdentityService(db)
    query = await service.get_users(search=search, active=active, role_id=role_id)
    return await paginate(db, query, pagination, User)


@router.get("/{user_id}", response_model=UserWithRoles)
async def get_user(
    user_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.view")),
) -> User:
    """Récupère un utilisateur par son ID."""
    service = IdentityService(db)
    user = await service.get_user_by_id(user_id)
    if not user:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Utilisateur non trouvé")
    return user


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.create")),
) -> IdResponse:
    """Crée un nouvel utilisateur."""
    service = IdentityService(db)
    user = await service.create_user(
        email=user_data.email,
        password=user_data.password,
        last_name=user_data.last_name,
        first_name=user_data.first_name,
        salutation=user_data.salutation,
        birth_date=user_data.birth_date,
        phone=user_data.phone,
        phone_whatsapp=user_data.phone_whatsapp,
        linkedin=user_data.linkedin,
        city=user_data.city,
        address=user_data.address,
    )
    return IdResponse(id=user.id, message="Utilisateur créé avec succès")


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.edit")),
) -> User:
    """Met à jour un utilisateur."""
    service = IdentityService(db)
    update_dict = user_data.model_dump(exclude_unset=True)
    return await service.update_user(user_id, **update_dict)


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.delete")),
) -> MessageResponse:
    """Supprime un utilisateur."""
    service = IdentityService(db)
    await service.delete_user(user_id)
    return MessageResponse(message="Utilisateur supprimé avec succès")


@router.post("/{user_id}/toggle-active", response_model=UserRead)
async def toggle_user_active(
    user_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.edit")),
) -> User:
    """Bascule le statut actif d'un utilisateur."""
    service = IdentityService(db)
    return await service.toggle_user_active(user_id)


@router.post("/bulk-action", response_model=MessageResponse)
async def bulk_action(
    action_data: UserBulkAction,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.edit")),
) -> MessageResponse:
    """Effectue une action en masse sur les utilisateurs."""
    service = IdentityService(db)
    count = 0

    for user_id in action_data.user_ids:
        try:
            if action_data.action == "activate":
                user = await service.get_user_by_id(user_id)
                if user and not user.active:
                    await service.update_user(user_id, active=True)
                    count += 1
            elif action_data.action == "deactivate":
                user = await service.get_user_by_id(user_id)
                if user and user.active:
                    await service.update_user(user_id, active=False)
                    count += 1
            elif action_data.action == "delete":
                await service.delete_user(user_id)
                count += 1
        except Exception:
            continue

    return MessageResponse(message=f"{count} utilisateur(s) modifié(s)")


@router.get("/{user_id}/roles", response_model=list)
async def get_user_roles(
    user_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.view")),
) -> list:
    """Récupère les rôles d'un utilisateur."""
    service = IdentityService(db)
    user = await service.get_user_by_id(user_id)
    if not user:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Utilisateur non trouvé")
    return [{"id": r.id, "code": r.code, "name_fr": r.name_fr} for r in user.roles]


@router.put("/{user_id}/roles", response_model=UserWithRoles)
async def update_user_roles(
    user_id: str,
    roles_data: UserRolesUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.roles")),
) -> User:
    """Met à jour les rôles d'un utilisateur."""
    service = IdentityService(db)
    return await service.set_user_roles(
        user_id, roles_data.role_ids, assigned_by=current_user.id
    )


@router.post("/{user_id}/reset-password", response_model=PasswordResetResponse)
async def reset_user_password(
    user_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.edit")),
) -> PasswordResetResponse:
    """Réinitialise le mot de passe d'un utilisateur."""
    service = IdentityService(db)
    new_password = await service.reset_user_password(user_id)
    return PasswordResetResponse(temporary_password=new_password)


@router.post("/{user_id}/verify-email", response_model=UserRead)
async def verify_user_email(
    user_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.edit")),
) -> User:
    """Marque l'email d'un utilisateur comme vérifié."""
    service = IdentityService(db)
    return await service.verify_user_email(user_id)


@router.get("/{user_id}/permissions", response_model=list[str])
async def get_user_permissions(
    user_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.view")),
) -> list[str]:
    """Récupère les permissions d'un utilisateur."""
    service = IdentityService(db)
    return await service.get_user_permissions(user_id)


@router.post("/{user_id}/anonymize", response_model=UserRead)
async def anonymize_user(
    user_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("users.delete")),
) -> User:
    """Anonymise un utilisateur (RGPD)."""
    service = IdentityService(db)
    return await service.anonymize_user(user_id)
