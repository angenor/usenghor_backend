"""
Router d'authentification
=========================

Endpoints pour l'authentification et la gestion du profil utilisateur.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import CredentialsException, NotFoundException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.identity import Role, User
from app.schemas.common import MessageResponse
from app.schemas.identity import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    Token,
    UserMe,
    UserMeUpdate,
    UserRead,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: DbSession = None,
) -> Token:
    """
    Authentifie un utilisateur et retourne les tokens JWT.

    - **username**: Email de l'utilisateur
    - **password**: Mot de passe
    """
    # Rechercher l'utilisateur par email
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise CredentialsException("Email ou mot de passe incorrect")

    if not user.password_hash:
        raise CredentialsException("Compte non configuré")

    if not verify_password(form_data.password, user.password_hash):
        raise CredentialsException("Email ou mot de passe incorrect")

    if not user.active:
        raise CredentialsException("Compte désactivé")

    # Mettre à jour last_login_at
    await db.execute(
        update(User).where(User.id == user.id).values(last_login_at=datetime.now(timezone.utc))
    )

    # Créer les tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/login/json", response_model=Token)
async def login_json(
    credentials: LoginRequest,
    db: DbSession = None,
) -> Token:
    """
    Authentifie un utilisateur via JSON et retourne les tokens JWT.

    Alternative à /login pour les clients qui préfèrent JSON.
    """
    # Rechercher l'utilisateur par email
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise CredentialsException("Email ou mot de passe incorrect")

    if not user.password_hash:
        raise CredentialsException("Compte non configuré")

    if not verify_password(credentials.password, user.password_hash):
        raise CredentialsException("Email ou mot de passe incorrect")

    if not user.active:
        raise CredentialsException("Compte désactivé")

    # Mettre à jour last_login_at
    await db.execute(
        update(User).where(User.id == user.id).values(last_login_at=datetime.now(timezone.utc))
    )

    # Créer les tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    db: DbSession = None,
) -> Token:
    """
    Rafraîchit les tokens JWT avec un refresh token valide.
    """
    payload = decode_token(request.refresh_token)

    if payload is None:
        raise CredentialsException("Token de rafraîchissement invalide ou expiré")

    if payload.get("type") != "refresh":
        raise CredentialsException("Type de token invalide")

    user_id = payload.get("sub")
    if user_id is None:
        raise CredentialsException("Token invalide")

    # Vérifier que l'utilisateur existe toujours
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise CredentialsException("Utilisateur non trouvé")

    if not user.active:
        raise CredentialsException("Compte désactivé")

    # Créer de nouveaux tokens
    access_token = create_access_token(data={"sub": user.id})
    new_refresh_token = create_refresh_token(data={"sub": user.id})

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: CurrentUser,
) -> MessageResponse:
    """
    Déconnecte l'utilisateur.

    Note: Avec JWT, la déconnexion côté serveur est limitée.
    Le client doit supprimer les tokens stockés localement.
    """
    # Dans une implémentation plus avancée, on pourrait :
    # - Invalider le refresh token en base
    # - Utiliser une liste noire de tokens
    return MessageResponse(message="Déconnexion réussie")


@router.get("/me", response_model=UserMe)
async def get_me(
    current_user: CurrentUser,
) -> User:
    """
    Retourne les informations de l'utilisateur connecté.
    """
    return current_user


@router.put("/me", response_model=UserRead)
async def update_me(
    user_update: UserMeUpdate,
    current_user: CurrentUser,
    db: DbSession = None,
) -> User:
    """
    Met à jour le profil de l'utilisateur connecté.
    """
    update_data = user_update.model_dump(exclude_unset=True)

    if update_data:
        await db.execute(
            update(User).where(User.id == current_user.id).values(**update_data)
        )
        await db.refresh(current_user)

    return current_user


@router.put("/me/password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DbSession = None,
) -> MessageResponse:
    """
    Change le mot de passe de l'utilisateur connecté.
    """
    if not current_user.password_hash:
        raise CredentialsException("Compte non configuré")

    if not verify_password(request.current_password, current_user.password_hash):
        raise CredentialsException("Mot de passe actuel incorrect")

    new_hash = get_password_hash(request.new_password)
    await db.execute(
        update(User).where(User.id == current_user.id).values(password_hash=new_hash)
    )

    return MessageResponse(message="Mot de passe modifié avec succès")
