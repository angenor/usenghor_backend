"""
Tests unitaires - IdentityService
=================================

Tests du service de gestion des identités.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import User, Role, Permission
from app.services.identity_service import IdentityService
from app.core.exceptions import ConflictException, NotFoundException


class TestIdentityServiceUsers:
    """Tests pour la gestion des utilisateurs."""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """Test de création d'un utilisateur."""
        service = IdentityService(db_session)

        user = await service.create_user(
            email="nouveau@usenghor.org",
            password="SecurePassword123!",
            last_name="Dupont",
            first_name="Jean",
        )

        assert user is not None
        assert user.email == "nouveau@usenghor.org"
        assert user.last_name == "Dupont"
        assert user.first_name == "Jean"
        assert user.active is True
        assert user.hashed_password is not None
        assert user.hashed_password != "SecurePassword123!"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test de création avec email en doublon."""
        service = IdentityService(db_session)

        with pytest.raises(ConflictException):
            await service.create_user(
                email=test_user.email,  # Email déjà utilisé
                password="AnotherPassword123!",
                last_name="Autre",
                first_name="Personne",
            )

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, db_session: AsyncSession, test_user: User):
        """Test de récupération d'un utilisateur par ID."""
        service = IdentityService(db_session)

        user = await service.get_user_by_id(test_user.id)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, db_session: AsyncSession):
        """Test de récupération d'un utilisateur inexistant."""
        service = IdentityService(db_session)

        user = await service.get_user_by_id("id-inexistant")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db_session: AsyncSession, test_user: User):
        """Test de récupération d'un utilisateur par email."""
        service = IdentityService(db_session)

        user = await service.get_user_by_email(test_user.email)

        assert user is not None
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_users_with_search(
        self, db_session: AsyncSession, sample_users: list[User]
    ):
        """Test de recherche d'utilisateurs."""
        service = IdentityService(db_session)

        # Recherche par nom
        query = await service.get_users(search="Nom0")
        result = await db_session.execute(query)
        users = result.scalars().all()

        assert len(users) == 1
        assert users[0].last_name == "Nom0"

    @pytest.mark.asyncio
    async def test_get_users_filter_active(
        self, db_session: AsyncSession, sample_users: list[User]
    ):
        """Test de filtrage des utilisateurs actifs."""
        service = IdentityService(db_session)

        # Filtrer les utilisateurs actifs
        query = await service.get_users(active=True)
        result = await db_session.execute(query)
        users = result.scalars().all()

        # 3 utilisateurs sur 5 sont actifs (indices 0, 2, 4)
        assert len(users) == 3
        assert all(u.active for u in users)

    @pytest.mark.asyncio
    async def test_update_user(self, db_session: AsyncSession, test_user: User):
        """Test de mise à jour d'un utilisateur."""
        service = IdentityService(db_session)

        updated = await service.update_user(
            test_user.id,
            last_name="NouveauNom",
            first_name="NouveauPrenom",
        )

        assert updated is not None
        assert updated.last_name == "NouveauNom"
        assert updated.first_name == "NouveauPrenom"
        # L'email ne doit pas changer
        assert updated.email == test_user.email

    @pytest.mark.asyncio
    async def test_deactivate_user(self, db_session: AsyncSession, test_user: User):
        """Test de désactivation d'un utilisateur."""
        service = IdentityService(db_session)

        result = await service.deactivate_user(test_user.id)

        assert result is True

        # Vérifier que l'utilisateur est désactivé
        user = await service.get_user_by_id(test_user.id)
        assert user.active is False


class TestIdentityServiceRoles:
    """Tests pour la gestion des rôles."""

    @pytest.mark.asyncio
    async def test_create_role(self, db_session: AsyncSession):
        """Test de création d'un rôle."""
        service = IdentityService(db_session)

        role = await service.create_role(
            name="Éditeur",
            code="editor",
            description="Rôle pour les éditeurs de contenu",
        )

        assert role is not None
        assert role.name == "Éditeur"
        assert role.code == "editor"

    @pytest.mark.asyncio
    async def test_create_role_duplicate_code(
        self, db_session: AsyncSession, admin_role: Role
    ):
        """Test de création avec code en doublon."""
        service = IdentityService(db_session)

        with pytest.raises(ConflictException):
            await service.create_role(
                name="Autre Admin",
                code=admin_role.code,  # Code déjà utilisé
                description="Description",
            )

    @pytest.mark.asyncio
    async def test_get_roles(self, db_session: AsyncSession, admin_role: Role):
        """Test de récupération de tous les rôles."""
        service = IdentityService(db_session)

        query = await service.get_roles()
        result = await db_session.execute(query)
        roles = result.scalars().all()

        assert len(roles) >= 1
        assert any(r.code == "admin" for r in roles)

    @pytest.mark.asyncio
    async def test_assign_permissions_to_role(
        self, db_session: AsyncSession, test_permissions: list[Permission]
    ):
        """Test d'assignation de permissions à un rôle."""
        service = IdentityService(db_session)

        # Créer un nouveau rôle
        role = await service.create_role(
            name="Test Role",
            code="test_role",
            description="Rôle de test",
        )

        # Assigner quelques permissions
        permission_ids = [test_permissions[0].id, test_permissions[1].id]
        await service.set_role_permissions(role.id, permission_ids)

        # Vérifier les permissions du rôle
        updated_role = await service.get_role_by_id(role.id)
        assert len(updated_role.permissions) == 2


class TestIdentityServiceAuthentication:
    """Tests pour l'authentification."""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test d'authentification réussie."""
        service = IdentityService(db_session)

        user = await service.authenticate_user(
            email=test_user.email,
            password="TestPassword123!",
        )

        assert user is not None
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test d'authentification avec mauvais mot de passe."""
        service = IdentityService(db_session)

        user = await service.authenticate_user(
            email=test_user.email,
            password="WrongPassword!",
        )

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, db_session: AsyncSession):
        """Test d'authentification avec email inexistant."""
        service = IdentityService(db_session)

        user = await service.authenticate_user(
            email="inexistant@usenghor.org",
            password="Password123!",
        )

        assert user is None
