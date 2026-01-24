"""
Tests d'intégration - Utilisateurs
==================================

Tests des endpoints de gestion des utilisateurs.
"""

import pytest
from httpx import AsyncClient

from app.models.identity import User


class TestUsersEndpoints:
    """Tests pour les endpoints utilisateurs."""

    @pytest.mark.asyncio
    async def test_list_users(
        self, authenticated_client: AsyncClient, sample_users: list[User]
    ):
        """Test de liste des utilisateurs."""
        response = await authenticated_client.get("/api/admin/users")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 5  # Au moins les 5 sample_users

    @pytest.mark.asyncio
    async def test_list_users_with_pagination(
        self, authenticated_client: AsyncClient, sample_users: list[User]
    ):
        """Test de pagination des utilisateurs."""
        response = await authenticated_client.get(
            "/api/admin/users",
            params={"page": 1, "limit": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["limit"] == 2

    @pytest.mark.asyncio
    async def test_list_users_with_search(
        self, authenticated_client: AsyncClient, sample_users: list[User]
    ):
        """Test de recherche d'utilisateurs."""
        response = await authenticated_client.get(
            "/api/admin/users",
            params={"search": "Nom0"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_users_filter_active(
        self, authenticated_client: AsyncClient, sample_users: list[User]
    ):
        """Test de filtrage par statut actif."""
        response = await authenticated_client.get(
            "/api/admin/users",
            params={"active": True},
        )

        assert response.status_code == 200
        data = response.json()
        # Tous les utilisateurs retournés doivent être actifs
        for user in data["items"]:
            assert user["active"] is True

    @pytest.mark.asyncio
    async def test_get_user(self, authenticated_client: AsyncClient, test_user: User):
        """Test de récupération d'un utilisateur."""
        response = await authenticated_client.get(f"/api/admin/users/{test_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, authenticated_client: AsyncClient):
        """Test de récupération d'un utilisateur inexistant."""
        # Utiliser un UUID valide mais inexistant
        non_existent_uuid = "00000000-0000-0000-0000-000000000000"
        response = await authenticated_client.get(f"/api/admin/users/{non_existent_uuid}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_user(self, authenticated_client: AsyncClient):
        """Test de création d'un utilisateur."""
        response = await authenticated_client.post(
            "/api/admin/users",
            json={
                "email": "nouveau.user@usenghor.org",
                "password": "SecurePassword123!",
                "last_name": "Nouveau",
                "first_name": "Utilisateur",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test de création avec email en doublon."""
        response = await authenticated_client.post(
            "/api/admin/users",
            json={
                "email": test_user.email,  # Email déjà utilisé
                "password": "SecurePassword123!",
                "last_name": "Doublon",
                "first_name": "Test",
            },
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_user(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test de mise à jour d'un utilisateur."""
        response = await authenticated_client.put(
            f"/api/admin/users/{test_user.id}",
            json={
                "last_name": "NomModifié",
                "first_name": "PrénomModifié",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["last_name"] == "NomModifié"
        assert data["first_name"] == "PrénomModifié"

    @pytest.mark.asyncio
    async def test_delete_user(
        self, authenticated_client: AsyncClient, sample_users: list[User]
    ):
        """Test de suppression d'un utilisateur."""
        user_to_delete = sample_users[-1]  # Dernier utilisateur

        response = await authenticated_client.delete(
            f"/api/admin/users/{user_to_delete.id}"
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_users_unauthorized(self, client: AsyncClient):
        """Test sans authentification."""
        response = await client.get("/api/admin/users")

        assert response.status_code == 401
