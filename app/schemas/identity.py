"""
Schémas Identity
================

Schémas Pydantic pour l'authentification et les utilisateurs.
"""

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


# =============================================================================
# Token Schemas
# =============================================================================


class Token(BaseModel):
    """Token d'accès retourné après authentification."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Payload du token JWT."""

    sub: str  # user_id
    exp: datetime
    type: str  # access ou refresh


# =============================================================================
# Auth Schemas
# =============================================================================


class LoginRequest(BaseModel):
    """Requête de connexion."""

    email: EmailStr
    password: str = Field(min_length=6)


class RefreshTokenRequest(BaseModel):
    """Requête de rafraîchissement du token."""

    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Requête de réinitialisation de mot de passe."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Requête de nouveau mot de passe."""

    token: str
    new_password: str = Field(min_length=8)


class ChangePasswordRequest(BaseModel):
    """Requête de changement de mot de passe."""

    current_password: str
    new_password: str = Field(min_length=8)


# =============================================================================
# Permission Schemas
# =============================================================================


class PermissionBase(BaseModel):
    """Base pour les permissions."""

    code: str
    name_fr: str
    description: str | None = None
    category: str | None = None


class PermissionRead(PermissionBase):
    """Permission en lecture."""

    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Role Schemas
# =============================================================================


class RoleBase(BaseModel):
    """Base pour les rôles."""

    code: str
    name_fr: str
    description: str | None = None
    hierarchy_level: int = 0
    active: bool = True


class RoleRead(RoleBase):
    """Rôle en lecture."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoleWithPermissions(RoleRead):
    """Rôle avec ses permissions."""

    permissions: list[PermissionRead] = []


# =============================================================================
# User Schemas
# =============================================================================


class UserBase(BaseModel):
    """Base pour les utilisateurs."""

    email: EmailStr
    last_name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    salutation: str | None = None
    birth_date: date | None = None
    phone: str | None = None
    phone_whatsapp: str | None = None
    linkedin: str | None = None
    city: str | None = None
    address: str | None = None


class UserCreate(UserBase):
    """Création d'utilisateur."""

    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    """Mise à jour d'utilisateur."""

    email: EmailStr | None = None
    last_name: str | None = None
    first_name: str | None = None
    salutation: str | None = None
    birth_date: date | None = None
    phone: str | None = None
    phone_whatsapp: str | None = None
    linkedin: str | None = None
    city: str | None = None
    address: str | None = None
    active: bool | None = None


class UserRead(UserBase):
    """Utilisateur en lecture."""

    id: str
    active: bool
    email_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    photo_external_id: str | None = None
    nationality_external_id: str | None = None
    residence_country_external_id: str | None = None

    model_config = {"from_attributes": True}


class UserWithRoles(UserRead):
    """Utilisateur avec ses rôles."""

    roles: list[RoleRead] = []


class UserMe(UserRead):
    """Utilisateur courant avec permissions."""

    roles: list[RoleWithPermissions] = []

    @property
    def permissions(self) -> list[str]:
        """Liste des codes de permissions."""
        perms = set()
        for role in self.roles:
            for perm in role.permissions:
                perms.add(perm.code)
        return list(perms)


class UserMeUpdate(BaseModel):
    """Mise à jour du profil utilisateur courant."""

    last_name: str | None = None
    first_name: str | None = None
    salutation: str | None = None
    birth_date: date | None = None
    phone: str | None = None
    phone_whatsapp: str | None = None
    linkedin: str | None = None
    city: str | None = None
    address: str | None = None
