"""
Modèles Identity
================

Modèles SQLAlchemy pour l'authentification et les utilisateurs.
Tables: permissions, roles, role_permissions, users, user_roles, user_tokens, audit_logs
"""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import Salutation, TimestampMixin, UUIDMixin


class Permission(Base, UUIDMixin):
    """Permissions (actions possibles)."""

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relations
    roles: Mapped[list["Role"]] = relationship(
        secondary="role_permissions", back_populates="permissions"
    )


class Role(Base, UUIDMixin, TimestampMixin):
    """Rôles."""

    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    hierarchy_level: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relations
    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permissions", back_populates="roles"
    )
    users: Mapped[list["User"]] = relationship(
        secondary="user_roles",
        back_populates="roles",
        primaryjoin="Role.id == UserRole.role_id",
        secondaryjoin="User.id == UserRole.user_id",
    )


class RolePermission(Base):
    """Relation rôles <-> permissions."""

    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )


class User(Base, UUIDMixin, TimestampMixin):
    """Utilisateurs."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    salutation: Mapped[Salutation | None] = mapped_column(Enum(Salutation))
    birth_date: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(30))
    phone_whatsapp: Mapped[str | None] = mapped_column(String(30))
    linkedin: Mapped[str | None] = mapped_column(String(255))

    # Références INTER-SERVICE (pas de FK)
    photo_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    nationality_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    residence_country_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))

    city: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)

    active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relations
    roles: Mapped[list["Role"]] = relationship(
        secondary="user_roles",
        back_populates="users",
        primaryjoin="User.id == UserRole.user_id",
        secondaryjoin="Role.id == UserRole.role_id",
    )
    tokens: Mapped[list["UserToken"]] = relationship(back_populates="user")

    @property
    def full_name(self) -> str:
        """Retourne le nom complet de l'utilisateur."""
        return f"{self.first_name} {self.last_name}"

    def has_permission(self, permission_code: str) -> bool:
        """Vérifie si l'utilisateur a une permission spécifique."""
        for role in self.roles:
            # Super admin a toutes les permissions
            if role.code == "super_admin":
                return True
            for perm in role.permissions:
                if perm.code == permission_code:
                    return True
        return False

    def has_role(self, role_code: str) -> bool:
        """Vérifie si l'utilisateur a un rôle spécifique."""
        return any(role.code == role_code for role in self.roles)

    @property
    def highest_role_level(self) -> int:
        """Retourne le niveau de hiérarchie le plus élevé parmi les rôles."""
        if not self.roles:
            return 0
        return max(role.hierarchy_level for role in self.roles)


class UserRole(Base):
    """Relation utilisateurs <-> rôles."""

    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    campus_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    assigned_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id")
    )


class UserToken(Base, UUIDMixin):
    """Tokens de réinitialisation et vérification."""

    __tablename__ = "user_tokens"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # email_verification, password_reset
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relations
    user: Mapped["User"] = relationship(back_populates="tokens")


class AuditLog(Base, UUIDMixin):
    """Audit et logs."""

    __tablename__ = "audit_logs"

    user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    table_name: Mapped[str | None] = mapped_column(String(100))
    record_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    old_values: Mapped[dict | None] = mapped_column(JSONB)
    new_values: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
