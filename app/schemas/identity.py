"""
Schémas Identity
================

Schémas Pydantic pour l'authentification et les utilisateurs.
"""

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


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


class RegisterRequest(BaseModel):
    """Requête d'inscription publique."""

    email: EmailStr
    password: str = Field(min_length=8)
    last_name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    salutation: str | None = None
    # Affectation organisationnelle (obligatoire pour le personnel)
    sector_id: str = Field(min_length=1)
    service_id: str = Field(min_length=1)
    campus_id: str = Field(min_length=1)
    # Champs optionnels
    biography: str | None = None
    linkedin_url: str | None = None
    facebook_url: str | None = None
    photo_base64: str | None = None


class RegisterResponse(BaseModel):
    """Réponse d'inscription."""

    id: str
    email: str
    message: str = "Inscription réussie. Un administrateur doit vérifier votre email avant que vous puissiez vous connecter."


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
    facebook: str | None = None
    biography: str | None = None
    city: str | None = None
    address: str | None = None


class UserCreate(UserBase):
    """Création d'utilisateur."""

    password: str = Field(min_length=8)
    photo_external_id: str | None = None


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
    facebook: str | None = None
    biography: str | None = None
    city: str | None = None
    address: str | None = None
    active: bool | None = None
    photo_external_id: str | None = None


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
    facebook: str | None = None
    biography: str | None = None
    city: str | None = None
    address: str | None = None
    photo_external_id: str | None = None
    nationality_external_id: str | None = None


# =============================================================================
# Admin Schemas - Users
# =============================================================================


class UserRolesUpdate(BaseModel):
    """Mise à jour des rôles d'un utilisateur."""

    role_ids: list[str]


class UserBulkAction(BaseModel):
    """Action en masse sur les utilisateurs."""

    user_ids: list[str]
    action: str = Field(pattern="^(activate|deactivate|delete)$")


class UserActivity(BaseModel):
    """Activité d'un utilisateur."""

    last_login_at: datetime | None
    created_at: datetime
    roles: list[str]
    total_logins: int = 0

    model_config = {"from_attributes": True}


class PasswordResetResponse(BaseModel):
    """Réponse de réinitialisation de mot de passe."""

    temporary_password: str
    message: str = "Mot de passe réinitialisé avec succès"


# =============================================================================
# Admin Schemas - Roles
# =============================================================================


class RoleCreate(BaseModel):
    """Création d'un rôle."""

    code: str = Field(min_length=2, max_length=50)
    name_fr: str = Field(min_length=2, max_length=100)
    description: str | None = None
    hierarchy_level: int = Field(default=0, ge=0, le=100)
    active: bool = True


class RoleUpdate(BaseModel):
    """Mise à jour d'un rôle."""

    code: str | None = Field(default=None, min_length=2, max_length=50)
    name_fr: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    hierarchy_level: int | None = Field(default=None, ge=0, le=100)
    active: bool | None = None


class RoleDuplicate(BaseModel):
    """Duplication d'un rôle."""

    new_code: str = Field(min_length=2, max_length=50)
    new_name: str = Field(min_length=2, max_length=100)


class RolePermissionsUpdate(BaseModel):
    """Mise à jour des permissions d'un rôle."""

    permission_ids: list[str]


class RoleCompare(BaseModel):
    """Comparaison de rôles."""

    role_ids: list[str] = Field(min_length=2, max_length=5)


# =============================================================================
# Admin Schemas - Permissions
# =============================================================================


class PermissionCreate(BaseModel):
    """Création d'une permission."""

    code: str = Field(min_length=2, max_length=50)
    name_fr: str = Field(min_length=2, max_length=100)
    description: str | None = None
    category: str | None = Field(default=None, max_length=50)


class PermissionUpdate(BaseModel):
    """Mise à jour d'une permission."""

    code: str | None = Field(default=None, min_length=2, max_length=50)
    name_fr: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    category: str | None = Field(default=None, max_length=50)


class PermissionMatrix(BaseModel):
    """Matrice des permissions."""

    permissions: dict
    roles: list[dict]


class PermissionMatrixUpdate(BaseModel):
    """Mise à jour de la matrice des permissions."""

    updates: list[dict]  # [{role_id, permission_id, granted}]


# =============================================================================
# Admin Schemas - Audit Logs
# =============================================================================


class AuditLogRead(BaseModel):
    """Log d'audit en lecture."""

    id: str
    user_id: str | None
    action: str
    table_name: str | None
    record_id: str | None
    old_values: dict | None
    new_values: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("ip_address", mode="before")
    @classmethod
    def convert_ip_to_string(cls, v):
        """Convertit l'adresse IP PostgreSQL INET en string."""
        if v is None:
            return None
        return str(v)


class AuditLogUserStat(BaseModel):
    """Statistique par utilisateur."""

    user_id: str
    count: int


class AuditLogDayStat(BaseModel):
    """Statistique par jour."""

    date: str
    count: int


class AuditLogStatistics(BaseModel):
    """Statistiques des logs d'audit."""

    total: int
    by_action: dict[str, int]
    by_table: dict[str, int]
    by_user: list[AuditLogUserStat] = []
    by_day: list[AuditLogDayStat] = []


class AuditLogPurge(BaseModel):
    """Requête de purge des logs d'audit."""

    before_date: datetime
