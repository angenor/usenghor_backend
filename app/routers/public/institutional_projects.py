"""
Router Public - Projets Institutionnels
=======================================

Endpoints publics pour consulter les projets institutionnels.
"""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.organization import ProjectStatus
from app.models.project import Project, ProjectCallStatus
from app.schemas.project import (
    ProjectCallRead,
    ProjectCategoryRead,
    ProjectPublic,
    ProjectReadWithRelations,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Institutional Projects"])


@router.get("/categories", response_model=list[ProjectCategoryRead])
async def list_categories(
    db: DbSession,
) -> list[ProjectCategoryRead]:
    """Liste toutes les catégories de projets."""
    service = ProjectService(db)
    query = await service.get_categories()
    result = await db.execute(query)
    return [ProjectCategoryRead.model_validate(c) for c in result.scalars().all()]


@router.get("", response_model=dict)
async def list_projects(
    db: DbSession,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche"),
    status: ProjectStatus | None = Query(None, description="Statut du projet"),
    category: str | None = Query(None, description="Slug de catégorie"),
) -> dict:
    """
    Liste les projets publiés avec pagination.

    Seuls les projets avec publication_status=published sont retournés.
    """
    service = ProjectService(db)
    query = await service.get_public_projects(
        search=search,
        status=status,
        category_slug=category,
    )
    return await paginate(db, query, pagination, Project, schema_class=ProjectPublic)


@router.get("/by-slug/{slug}", response_model=ProjectReadWithRelations)
async def get_project_by_slug(
    slug: str,
    db: DbSession,
) -> Project:
    """
    Récupère un projet publié par son slug.

    Retourne une erreur 404 si le projet n'existe pas ou n'est pas publié.
    """
    service = ProjectService(db)
    project = await service.get_public_project_by_slug(slug)
    if not project:
        raise NotFoundException("Projet non trouvé")
    return project


@router.get("/{project_id}", response_model=ProjectPublic)
async def get_project(
    project_id: str,
    db: DbSession,
) -> Project:
    """
    Récupère un projet publié par son ID.

    Retourne une erreur 404 si le projet n'existe pas ou n'est pas publié.
    """
    service = ProjectService(db)
    project = await service.get_project_by_id(project_id)
    if not project or project.publication_status.value != "published":
        raise NotFoundException("Projet non trouvé")
    return project


@router.get("/calls/ongoing", response_model=list[ProjectCallRead])
async def list_ongoing_calls(
    db: DbSession,
) -> list[ProjectCallRead]:
    """
    Liste les appels en cours (projets publiés uniquement).

    Utile pour afficher les opportunités actuelles sur le site.
    """
    service = ProjectService(db)
    calls = await service.get_public_calls(status=ProjectCallStatus.ONGOING)
    return [ProjectCallRead.model_validate(c) for c in calls]


@router.get("/calls/upcoming", response_model=list[ProjectCallRead])
async def list_upcoming_calls(
    db: DbSession,
) -> list[ProjectCallRead]:
    """
    Liste les appels à venir (projets publiés uniquement).

    Utile pour afficher les opportunités futures sur le site.
    """
    service = ProjectService(db)
    calls = await service.get_public_calls(status=ProjectCallStatus.UPCOMING)
    return [ProjectCallRead.model_validate(c) for c in calls]
