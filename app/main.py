"""
Point d'entrée FastAPI
======================

Application principale de l'API USenghor.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import close_db, init_db
from app.routers import auth
from app.routers.admin import router as admin_router
from app.routers.public import router as public_router


# ============================================================================
# Métadonnées OpenAPI
# ============================================================================

API_DESCRIPTION = """
## Université Senghor - API Backend

L'API USenghor fournit les services backend pour le site web de l'Université Senghor d'Alexandrie,
université internationale de langue française au service du développement africain.

### Fonctionnalités principales

* **Authentification** - JWT avec refresh tokens, gestion des sessions
* **Gestion des utilisateurs** - CRUD complet avec rôles et permissions (RBAC)
* **Contenu éditorial** - Actualités, événements, médias
* **Gestion académique** - Programmes, formations, candidatures
* **Newsletter** - Campagnes et abonnés
* **Dashboard** - Statistiques et monitoring

### Authentification

L'API utilise l'authentification JWT Bearer. Pour accéder aux endpoints protégés :

1. Obtenir un token via `POST /api/auth/login`
2. Inclure le token dans l'en-tête : `Authorization: Bearer <token>`
3. Rafraîchir le token avant expiration via `POST /api/auth/refresh`

### Codes de réponse

| Code | Description |
|------|-------------|
| 200  | Succès |
| 201  | Ressource créée |
| 204  | Suppression réussie |
| 400  | Erreur de validation |
| 401  | Non authentifié |
| 403  | Permission refusée |
| 404  | Ressource non trouvée |
| 409  | Conflit (doublon) |
| 422  | Données invalides |
| 500  | Erreur serveur |
"""

TAGS_METADATA = [
    {
        "name": "Health",
        "description": "Endpoints de vérification de santé de l'API.",
    },
    {
        "name": "Root",
        "description": "Informations générales sur l'API.",
    },
    {
        "name": "Auth",
        "description": "Authentification et gestion des sessions utilisateur.",
    },
    {
        "name": "Users",
        "description": "Gestion des utilisateurs (CRUD, activation, rôles).",
    },
    {
        "name": "Roles",
        "description": "Gestion des rôles et permissions RBAC.",
    },
    {
        "name": "Permissions",
        "description": "Liste et gestion des permissions.",
    },
    {
        "name": "Dashboard",
        "description": "Statistiques globales et tableau de bord administrateur.",
    },
    {
        "name": "Audit Logs",
        "description": "Journal d'audit des actions utilisateurs.",
    },
    {
        "name": "News",
        "description": "Gestion des actualités (multilingue).",
    },
    {
        "name": "Events",
        "description": "Gestion des événements et inscriptions.",
    },
    {
        "name": "Media",
        "description": "Gestion des fichiers médias (images, documents).",
    },
    {
        "name": "Albums",
        "description": "Gestion des albums photos.",
    },
    {
        "name": "Programs",
        "description": "Gestion des programmes académiques.",
    },
    {
        "name": "Applications",
        "description": "Gestion des candidatures et appels à candidatures.",
    },
    {
        "name": "Partners",
        "description": "Gestion des partenaires institutionnels.",
    },
    {
        "name": "Campuses",
        "description": "Gestion des campus et équipes.",
    },
    {
        "name": "Newsletter",
        "description": "Gestion des campagnes et abonnés newsletter.",
    },
    {
        "name": "Editorial",
        "description": "Contenus éditoriaux et pages statiques.",
    },
    {
        "name": "Projects",
        "description": "Projets institutionnels et appels à projets.",
    },
    {
        "name": "Public",
        "description": "Endpoints publics (sans authentification).",
    },
]


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
    description=API_DESCRIPTION,
    version="0.1.0",
    docs_url="/api/docs" if settings.is_development else None,
    redoc_url="/api/redoc" if settings.is_development else None,
    openapi_url="/api/openapi.json" if settings.is_development else None,
    openapi_tags=TAGS_METADATA,
    contact={
        "name": "Université Senghor",
        "url": "https://www.usenghor.org",
        "email": "contact@usenghor.org",
    },
    license_info={
        "name": "Propriétaire",
        "identifier": "Proprietary",
    },
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

# Fichiers statiques (uploads)
# Créer le dossier immédiatement pour permettre le montage
uploads_dir = Path(settings.storage_path)
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


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
