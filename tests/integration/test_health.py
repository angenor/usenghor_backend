"""
Tests d'intégration - Health & Root
===================================

Tests des endpoints de santé et racine.
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Tests pour les endpoints de santé."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test de l'endpoint de santé."""
        response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test de l'endpoint racine."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "USenghor API"
        assert "version" in data
        assert "documentation" in data


class TestOpenAPIDocumentation:
    """Tests pour la documentation OpenAPI."""

    @pytest.mark.asyncio
    async def test_openapi_json(self, client: AsyncClient):
        """Test de disponibilité du schéma OpenAPI."""
        response = await client.get("/api/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    @pytest.mark.asyncio
    async def test_swagger_ui(self, client: AsyncClient):
        """Test de disponibilité de Swagger UI."""
        response = await client.get("/api/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_redoc(self, client: AsyncClient):
        """Test de disponibilité de ReDoc."""
        response = await client.get("/api/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
