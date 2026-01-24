"""
Configuration des tests
=======================

Fixtures pytest pour les tests unitaires et d'intégration.
Utilise PostgreSQL pour une compatibilité complète avec la production.
"""

import os
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.core.security import get_password_hash, create_access_token


# ============================================================================
# Configuration de la base de données de test PostgreSQL
# ============================================================================

# URL de la base de données de test
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://usenghor:usenghor_secret@localhost:5432/usenghor_test"
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Crée une session de base de données pour chaque test.

    Chaque test obtient une session fraîche avec nettoyage automatique
    des données après le test pour assurer l'isolation.
    """
    # Import des modèles pour que Base.metadata soit peuplé
    from app import models  # noqa: F401

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Créer les tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()

    # Nettoyer les données après le test
    async with async_session() as cleanup_session:
        async with cleanup_session.begin():
            # Supprimer dans l'ordre inverse des dépendances FK
            for table in reversed(Base.metadata.sorted_tables):
                await cleanup_session.execute(table.delete())

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Crée un client HTTP pour les tests d'intégration."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================================================
# Fixtures de données de test
# ============================================================================

@pytest_asyncio.fixture
async def test_permissions(db_session: AsyncSession) -> list[Permission]:
    """Crée des permissions de test."""
    permissions_data = [
        ("users.view", "Voir les utilisateurs"),
        ("users.create", "Créer des utilisateurs"),
        ("users.edit", "Modifier les utilisateurs"),
        ("users.delete", "Supprimer des utilisateurs"),
        ("dashboard.view", "Voir le tableau de bord"),
        ("admin.audit", "Accès aux logs d'audit"),
        ("admin.settings", "Paramètres admin"),
        ("news.view", "Voir les actualités"),
        ("news.create", "Créer des actualités"),
    ]

    permissions = []
    for code, name_fr in permissions_data:
        permission = Permission(
            id=str(uuid4()),
            code=code,
            name_fr=name_fr,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(permission)
        permissions.append(permission)

    await db_session.commit()
    return permissions


@pytest_asyncio.fixture
async def admin_role(db_session: AsyncSession, test_permissions: list[Permission]) -> Role:
    """Crée un rôle admin avec toutes les permissions."""
    role = Role(
        id=str(uuid4()),
        name_fr="Admin",
        code="admin",
        description="Administrateur avec tous les droits",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(role)
    await db_session.flush()

    # Associer toutes les permissions au rôle
    for permission in test_permissions:
        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
        )
        db_session.add(role_permission)

    await db_session.commit()

    # Recharger le rôle avec ses permissions
    await db_session.refresh(role)
    return role


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, admin_role: Role) -> User:
    """Crée un utilisateur de test avec le rôle admin."""
    user = User(
        id=str(uuid4()),
        email="test@usenghor.org",
        password_hash=get_password_hash("TestPass123!"),
        last_name="Test",
        first_name="User",
        active=True,
        email_verified=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.flush()

    # Associer le rôle admin à l'utilisateur
    user_role = UserRole(
        user_id=user.id,
        role_id=admin_role.id,
    )
    db_session.add(user_role)

    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    """Crée des en-têtes d'authentification pour les tests."""
    token = create_access_token({"sub": test_user.id, "type": "access"})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def authenticated_client(
    client: AsyncClient,
    auth_headers: dict[str, str]
) -> AsyncClient:
    """Client HTTP avec authentification."""
    client.headers.update(auth_headers)
    return client


# ============================================================================
# Fixtures pour données de test additionnelles
# ============================================================================

@pytest_asyncio.fixture
async def sample_users(db_session: AsyncSession, admin_role: Role) -> list[User]:
    """Crée plusieurs utilisateurs de test."""
    users = []
    for i in range(5):
        user = User(
            id=str(uuid4()),
            email=f"user{i}@usenghor.org",
            password_hash=get_password_hash("Pass123!"),
            last_name=f"Nom{i}",
            first_name=f"Prenom{i}",
            active=i % 2 == 0,  # Un sur deux actif
            email_verified=True,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        users.append(user)

    await db_session.flush()

    # Associer le rôle admin au premier utilisateur
    user_role = UserRole(
        user_id=users[0].id,
        role_id=admin_role.id,
    )
    db_session.add(user_role)

    await db_session.commit()
    return users
