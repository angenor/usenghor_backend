"""
Dépendances FastAPI
===================

Dépendances réutilisables pour l'injection de dépendances.
"""

from functools import wraps
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import CredentialsException, PermissionDeniedException
from app.core.security import decode_token
from app.database import get_db
from app.models.identity import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Récupère l'utilisateur courant à partir du token JWT.

    Args:
        token: Token JWT Bearer.
        db: Session de base de données.

    Returns:
        Utilisateur authentifié.

    Raises:
        CredentialsException: Si le token est invalide ou l'utilisateur n'existe pas.
    """
    payload = decode_token(token)
    if payload is None:
        raise CredentialsException("Token invalide ou expiré")

    if payload.get("type") != "access":
        raise CredentialsException("Type de token invalide")

    user_id: str = payload.get("sub")
    if user_id is None:
        raise CredentialsException("Token invalide")

    # Charger l'utilisateur avec ses rôles et permissions
    from app.models.identity import Role

    result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise CredentialsException("Utilisateur non trouvé")

    if not user.active:
        raise CredentialsException("Compte désactivé")

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Vérifie que l'utilisateur est actif.

    Args:
        current_user: Utilisateur courant.

    Returns:
        Utilisateur actif.

    Raises:
        CredentialsException: Si l'utilisateur est inactif.
    """
    if not current_user.active:
        raise CredentialsException("Compte désactivé")
    return current_user


def require_permission(permission_code: str):
    """
    Décorateur pour vérifier une permission spécifique.

    Args:
        permission_code: Code de la permission requise.

    Example:
        @router.get("/users")
        @require_permission("users.view")
        async def list_users(current_user: User = Depends(get_current_user)):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Récupérer current_user depuis les kwargs
            current_user = kwargs.get("current_user")
            if current_user is None:
                raise CredentialsException("Authentification requise")

            if not current_user.has_permission(permission_code):
                raise PermissionDeniedException(
                    f"Permission '{permission_code}' requise"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


class PermissionChecker:
    """
    Classe de vérification des permissions utilisable comme dépendance.

    Example:
        @router.get("/users")
        async def list_users(
            current_user: User = Depends(get_current_user),
            _: bool = Depends(PermissionChecker("users.view"))
        ):
            ...
    """

    def __init__(self, permission_code: str):
        self.permission_code = permission_code

    async def __call__(
        self, current_user: Annotated[User, Depends(get_current_user)]
    ) -> bool:
        if not current_user.has_permission(self.permission_code):
            raise PermissionDeniedException(
                f"Permission '{self.permission_code}' requise"
            )
        return True


# Type aliases pour les annotations
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
