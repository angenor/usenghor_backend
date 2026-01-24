"""
Tests d'intégration - Authentification
======================================

Tests des endpoints d'authentification.
"""

import pytest
from httpx import AsyncClient

from app.models.identity import User


class TestAuthLogin:
    """Tests pour l'endpoint de connexion."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test de connexion réussie."""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPass123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test de connexion avec mauvais mot de passe."""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "WrongPassword!",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_user(self, client: AsyncClient):
        """Test de connexion avec utilisateur inconnu."""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "inconnu@usenghor.org",
                "password": "Password123!",
            },
        )

        assert response.status_code == 401


class TestAuthRefresh:
    """Tests pour le rafraîchissement de token."""

    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, test_user: User):
        """Test de rafraîchissement de token."""
        # D'abord se connecter pour obtenir un refresh token
        login_response = await client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPass123!",
            },
        )
        tokens = login_response.json()

        # Utiliser le refresh token
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test de rafraîchissement avec token invalide."""
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401


class TestAuthMe:
    """Tests pour l'endpoint /me."""

    @pytest.mark.asyncio
    async def test_get_current_user(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test de récupération de l'utilisateur courant."""
        response = await authenticated_client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["last_name"] == test_user.last_name

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test sans authentification."""
        response = await client.get("/api/auth/me")

        assert response.status_code == 401


class TestAuthLogout:
    """Tests pour la déconnexion."""

    @pytest.mark.asyncio
    async def test_logout(self, authenticated_client: AsyncClient):
        """Test de déconnexion."""
        response = await authenticated_client.post("/api/auth/logout")

        assert response.status_code == 200
