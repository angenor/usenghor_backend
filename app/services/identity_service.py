"""
Service Identity
=================

Logique métier pour la gestion des utilisateurs, rôles et permissions.
"""

import secrets
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import get_password_hash
from app.models.identity import (
    AuditLog,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
    UserToken,
)


class IdentityService:
    """Service pour la gestion des identités."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # USERS
    # =========================================================================

    async def get_users(
        self,
        search: str | None = None,
        active: bool | None = None,
        role_id: str | None = None,
    ) -> select:
        """
        Construit une requête pour lister les utilisateurs.

        Args:
            search: Recherche sur email, nom, prénom.
            active: Filtrer par statut actif.
            role_id: Filtrer par rôle.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(User).options(selectinload(User.roles))

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    User.email.ilike(search_filter),
                    User.last_name.ilike(search_filter),
                    User.first_name.ilike(search_filter),
                )
            )

        if active is not None:
            query = query.where(User.active == active)

        if role_id:
            query = query.join(User.roles).where(Role.id == role_id)

        return query

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Récupère un utilisateur par son ID."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Récupère un utilisateur par son email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password: str,
        last_name: str,
        first_name: str,
        **kwargs,
    ) -> User:
        """
        Crée un nouvel utilisateur.

        Args:
            email: Email de l'utilisateur.
            password: Mot de passe en clair.
            last_name: Nom de famille.
            first_name: Prénom.
            **kwargs: Autres champs optionnels.

        Returns:
            Utilisateur créé.

        Raises:
            ConflictException: Si l'email existe déjà.
        """
        existing = await self.get_user_by_email(email)
        if existing:
            raise ConflictException("Un utilisateur avec cet email existe déjà")

        user = User(
            id=str(uuid4()),
            email=email,
            password_hash=get_password_hash(password),
            last_name=last_name,
            first_name=first_name,
            **kwargs,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_user(self, user_id: str, **kwargs) -> User:
        """
        Met à jour un utilisateur.

        Args:
            user_id: ID de l'utilisateur.
            **kwargs: Champs à mettre à jour.

        Returns:
            Utilisateur mis à jour.

        Raises:
            NotFoundException: Si l'utilisateur n'existe pas.
            ConflictException: Si le nouvel email existe déjà.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("Utilisateur non trouvé")

        # Vérifier l'unicité de l'email si modifié
        if "email" in kwargs and kwargs["email"] != user.email:
            existing = await self.get_user_by_email(kwargs["email"])
            if existing:
                raise ConflictException("Un utilisateur avec cet email existe déjà")

        await self.db.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_user_by_id(user_id)

    async def delete_user(self, user_id: str) -> None:
        """
        Supprime un utilisateur.

        Args:
            user_id: ID de l'utilisateur.

        Raises:
            NotFoundException: Si l'utilisateur n'existe pas.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("Utilisateur non trouvé")

        await self.db.execute(delete(User).where(User.id == user_id))

    async def toggle_user_active(self, user_id: str) -> User:
        """Bascule le statut actif d'un utilisateur."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("Utilisateur non trouvé")

        await self.db.execute(
            update(User).where(User.id == user_id).values(active=not user.active)
        )
        await self.db.flush()
        return await self.get_user_by_id(user_id)

    async def set_user_roles(
        self,
        user_id: str,
        role_ids: list[str],
        assigned_by: str | None = None,
    ) -> User:
        """
        Définit les rôles d'un utilisateur.

        Args:
            user_id: ID de l'utilisateur.
            role_ids: Liste des IDs de rôles.
            assigned_by: ID de l'utilisateur qui assigne.

        Returns:
            Utilisateur avec ses nouveaux rôles.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("Utilisateur non trouvé")

        # Supprimer les rôles existants
        await self.db.execute(delete(UserRole).where(UserRole.user_id == user_id))

        # Ajouter les nouveaux rôles
        for role_id in role_ids:
            role = await self.get_role_by_id(role_id)
            if not role:
                raise NotFoundException(f"Rôle {role_id} non trouvé")

            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by=assigned_by,
            )
            self.db.add(user_role)

        await self.db.flush()
        return await self.get_user_by_id(user_id)

    async def reset_user_password(self, user_id: str) -> str:
        """
        Réinitialise le mot de passe d'un utilisateur.

        Args:
            user_id: ID de l'utilisateur.

        Returns:
            Nouveau mot de passe temporaire.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("Utilisateur non trouvé")

        new_password = secrets.token_urlsafe(12)
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=get_password_hash(new_password))
        )
        return new_password

    async def verify_user_email(self, user_id: str) -> User:
        """Marque l'email d'un utilisateur comme vérifié."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("Utilisateur non trouvé")

        await self.db.execute(
            update(User).where(User.id == user_id).values(email_verified=True)
        )
        await self.db.flush()
        return await self.get_user_by_id(user_id)

    async def anonymize_user(self, user_id: str) -> User:
        """
        Anonymise un utilisateur (RGPD).

        Args:
            user_id: ID de l'utilisateur.

        Returns:
            Utilisateur anonymisé.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("Utilisateur non trouvé")

        anonymized_data = {
            "email": f"anonymized_{user_id}@deleted.local",
            "last_name": "ANONYMISÉ",
            "first_name": "Utilisateur",
            "password_hash": None,
            "phone": None,
            "phone_whatsapp": None,
            "linkedin": None,
            "city": None,
            "address": None,
            "birth_date": None,
            "active": False,
        }
        await self.db.execute(
            update(User).where(User.id == user_id).values(**anonymized_data)
        )
        await self.db.flush()
        return await self.get_user_by_id(user_id)

    async def get_user_permissions(self, user_id: str) -> list[str]:
        """Récupère la liste des permissions d'un utilisateur."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("Utilisateur non trouvé")

        permissions = set()
        for role in user.roles:
            if role.code == "super_admin":
                # Super admin: récupérer toutes les permissions
                result = await self.db.execute(select(Permission.code))
                return list(result.scalars().all())
            for perm in role.permissions:
                permissions.add(perm.code)
        return list(permissions)

    # =========================================================================
    # ROLES
    # =========================================================================

    async def get_roles(
        self,
        search: str | None = None,
        active: bool | None = None,
    ) -> select:
        """Construit une requête pour lister les rôles."""
        query = select(Role).options(selectinload(Role.permissions))

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Role.code.ilike(search_filter),
                    Role.name_fr.ilike(search_filter),
                )
            )

        if active is not None:
            query = query.where(Role.active == active)

        return query

    async def get_role_by_id(self, role_id: str) -> Role | None:
        """Récupère un rôle par son ID."""
        result = await self.db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    async def get_role_by_code(self, code: str) -> Role | None:
        """Récupère un rôle par son code."""
        result = await self.db.execute(select(Role).where(Role.code == code))
        return result.scalar_one_or_none()

    async def create_role(
        self,
        code: str,
        name_fr: str,
        description: str | None = None,
        hierarchy_level: int = 0,
        active: bool = True,
    ) -> Role:
        """Crée un nouveau rôle."""
        existing = await self.get_role_by_code(code)
        if existing:
            raise ConflictException("Un rôle avec ce code existe déjà")

        role = Role(
            id=str(uuid4()),
            code=code,
            name_fr=name_fr,
            description=description,
            hierarchy_level=hierarchy_level,
            active=active,
        )
        self.db.add(role)
        await self.db.flush()
        return role

    async def update_role(self, role_id: str, **kwargs) -> Role:
        """Met à jour un rôle."""
        role = await self.get_role_by_id(role_id)
        if not role:
            raise NotFoundException("Rôle non trouvé")

        # Vérifier l'unicité du code si modifié
        if "code" in kwargs and kwargs["code"] != role.code:
            existing = await self.get_role_by_code(kwargs["code"])
            if existing:
                raise ConflictException("Un rôle avec ce code existe déjà")

        await self.db.execute(
            update(Role).where(Role.id == role_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_role_by_id(role_id)

    async def delete_role(self, role_id: str) -> None:
        """Supprime un rôle."""
        role = await self.get_role_by_id(role_id)
        if not role:
            raise NotFoundException("Rôle non trouvé")

        # Empêcher la suppression des rôles système
        if role.code in ("super_admin", "admin", "user"):
            raise ConflictException("Impossible de supprimer un rôle système")

        await self.db.execute(delete(Role).where(Role.id == role_id))

    async def toggle_role_active(self, role_id: str) -> Role:
        """Bascule le statut actif d'un rôle."""
        role = await self.get_role_by_id(role_id)
        if not role:
            raise NotFoundException("Rôle non trouvé")

        await self.db.execute(
            update(Role).where(Role.id == role_id).values(active=not role.active)
        )
        await self.db.flush()
        return await self.get_role_by_id(role_id)

    async def duplicate_role(self, role_id: str, new_code: str, new_name: str) -> Role:
        """Duplique un rôle avec ses permissions."""
        role = await self.get_role_by_id(role_id)
        if not role:
            raise NotFoundException("Rôle non trouvé")

        existing = await self.get_role_by_code(new_code)
        if existing:
            raise ConflictException("Un rôle avec ce code existe déjà")

        # Créer le nouveau rôle
        new_role = Role(
            id=str(uuid4()),
            code=new_code,
            name_fr=new_name,
            description=role.description,
            hierarchy_level=role.hierarchy_level,
            active=True,
        )
        self.db.add(new_role)
        await self.db.flush()

        # Copier les permissions
        for perm in role.permissions:
            role_perm = RolePermission(role_id=new_role.id, permission_id=perm.id)
            self.db.add(role_perm)

        await self.db.flush()
        return await self.get_role_by_id(new_role.id)

    async def set_role_permissions(
        self, role_id: str, permission_ids: list[str]
    ) -> Role:
        """Définit les permissions d'un rôle."""
        role = await self.get_role_by_id(role_id)
        if not role:
            raise NotFoundException("Rôle non trouvé")

        # Supprimer les permissions existantes
        await self.db.execute(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )

        # Ajouter les nouvelles permissions
        for perm_id in permission_ids:
            perm = await self.get_permission_by_id(perm_id)
            if not perm:
                raise NotFoundException(f"Permission {perm_id} non trouvée")

            role_perm = RolePermission(role_id=role_id, permission_id=perm_id)
            self.db.add(role_perm)

        await self.db.flush()
        # Expirer le rôle pour forcer le rechargement des relations
        await self.db.refresh(role, ["permissions"])
        return role

    async def get_role_users(self, role_id: str) -> list[User]:
        """Récupère les utilisateurs ayant un rôle."""
        role = await self.get_role_by_id(role_id)
        if not role:
            raise NotFoundException("Rôle non trouvé")

        result = await self.db.execute(
            select(User).join(User.roles).where(Role.id == role_id)
        )
        return list(result.scalars().all())

    # =========================================================================
    # PERMISSIONS
    # =========================================================================

    async def get_permissions(
        self,
        search: str | None = None,
        category: str | None = None,
    ) -> select:
        """Construit une requête pour lister les permissions."""
        query = select(Permission)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Permission.code.ilike(search_filter),
                    Permission.name_fr.ilike(search_filter),
                )
            )

        if category:
            query = query.where(Permission.category == category)

        return query

    async def get_permission_by_id(self, permission_id: str) -> Permission | None:
        """Récupère une permission par son ID."""
        result = await self.db.execute(
            select(Permission).where(Permission.id == permission_id)
        )
        return result.scalar_one_or_none()

    async def get_permission_by_code(self, code: str) -> Permission | None:
        """Récupère une permission par son code."""
        result = await self.db.execute(
            select(Permission).where(Permission.code == code)
        )
        return result.scalar_one_or_none()

    async def create_permission(
        self,
        code: str,
        name_fr: str,
        description: str | None = None,
        category: str | None = None,
    ) -> Permission:
        """Crée une nouvelle permission."""
        existing = await self.get_permission_by_code(code)
        if existing:
            raise ConflictException("Une permission avec ce code existe déjà")

        permission = Permission(
            id=str(uuid4()),
            code=code,
            name_fr=name_fr,
            description=description,
            category=category,
        )
        self.db.add(permission)
        await self.db.flush()
        return permission

    async def update_permission(self, permission_id: str, **kwargs) -> Permission:
        """Met à jour une permission."""
        perm = await self.get_permission_by_id(permission_id)
        if not perm:
            raise NotFoundException("Permission non trouvée")

        # Vérifier l'unicité du code si modifié
        if "code" in kwargs and kwargs["code"] != perm.code:
            existing = await self.get_permission_by_code(kwargs["code"])
            if existing:
                raise ConflictException("Une permission avec ce code existe déjà")

        await self.db.execute(
            update(Permission).where(Permission.id == permission_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_permission_by_id(permission_id)

    async def delete_permission(self, permission_id: str) -> None:
        """Supprime une permission."""
        perm = await self.get_permission_by_id(permission_id)
        if not perm:
            raise NotFoundException("Permission non trouvée")

        await self.db.execute(
            delete(Permission).where(Permission.id == permission_id)
        )

    async def get_permission_roles(self, permission_id: str) -> list[Role]:
        """Récupère les rôles ayant une permission."""
        perm = await self.get_permission_by_id(permission_id)
        if not perm:
            raise NotFoundException("Permission non trouvée")

        result = await self.db.execute(
            select(Role).join(Role.permissions).where(Permission.id == permission_id)
        )
        return list(result.scalars().all())

    async def get_permissions_matrix(self) -> dict:
        """Récupère la matrice permissions/rôles."""
        roles = await self.db.execute(
            select(Role).options(selectinload(Role.permissions)).order_by(Role.hierarchy_level.desc())
        )
        roles = list(roles.scalars().all())

        permissions = await self.db.execute(
            select(Permission).order_by(Permission.category, Permission.code)
        )
        permissions = list(permissions.scalars().all())

        matrix = {}
        for perm in permissions:
            matrix[perm.code] = {
                "id": perm.id,
                "name_fr": perm.name_fr,
                "category": perm.category,
                "roles": {},
            }
            for role in roles:
                has_perm = any(p.id == perm.id for p in role.permissions)
                matrix[perm.code]["roles"][role.code] = has_perm

        return {
            "permissions": matrix,
            "roles": [
                {"id": r.id, "code": r.code, "name_fr": r.name_fr}
                for r in roles
            ],
        }

    # =========================================================================
    # AUDIT LOGS
    # =========================================================================

    async def get_audit_logs(
        self,
        user_id: str | None = None,
        table_name: str | None = None,
        record_id: str | None = None,
        action: str | None = None,
    ) -> select:
        """Construit une requête pour lister les logs d'audit."""
        query = select(AuditLog)

        if user_id:
            query = query.where(AuditLog.user_id == user_id)

        if table_name:
            query = query.where(AuditLog.table_name == table_name)

        if record_id:
            query = query.where(AuditLog.record_id == record_id)

        if action:
            query = query.where(AuditLog.action == action)

        return query

    async def get_audit_log_by_id(self, log_id: str) -> AuditLog | None:
        """Récupère un log d'audit par son ID."""
        result = await self.db.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def create_audit_log(
        self,
        action: str,
        user_id: str | None = None,
        table_name: str | None = None,
        record_id: str | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Crée une entrée de log d'audit."""
        log = AuditLog(
            id=str(uuid4()),
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_audit_statistics(self) -> dict:
        """Récupère les statistiques des logs d'audit."""
        # Total par action
        actions_result = await self.db.execute(
            select(AuditLog.action, func.count(AuditLog.id))
            .group_by(AuditLog.action)
        )
        actions = dict(actions_result.all())

        # Total par table
        tables_result = await self.db.execute(
            select(AuditLog.table_name, func.count(AuditLog.id))
            .where(AuditLog.table_name.isnot(None))
            .group_by(AuditLog.table_name)
        )
        tables = dict(tables_result.all())

        # Total
        total_result = await self.db.execute(select(func.count(AuditLog.id)))
        total = total_result.scalar() or 0

        return {
            "total": total,
            "by_action": actions,
            "by_table": tables,
        }

    async def purge_audit_logs(self, before_date: datetime) -> int:
        """
        Purge les logs d'audit avant une date.

        Args:
            before_date: Date limite.

        Returns:
            Nombre de logs supprimés.
        """
        result = await self.db.execute(
            delete(AuditLog).where(AuditLog.created_at < before_date)
        )
        return result.rowcount
