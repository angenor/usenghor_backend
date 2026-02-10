"""
Router Public - Programmes
==========================

Endpoints publics pour les programmes de formation.
"""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.academic import Program, ProgramType
from app.models.base import PublicationStatus
from app.schemas.academic import ProgramPublic, ProgramPublicWithDetails
from app.schemas.content import NewsPublicEnriched
from app.services.academic_service import AcademicService
from app.services.content_service import ContentService

router = APIRouter(prefix="/programs", tags=["Programs"])


@router.get("", response_model=dict)
async def list_programs(
    db: DbSession,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur code, titre, description"),
    program_type: ProgramType | None = Query(None, description="Filtrer par type"),
    sector_id: str | None = Query(None, description="Filtrer par département"),
) -> dict:
    """Liste les programmes publiés avec pagination et filtres."""
    service = AcademicService(db)
    query = await service.get_published_programs(
        search=search,
        program_type=program_type,
        sector_id=sector_id,
        skip_order_by=True,  # Let paginate handle ORDER BY
    )
    return await paginate(db, query, pagination, Program, ProgramPublic)


@router.get("/featured", response_model=list[ProgramPublic])
async def list_featured_programs(
    db: DbSession,
    limit: int = Query(4, ge=1, le=20, description="Nombre maximum de programmes"),
) -> list[Program]:
    """Liste les programmes publiés mis à la une."""
    service = AcademicService(db)
    programs = await service.get_featured_programs(limit=limit)
    return programs


@router.get("/{slug}/news", response_model=list[NewsPublicEnriched])
async def get_program_news(
    slug: str,
    db: DbSession,
) -> list[NewsPublicEnriched]:
    """Récupère les actualités publiées associées à un programme."""
    academic_service = AcademicService(db)
    program = await academic_service.get_program_by_slug(slug)
    if not program or program.status != PublicationStatus.PUBLISHED:
        raise NotFoundException("Programme non trouvé")

    content_service = ContentService(db)
    query = await content_service.get_news(
        status=PublicationStatus.PUBLISHED,
        program_id=program.id,
    )
    result = await db.execute(query)
    news_list = list(result.scalars().all())

    enriched_items = await content_service.enrich_news_with_names(news_list)
    return [NewsPublicEnriched.model_validate(item) for item in enriched_items]


@router.get("/{slug}/media-library", response_model=list[str])
async def get_program_media_library(
    slug: str,
    db: DbSession,
) -> list[str]:
    """Récupère les IDs des albums de la médiathèque associés à un programme."""
    service = AcademicService(db)
    program = await service.get_program_by_slug(slug)
    if not program or program.status != PublicationStatus.PUBLISHED:
        raise NotFoundException("Programme non trouvé")

    return await service.get_program_albums(program.id)


@router.get("/{slug}", response_model=ProgramPublicWithDetails)
async def get_program_by_slug(
    slug: str,
    db: DbSession,
) -> Program:
    """Récupère un programme publié par son slug."""
    service = AcademicService(db)
    program = await service.get_program_by_slug(slug)
    if not program:
        raise NotFoundException("Programme non trouvé")

    if program.status != PublicationStatus.PUBLISHED:
        raise NotFoundException("Programme non trouvé")

    return program


@router.get("/by-type/{program_type}", response_model=list[ProgramPublic])
async def list_programs_by_type(
    program_type: ProgramType,
    db: DbSession,
) -> list[Program]:
    """Liste les programmes publiés d'un type donné."""
    service = AcademicService(db)
    query = await service.get_published_programs(program_type=program_type)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/by-sector/{sector_id}", response_model=list[ProgramPublic])
async def list_programs_by_sector(
    sector_id: str,
    db: DbSession,
) -> list[Program]:
    """Liste les programmes publiés d'un département donné."""
    service = AcademicService(db)
    query = await service.get_published_programs(sector_id=sector_id)
    result = await db.execute(query)
    return list(result.scalars().all())
