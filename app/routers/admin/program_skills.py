"""
Router Admin - Compétences de programme
=======================================

Endpoints CRUD pour la gestion des compétences.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.academic import ProgramSkill
from app.schemas.academic import (
    ProgramSkillCreate,
    ProgramSkillRead,
    ProgramSkillReorder,
    ProgramSkillUpdate,
)
from app.schemas.common import IdResponse, MessageResponse
from app.services.academic_service import AcademicService

router = APIRouter(prefix="/program-skills", tags=["Program Skills"])


@router.get("", response_model=dict)
async def list_skills(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    program_id: str | None = Query(None, description="Filtrer par programme"),
    _: bool = Depends(PermissionChecker("programs.view")),
) -> dict:
    """Liste les compétences avec pagination et filtres."""
    service = AcademicService(db)
    query = await service.get_skills(program_id=program_id)
    return await paginate(db, query, pagination, ProgramSkill, ProgramSkillRead)


@router.get("/{skill_id}", response_model=ProgramSkillRead)
async def get_skill(
    skill_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.view")),
) -> ProgramSkill:
    """Récupère une compétence par son ID."""
    service = AcademicService(db)
    skill = await service.get_skill_by_id(skill_id)
    if not skill:
        raise NotFoundException("Compétence non trouvée")
    return skill


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: ProgramSkillCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> IdResponse:
    """Crée une nouvelle compétence."""
    service = AcademicService(db)
    skill = await service.create_skill(
        program_id=skill_data.program_id,
        title=skill_data.title,
        description=skill_data.description,
        display_order=skill_data.display_order,
    )
    return IdResponse(id=skill.id, message="Compétence créée avec succès")


@router.put("/{skill_id}", response_model=ProgramSkillRead)
async def update_skill(
    skill_id: str,
    skill_data: ProgramSkillUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> ProgramSkill:
    """Met à jour une compétence."""
    service = AcademicService(db)
    update_dict = skill_data.model_dump(exclude_unset=True)
    return await service.update_skill(skill_id, **update_dict)


@router.delete("/{skill_id}", response_model=MessageResponse)
async def delete_skill(
    skill_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> MessageResponse:
    """Supprime une compétence."""
    service = AcademicService(db)
    await service.delete_skill(skill_id)
    return MessageResponse(message="Compétence supprimée avec succès")


@router.put("/reorder", response_model=list[ProgramSkillRead])
async def reorder_skills(
    reorder_data: ProgramSkillReorder,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> list[ProgramSkill]:
    """Réordonne les compétences."""
    service = AcademicService(db)
    return await service.reorder_skills(reorder_data.skill_ids)
