"""
Router Admin - Débouchés professionnels
=======================================

Endpoints CRUD pour la gestion des débouchés.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.academic import ProgramCareerOpportunity
from app.schemas.academic import (
    ProgramCareerOpportunityCreate,
    ProgramCareerOpportunityRead,
    ProgramCareerOpportunityReorder,
    ProgramCareerOpportunityUpdate,
)
from app.schemas.common import IdResponse, MessageResponse
from app.services.academic_service import AcademicService

router = APIRouter(prefix="/career-opportunities", tags=["Career Opportunities"])


@router.get("", response_model=dict)
async def list_career_opportunities(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    program_id: str | None = Query(None, description="Filtrer par programme"),
    _: bool = Depends(PermissionChecker("programs.view")),
) -> dict:
    """Liste les débouchés avec pagination et filtres."""
    service = AcademicService(db)
    query = await service.get_career_opportunities(program_id=program_id)
    return await paginate(db, query, pagination, ProgramCareerOpportunity, ProgramCareerOpportunityRead)


@router.get("/{opportunity_id}", response_model=ProgramCareerOpportunityRead)
async def get_career_opportunity(
    opportunity_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.view")),
) -> ProgramCareerOpportunity:
    """Récupère un débouché par son ID."""
    service = AcademicService(db)
    opportunity = await service.get_career_opportunity_by_id(opportunity_id)
    if not opportunity:
        raise NotFoundException("Débouché non trouvé")
    return opportunity


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_career_opportunity(
    opportunity_data: ProgramCareerOpportunityCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> IdResponse:
    """Crée un nouveau débouché."""
    service = AcademicService(db)
    opportunity = await service.create_career_opportunity(
        program_id=opportunity_data.program_id,
        title=opportunity_data.title,
        description=opportunity_data.description,
        display_order=opportunity_data.display_order,
    )
    return IdResponse(id=opportunity.id, message="Débouché créé avec succès")


@router.put("/{opportunity_id}", response_model=ProgramCareerOpportunityRead)
async def update_career_opportunity(
    opportunity_id: str,
    opportunity_data: ProgramCareerOpportunityUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> ProgramCareerOpportunity:
    """Met à jour un débouché."""
    service = AcademicService(db)
    update_dict = opportunity_data.model_dump(exclude_unset=True)
    return await service.update_career_opportunity(opportunity_id, **update_dict)


@router.delete("/{opportunity_id}", response_model=MessageResponse)
async def delete_career_opportunity(
    opportunity_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> MessageResponse:
    """Supprime un débouché."""
    service = AcademicService(db)
    await service.delete_career_opportunity(opportunity_id)
    return MessageResponse(message="Débouché supprimé avec succès")


@router.put("/reorder", response_model=list[ProgramCareerOpportunityRead])
async def reorder_career_opportunities(
    reorder_data: ProgramCareerOpportunityReorder,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> list[ProgramCareerOpportunity]:
    """Réordonne les débouchés."""
    service = AcademicService(db)
    return await service.reorder_career_opportunities(reorder_data.opportunity_ids)
