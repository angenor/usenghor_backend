"""
Tests d'intégration - Dashboard
===============================

Tests des endpoints du tableau de bord.
"""

import pytest
from httpx import AsyncClient

from app.models.identity import User


class TestDashboardEndpoints:
    """Tests pour les endpoints du dashboard."""

    @pytest.mark.asyncio
    async def test_get_global_stats(
        self, authenticated_client: AsyncClient, sample_users: list[User]
    ):
        """Test de récupération des statistiques globales."""
        response = await authenticated_client.get("/api/admin/dashboard/stats")

        assert response.status_code == 200
        data = response.json()

        # Vérifier la structure des statistiques
        assert "users" in data
        assert "news" in data
        assert "events" in data
        assert "applications" in data

        # Vérifier les compteurs utilisateurs
        assert "total" in data["users"]
        assert "active" in data["users"]
        assert "inactive" in data["users"]

    @pytest.mark.asyncio
    async def test_get_recent_activity(self, authenticated_client: AsyncClient):
        """Test de récupération de l'activité récente."""
        response = await authenticated_client.get("/api/admin/dashboard/recent-activity")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_get_recent_activity_with_limit(
        self, authenticated_client: AsyncClient
    ):
        """Test de l'activité récente avec limite."""
        response = await authenticated_client.get(
            "/api/admin/dashboard/recent-activity",
            params={"limit": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5

    @pytest.mark.asyncio
    async def test_get_recent_activity_filter_action(
        self, authenticated_client: AsyncClient
    ):
        """Test du filtrage par action."""
        response = await authenticated_client.get(
            "/api/admin/dashboard/recent-activity",
            params={"action": "login"},
        )

        assert response.status_code == 200
        data = response.json()
        # Tous les items doivent avoir l'action "login"
        for item in data["items"]:
            assert item["action"] == "login"

    @pytest.mark.asyncio
    async def test_get_pending_tasks(self, authenticated_client: AsyncClient):
        """Test de récupération des tâches en attente."""
        response = await authenticated_client.get("/api/admin/dashboard/pending-tasks")

        assert response.status_code == 200
        data = response.json()

        assert "tasks" in data
        assert "total" in data
        assert isinstance(data["tasks"], list)

    @pytest.mark.asyncio
    async def test_dashboard_stats_unauthorized(self, client: AsyncClient):
        """Test des statistiques sans authentification."""
        response = await client.get("/api/admin/dashboard/stats")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_recent_activity_unauthorized(self, client: AsyncClient):
        """Test de l'activité récente sans authentification."""
        response = await client.get("/api/admin/dashboard/recent-activity")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_pending_tasks_unauthorized(self, client: AsyncClient):
        """Test des tâches en attente sans authentification."""
        response = await client.get("/api/admin/dashboard/pending-tasks")

        assert response.status_code == 401
