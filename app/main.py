"""
Point d'entrée FastAPI
======================

Application principale de l'API USenghor.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_db, init_db
from app.routers import auth
from app.routers.admin import router as admin_router
from app.routers.public import router as public_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gestionnaire du cycle de vie de l'application.

    - Startup: Initialisation de la base de données
    - Shutdown: Fermeture des connexions
    """
    # Startup
    if settings.is_development:
        await init_db()

    yield

    # Shutdown
    await close_db()


app = FastAPI(
    title="USenghor API",
    description="API pour le site web de l'Université Senghor d'Alexandrie",
    version="0.1.0",
    docs_url="/api/docs" if settings.is_development else None,
    redoc_url="/api/redoc" if settings.is_development else None,
    openapi_url="/api/openapi.json" if settings.is_development else None,
    lifespan=lifespan,
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(admin_router)
app.include_router(public_router)


@app.get("/api/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Endpoint de vérification de santé de l'API."""
    return {"status": "ok", "message": "USenghor API is running"}


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Endpoint racine."""
    return {
        "name": "USenghor API",
        "version": "0.1.0",
        "documentation": "/api/docs",
    }
