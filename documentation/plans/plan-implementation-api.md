# Plan d'implémentation - API FastAPI USenghor

> **Version**: 1.0
> **Python**: 3.14
> **Framework**: FastAPI
> **Base de données**: PostgreSQL 15+

---

## Table des matières

1. [Architecture globale](#1-architecture-globale)
2. [Structure du projet](#2-structure-du-projet)
3. [Dépendances](#3-dépendances)
4. [Authentification & Autorisations](#4-authentification--autorisations)
5. [Services et Endpoints](#5-services-et-endpoints)
6. [Patterns communs](#6-patterns-communs)
7. [Ordre d'implémentation](#7-ordre-dimplémentation)

---

## 1. Architecture globale

### 1.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                         Clients                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Nuxt Front  │  │  Nuxt Admin  │  │  Mobile App  │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
└─────────┼─────────────────┼─────────────────┼───────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Middleware: Auth, CORS, Rate Limiting, Logging             ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Routers: /api/public/* | /api/admin/* | /api/auth/*        ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Services Layer                            │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │  Core  │ │Identity│ │ Media  │ │Academic│ │Content │  ...    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL 15+                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  12 schémas: core, identity, media, organization, campus,  │ │
│  │  partner, academic, application, content, project,          │ │
│  │  newsletter, editorial                                      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Principes architecturaux

- **Monolithe modulaire** : Code organisé par domaine métier (bounded contexts)
- **Préparé microservices** : Pattern `*_external_id` pour références cross-services
- **API RESTful** : Conventions REST strictes
- **RBAC** : Contrôle d'accès basé sur les rôles et permissions

---

## 2. Structure du projet

```
usenghor_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Point d'entrée FastAPI
│   ├── config.py                  # Configuration (env vars)
│   ├── database.py                # Connexion PostgreSQL
│   │
│   ├── core/                      # Utilitaires partagés
│   │   ├── __init__.py
│   │   ├── dependencies.py        # Dépendances FastAPI (auth, db)
│   │   ├── exceptions.py          # Exceptions personnalisées
│   │   ├── pagination.py          # Utilitaires pagination
│   │   ├── security.py            # JWT, hashing
│   │   └── utils.py               # Fonctions utilitaires
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py                # Middleware authentification
│   │   ├── audit.py               # Logging des actions
│   │   └── cors.py                # Configuration CORS
│   │
│   ├── models/                    # Modèles SQLAlchemy
│   │   ├── __init__.py
│   │   ├── base.py                # Modèle de base
│   │   ├── core.py                # countries
│   │   ├── identity.py            # users, roles, permissions
│   │   ├── media.py               # media, albums
│   │   ├── organization.py        # departments, services
│   │   ├── campus.py              # campuses, campus_team
│   │   ├── partner.py             # partners
│   │   ├── academic.py            # programs, semesters, courses
│   │   ├── application.py         # application_calls, applications
│   │   ├── content.py             # news, events, tags
│   │   ├── project.py             # projects, project_calls
│   │   ├── newsletter.py          # campaigns, subscribers
│   │   └── editorial.py           # editorial_contents
│   │
│   ├── schemas/                   # Schémas Pydantic
│   │   ├── __init__.py
│   │   ├── common.py              # Schémas partagés (pagination, etc.)
│   │   ├── core.py
│   │   ├── identity.py
│   │   ├── media.py
│   │   ├── organization.py
│   │   ├── campus.py
│   │   ├── partner.py
│   │   ├── academic.py
│   │   ├── application.py
│   │   ├── content.py
│   │   ├── project.py
│   │   ├── newsletter.py
│   │   └── editorial.py
│   │
│   ├── services/                  # Logique métier
│   │   ├── __init__.py
│   │   ├── core_service.py
│   │   ├── identity_service.py
│   │   ├── media_service.py
│   │   ├── organization_service.py
│   │   ├── campus_service.py
│   │   ├── partner_service.py
│   │   ├── academic_service.py
│   │   ├── application_service.py
│   │   ├── content_service.py
│   │   ├── project_service.py
│   │   ├── newsletter_service.py
│   │   └── editorial_service.py
│   │
│   └── routers/                   # Routes API
│       ├── __init__.py
│       ├── auth.py                # /api/auth/*
│       ├── public/                # /api/public/* (sans auth)
│       │   ├── __init__.py
│       │   ├── programs.py
│       │   ├── news.py
│       │   ├── events.py
│       │   └── countries.py
│       │
│       └── admin/                 # /api/admin/* (avec auth)
│           ├── __init__.py
│           ├── dashboard.py
│           ├── users.py
│           ├── roles.py
│           ├── permissions.py
│           ├── audit_logs.py
│           ├── programs.py
│           ├── applications.py
│           ├── news.py
│           ├── events.py
│           ├── projects.py
│           ├── departments.py
│           ├── services.py
│           ├── campuses.py
│           ├── partners.py
│           ├── media.py
│           ├── albums.py
│           ├── newsletter.py
│           ├── editorial.py
│           └── countries.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Fixtures pytest
│   ├── test_auth.py
│   └── ...
│
├── alembic/                       # Migrations (optionnel)
│   ├── versions/
│   └── env.py
│
├── pyproject.toml                 # Configuration projet
├── requirements.txt
├── .env.example
└── README.md
```

---

## 3. Dépendances

### 3.1 requirements.txt

```txt
# Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6

# Base de données
sqlalchemy>=2.0.25
asyncpg>=0.29.0
psycopg2-binary>=2.9.9

# Authentification
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# Validation
pydantic>=2.5.3
pydantic-settings>=2.1.0
email-validator>=2.1.0

# Utilitaires
python-dotenv>=1.0.0
Pillow>=10.2.0

# Export
openpyxl>=3.1.2
reportlab>=4.0.8

# Email
aiosmtplib>=3.0.1
jinja2>=3.1.3

# Tests
pytest>=7.4.4
pytest-asyncio>=0.23.3
httpx>=0.26.0
```

---

## 4. Authentification & Autorisations

### 4.1 Endpoints d'authentification

```
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/refresh
POST /api/auth/forgot-password
POST /api/auth/reset-password
GET  /api/auth/me
PUT  /api/auth/me
PUT  /api/auth/me/password
```

### 4.2 Système de permissions

| Permission | Description |
|------------|-------------|
| `users.view` | Voir les utilisateurs |
| `users.create` | Créer des utilisateurs |
| `users.edit` | Modifier les utilisateurs |
| `users.delete` | Supprimer des utilisateurs |
| `users.roles` | Gérer les rôles des utilisateurs |
| `programs.view` | Voir les formations |
| `programs.create` | Créer des formations |
| `programs.edit` | Modifier les formations |
| `programs.delete` | Supprimer des formations |
| `applications.view` | Voir les candidatures |
| `applications.evaluate` | Évaluer les candidatures |
| `applications.export` | Exporter les candidatures |
| `events.view` / `create` / `edit` / `delete` | Gestion événements |
| `news.view` / `create` / `edit` / `delete` | Gestion actualités |
| `campuses.view` / `create` / `edit` / `delete` | Gestion campus |
| `partners.view` / `create` / `edit` / `delete` | Gestion partenaires |
| `projects.view` / `create` / `edit` / `delete` | Gestion projets |
| `media.view` / `create` / `edit` / `delete` | Gestion médias |
| `newsletter.view` / `create` / `send` | Gestion newsletter |
| `editorial.view` / `edit` | Gestion contenu éditorial |
| `organization.view` / `edit` | Gestion organisation |
| `admin.settings` | Paramètres système |
| `admin.audit` | Voir les logs d'audit |

### 4.3 Rôles prédéfinis

| Rôle | Niveau | Description |
|------|--------|-------------|
| `super_admin` | 100 | Accès total, toutes permissions implicites |
| `admin` | 80 | Administration générale |
| `campus_admin` | 60 | Administration d'un campus spécifique |
| `editor` | 40 | Création et modification de contenus |
| `moderator` | 30 | Modération |
| `user` | 10 | Utilisateur de base |

### 4.4 Décorateur de permission

```python
# Exemple d'utilisation
@router.get("/users")
@require_permission("users.view")
async def list_users(current_user: User = Depends(get_current_user)):
    ...
```

---

## 5. Services et Endpoints

### 5.1 Dashboard (`00_dashboard`)

```
GET /api/admin/dashboard/stats
GET /api/admin/dashboard/recent-activity
GET /api/admin/dashboard/pending-tasks
```

---

### 5.2 Core - Pays (`01_core`)

```
GET    /api/admin/countries
GET    /api/admin/countries/{id}
POST   /api/admin/countries
PUT    /api/admin/countries/{id}
POST   /api/admin/countries/{id}/toggle-active
POST   /api/admin/countries/bulk-toggle
POST   /api/admin/countries/import-iso

# Public
GET    /api/public/countries
```

---

### 5.3 Identity - Utilisateurs (`02_identity`)

#### Utilisateurs
```
GET    /api/admin/users
GET    /api/admin/users/{id}
POST   /api/admin/users
PUT    /api/admin/users/{id}
DELETE /api/admin/users/{id}
POST   /api/admin/users/{id}/toggle-active
POST   /api/admin/users/bulk-action
GET    /api/admin/users/{id}/roles
PUT    /api/admin/users/{id}/roles
POST   /api/admin/users/{id}/reset-password
POST   /api/admin/users/{id}/verify-email
GET    /api/admin/users/{id}/activity
GET    /api/admin/users/{id}/permissions
POST   /api/admin/users/{id}/anonymize
```

#### Rôles
```
GET    /api/admin/roles
GET    /api/admin/roles/{id}
POST   /api/admin/roles
PUT    /api/admin/roles/{id}
DELETE /api/admin/roles/{id}
POST   /api/admin/roles/{id}/duplicate
POST   /api/admin/roles/{id}/toggle-active
GET    /api/admin/roles/{id}/permissions
PUT    /api/admin/roles/{id}/permissions
GET    /api/admin/roles/{id}/users
GET    /api/admin/roles/compare
```

#### Permissions
```
GET    /api/admin/permissions
GET    /api/admin/permissions/{id}
POST   /api/admin/permissions
PUT    /api/admin/permissions/{id}
GET    /api/admin/permissions/{id}/roles
GET    /api/admin/permissions/matrix
PUT    /api/admin/permissions/matrix
```

#### Audit
```
GET    /api/admin/audit-logs
GET    /api/admin/audit-logs/{id}
GET    /api/admin/audit-logs/user/{user_id}
GET    /api/admin/audit-logs/record/{table_name}/{record_id}
GET    /api/admin/audit-logs/export
GET    /api/admin/audit-logs/statistics
POST   /api/admin/audit-logs/purge
```

---

### 5.4 Media (`03_media`)

#### Fichiers médias
```
GET    /api/admin/media
GET    /api/admin/media/{id}
POST   /api/admin/media/upload
POST   /api/admin/media/upload-multiple
PUT    /api/admin/media/{id}
DELETE /api/admin/media/{id}
POST   /api/admin/media/bulk-delete
GET    /api/admin/media/statistics
```

#### Albums
```
GET    /api/admin/albums
GET    /api/admin/albums/{id}
POST   /api/admin/albums
PUT    /api/admin/albums/{id}
DELETE /api/admin/albums/{id}
POST   /api/admin/albums/{id}/media
DELETE /api/admin/albums/{id}/media/{media_id}
PUT    /api/admin/albums/{id}/media/reorder
```

---

### 5.5 Organization (`04_organization`)

#### Départements
```
GET    /api/admin/departments
GET    /api/admin/departments/{id}
POST   /api/admin/departments
PUT    /api/admin/departments/{id}
DELETE /api/admin/departments/{id}
PUT    /api/admin/departments/{id}/reorder
GET    /api/admin/departments/{id}/services
GET    /api/admin/departments/{id}/programs
POST   /api/admin/departments/{id}/toggle-active
```

#### Services
```
GET    /api/admin/services
GET    /api/admin/services/{id}
POST   /api/admin/services
PUT    /api/admin/services/{id}
DELETE /api/admin/services/{id}
GET    /api/admin/services/{id}/objectives
POST   /api/admin/services/{id}/objectives
PUT    /api/admin/services/{id}/objectives/{objective_id}
DELETE /api/admin/services/{id}/objectives/{objective_id}
GET    /api/admin/services/{id}/achievements
POST   /api/admin/services/{id}/achievements
GET    /api/admin/services/{id}/projects
PUT    /api/admin/services/{id}/reorder
```

---

### 5.6 Campus (`05_campus`)

#### Campus
```
GET    /api/admin/campuses
GET    /api/admin/campuses/{id}
POST   /api/admin/campuses
PUT    /api/admin/campuses/{id}
DELETE /api/admin/campuses/{id}
POST   /api/admin/campuses/{id}/toggle-active
GET    /api/admin/campuses/{id}/team
GET    /api/admin/campuses/{id}/partners
GET    /api/admin/campuses/{id}/programs
GET    /api/admin/campuses/{id}/media-library
```

#### Équipes campus
```
GET    /api/admin/campus-team
GET    /api/admin/campus-team/{id}
POST   /api/admin/campus-team
PUT    /api/admin/campus-team/{id}
DELETE /api/admin/campus-team/{id}
PUT    /api/admin/campus-team/{id}/reorder
POST   /api/admin/campus-team/{id}/toggle-active
```

---

### 5.7 Partner (`06_partner`)

```
GET    /api/admin/partners
GET    /api/admin/partners/{id}
POST   /api/admin/partners
PUT    /api/admin/partners/{id}
DELETE /api/admin/partners/{id}
POST   /api/admin/partners/{id}/toggle-active
PUT    /api/admin/partners/reorder

# Public
GET    /api/public/partners
```

---

### 5.8 Academic (`07_academic`)

#### Programmes
```
GET    /api/admin/programs
GET    /api/admin/programs/{id}
POST   /api/admin/programs
PUT    /api/admin/programs/{id}
DELETE /api/admin/programs/{id}
POST   /api/admin/programs/{id}/toggle-active
POST   /api/admin/programs/{id}/duplicate
GET    /api/admin/programs/{id}/semesters
GET    /api/admin/programs/{id}/skills
GET    /api/admin/programs/{id}/career-opportunities

# Public
GET    /api/public/programs
GET    /api/public/programs/{slug}
```

#### Semestres et cours
```
GET    /api/admin/program-semesters
GET    /api/admin/program-semesters/{id}
POST   /api/admin/program-semesters
PUT    /api/admin/program-semesters/{id}
DELETE /api/admin/program-semesters/{id}
GET    /api/admin/program-semesters/{id}/courses
POST   /api/admin/program-semesters/{id}/courses
PUT    /api/admin/program-semesters/{id}/courses/{course_id}
DELETE /api/admin/program-semesters/{id}/courses/{course_id}
PUT    /api/admin/program-semesters/{id}/courses/reorder
```

#### Compétences
```
GET    /api/admin/program-skills
GET    /api/admin/program-skills/{id}
POST   /api/admin/program-skills
PUT    /api/admin/program-skills/{id}
DELETE /api/admin/program-skills/{id}
PUT    /api/admin/program-skills/reorder
```

#### Débouchés
```
GET    /api/admin/career-opportunities
GET    /api/admin/career-opportunities/{id}
POST   /api/admin/career-opportunities
PUT    /api/admin/career-opportunities/{id}
DELETE /api/admin/career-opportunities/{id}
PUT    /api/admin/career-opportunities/reorder
```

---

### 5.9 Application (`08_application`)

#### Appels à candidatures
```
GET    /api/admin/application-calls
GET    /api/admin/application-calls/{id}
POST   /api/admin/application-calls
PUT    /api/admin/application-calls/{id}
DELETE /api/admin/application-calls/{id}
POST   /api/admin/application-calls/{id}/publish
POST   /api/admin/application-calls/{id}/close
POST   /api/admin/application-calls/{id}/duplicate
GET    /api/admin/application-calls/{id}/statistics
GET    /api/admin/application-calls/{id}/applications

# Public
GET    /api/public/application-calls
GET    /api/public/application-calls/{id}
```

#### Candidatures
```
GET    /api/admin/applications
GET    /api/admin/applications/{id}
PUT    /api/admin/applications/{id}
PUT    /api/admin/applications/{id}/status
POST   /api/admin/applications/{id}/evaluate
GET    /api/admin/applications/{id}/documents
GET    /api/admin/applications/{id}/history
POST   /api/admin/applications/bulk-status
GET    /api/admin/applications/export
GET    /api/admin/applications/statistics
```

---

### 5.10 Content (`09_content`)

#### Actualités
```
GET    /api/admin/news
GET    /api/admin/news/{id}
POST   /api/admin/news
PUT    /api/admin/news/{id}
DELETE /api/admin/news/{id}
POST   /api/admin/news/{id}/publish
POST   /api/admin/news/{id}/unpublish
POST   /api/admin/news/{id}/duplicate
GET    /api/admin/news/{id}/versions

# Public
GET    /api/public/news
GET    /api/public/news/{slug}
```

#### Événements
```
GET    /api/admin/events
GET    /api/admin/events/{id}
POST   /api/admin/events
PUT    /api/admin/events/{id}
DELETE /api/admin/events/{id}
POST   /api/admin/events/{id}/publish
POST   /api/admin/events/{id}/cancel
POST   /api/admin/events/{id}/duplicate
GET    /api/admin/events/{id}/registrations
GET    /api/admin/events/{id}/registrations/export

# Public
GET    /api/public/events
GET    /api/public/events/{slug}
POST   /api/public/events/{id}/register
```

#### Inscriptions événements
```
GET    /api/admin/event-registrations
GET    /api/admin/event-registrations/{id}
PUT    /api/admin/event-registrations/{id}
DELETE /api/admin/event-registrations/{id}
POST   /api/admin/event-registrations/{id}/confirm
POST   /api/admin/event-registrations/{id}/cancel
POST   /api/admin/event-registrations/bulk-action
GET    /api/admin/event-registrations/export
```

#### Étiquettes
```
GET    /api/admin/tags
GET    /api/admin/tags/{id}
POST   /api/admin/tags
PUT    /api/admin/tags/{id}
DELETE /api/admin/tags/{id}
POST   /api/admin/tags/merge
GET    /api/admin/tags/{id}/usage
```

---

### 5.11 Project (`10_project`)

#### Projets
```
GET    /api/admin/projects
GET    /api/admin/projects/{id}
POST   /api/admin/projects
PUT    /api/admin/projects/{id}
DELETE /api/admin/projects/{id}
POST   /api/admin/projects/{id}/toggle-active
PUT    /api/admin/projects/reorder

# Public
GET    /api/public/projects
GET    /api/public/projects/{slug}
```

#### Catégories de projets
```
GET    /api/admin/project-categories
GET    /api/admin/project-categories/{id}
POST   /api/admin/project-categories
PUT    /api/admin/project-categories/{id}
DELETE /api/admin/project-categories/{id}
PUT    /api/admin/project-categories/reorder
GET    /api/admin/project-categories/{id}/projects
```

#### Appels à projets
```
GET    /api/admin/project-calls
GET    /api/admin/project-calls/{id}
POST   /api/admin/project-calls
PUT    /api/admin/project-calls/{id}
DELETE /api/admin/project-calls/{id}
POST   /api/admin/project-calls/{id}/publish
POST   /api/admin/project-calls/{id}/close
GET    /api/admin/project-calls/{id}/submissions

# Public
GET    /api/public/project-calls
GET    /api/public/project-calls/{id}
```

---

### 5.12 Newsletter (`11_newsletter`)

#### Campagnes
```
GET    /api/admin/newsletter-campaigns
GET    /api/admin/newsletter-campaigns/{id}
POST   /api/admin/newsletter-campaigns
PUT    /api/admin/newsletter-campaigns/{id}
DELETE /api/admin/newsletter-campaigns/{id}
POST   /api/admin/newsletter-campaigns/{id}/send
POST   /api/admin/newsletter-campaigns/{id}/schedule
POST   /api/admin/newsletter-campaigns/{id}/test
POST   /api/admin/newsletter-campaigns/{id}/duplicate
GET    /api/admin/newsletter-campaigns/{id}/statistics
```

#### Abonnés
```
GET    /api/admin/newsletter-subscribers
GET    /api/admin/newsletter-subscribers/{id}
POST   /api/admin/newsletter-subscribers
PUT    /api/admin/newsletter-subscribers/{id}
DELETE /api/admin/newsletter-subscribers/{id}
POST   /api/admin/newsletter-subscribers/import
GET    /api/admin/newsletter-subscribers/export
POST   /api/admin/newsletter-subscribers/bulk-action

# Public
POST   /api/public/newsletter/subscribe
GET    /api/public/newsletter/unsubscribe/{token}
```

#### Statistiques newsletter
```
GET    /api/admin/newsletter/statistics
GET    /api/admin/newsletter/statistics/overview
GET    /api/admin/newsletter/statistics/campaigns
GET    /api/admin/newsletter/statistics/growth
```

---

### 5.13 Editorial (`12_editorial`)

```
GET    /api/admin/editorial-categories
GET    /api/admin/editorial/{category}
PUT    /api/admin/editorial/{category}
GET    /api/admin/editorial/{category}/history

# Public
GET    /api/public/editorial/{category}
```

**Catégories éditoriales :**
- `key_figures` - Chiffres clés
- `values` - Valeurs de l'université
- `contact` - Informations de contact
- `social_media` - Réseaux sociaux
- `legal` - Mentions légales

---

## 6. Patterns communs

### 6.1 Pagination

```python
# Schéma de pagination
class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    limit: int
    pages: int

# Paramètres communs
page: int = Query(1, ge=1)
limit: int = Query(20, ge=1, le=100)
sort_by: str = Query("created_at")
sort_order: str = Query("desc", pattern="^(asc|desc)$")
```

### 6.2 Filtres communs

```python
# Paramètres de recherche
search: str = Query(None, description="Recherche textuelle")
active: bool = Query(None, description="Filtrer par statut actif")
date_from: date = Query(None, description="Date de début")
date_to: date = Query(None, description="Date de fin")
```

### 6.3 Réponses standard

```python
# Succès création
{ "id": "uuid", "message": "Créé avec succès" }

# Succès modification
{ "message": "Modifié avec succès" }

# Succès suppression
{ "message": "Supprimé avec succès" }

# Erreur validation
{
    "detail": [
        { "loc": ["body", "email"], "msg": "Email invalide", "type": "value_error" }
    ]
}

# Erreur 404
{ "detail": "Ressource non trouvée" }

# Erreur 403
{ "detail": "Permission refusée" }
```

### 6.4 Upload de fichiers

```python
# Endpoint upload
POST /api/admin/media/upload
Content-Type: multipart/form-data

# Paramètres
file: UploadFile
folder: str = "general"
alt_text: str = None

# Réponse
{
    "id": "uuid",
    "filename": "image.jpg",
    "url": "https://cdn.usenghor.org/...",
    "mime_type": "image/jpeg",
    "size": 102400
}
```

### 6.5 Export

```python
# Endpoint export générique
GET /api/admin/{resource}/export
Accept: text/csv | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

# Paramètres
format: str = Query("csv", pattern="^(csv|xlsx)$")
# + tous les filtres du listing
```

---

## 7. Ordre d'implémentation

> **Légende** : `[ ]` À faire · `[~]` En cours · `[x]` Terminé

### Phase 1 : Fondations (Semaine 1-2)

- [x] **1. Configuration projet**
  - [x] Structure des dossiers
  - [x] Configuration FastAPI
  - [x] Connexion PostgreSQL
  - [x] Docker Compose (PostgreSQL + Adminer)

- [x] **2. Authentification**
  - [x] Login/Logout
  - [x] JWT tokens
  - [x] Middleware auth
  - [x] Endpoints /api/auth/* (login, refresh, logout, me)

- [x] **3. Core Identity**
  - [x] CRUD utilisateurs
  - [x] CRUD rôles
  - [x] CRUD permissions
  - [x] Système RBAC

### Phase 2 : Données de base (Semaine 3-4)

- [x] **4. Core**
  - [x] CRUD pays

- [x] **5. Media**
  - [x] Upload fichiers
  - [x] CRUD albums

- [x] **6. Organization**
  - [x] CRUD départements
  - [x] CRUD services

### Phase 3 : Contenus (Semaine 5-6)

- [x] **7. Content**
  - [x] CRUD actualités
  - [x] CRUD événements
  - [x] CRUD étiquettes
  - [x] Inscriptions événements

- [x] **8. Campus**
  - [x] CRUD campus
  - [x] Équipes campus

- [x] **9. Partners**
  - [x] CRUD partenaires

### Phase 4 : Académique (Semaine 7-8)

- [x] **10. Academic**
  - [x] CRUD programmes
  - [x] Semestres et cours
  - [x] Compétences
  - [x] Débouchés

- [x] **11. Application**
  - [x] Appels à candidatures
  - [x] Gestion candidatures
  - [x] Évaluation

### Phase 5 : Communication (Semaine 9-10)

- [x] **12. Newsletter**
  - [x] Campagnes
  - [x] Abonnés
  - [x] Envoi emails

- [x] **13. Editorial**
  - [x] Contenus éditoriaux
  - [x] Historique versions

- [x] **14. Project**
  - [x] CRUD projets
  - [x] Catégories
  - [x] Appels à projets

### Phase 6 : Finalisation (Semaine 11-12)

- [x] **15. Dashboard**
  - [x] Statistiques globales
  - [x] Activité récente
  - [x] Tâches en attente

- [x] **16. Audit**
  - [x] Journal d'audit
  - [x] Statistiques
  - [x] Export

- [x] **17. Tests & Documentation**
  - [x] Tests unitaires
  - [x] Tests d'intégration
  - [x] Documentation OpenAPI

---

## Annexes

### A. Variables d'environnement

```env
# Application
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/usenghor

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Storage
STORAGE_TYPE=local  # ou s3
STORAGE_PATH=/var/www/uploads

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@usenghor.org
SMTP_PASSWORD=your-password
```

### B. Codes HTTP utilisés

| Code | Usage |
|------|-------|
| 200 | Succès GET, PUT |
| 201 | Succès POST (création) |
| 204 | Succès DELETE |
| 400 | Erreur de validation |
| 401 | Non authentifié |
| 403 | Permission refusée |
| 404 | Ressource non trouvée |
| 409 | Conflit (doublon, etc.) |
| 422 | Entité non traitable |
| 500 | Erreur serveur |

### C. Références

- [Plans d'implémentation pages](../../usenghor_nuxt/bank/plans/plan-back-office/)
- [Modèle de données SQL](../modele_de_données/services/main.sql)
- [Description sidebar](../../usenghor_nuxt/bank/plans/plan-back-office/description-side-bare.md)
