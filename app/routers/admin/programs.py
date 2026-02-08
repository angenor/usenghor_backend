"""
Router Admin - Programmes
=========================

Endpoints CRUD pour la gestion des programmes de formation.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.academic import Program, ProgramType
from app.models.base import PublicationStatus
from app.schemas.academic import (
    ProgramCampusCreate,
    ProgramCareerOpportunityRead,
    ProgramCreate,
    ProgramDuplicate,
    ProgramPartnerCreate,
    ProgramPartnerRead,
    ProgramPartnerUpdate,
    ProgramRead,
    ProgramReorder,
    ProgramSemesterWithCourses,
    ProgramSkillRead,
    ProgramUpdate,
    ProgramWithDetails,
)
from app.schemas.common import IdResponse, MessageResponse
from app.services.academic_service import AcademicService

router = APIRouter(prefix="/programs", tags=["Programs"])


@router.get("", response_model=dict)
async def list_programs(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur code, titre, description"),
    program_type: ProgramType | None = Query(None, alias="type", description="Filtrer par type"),
    sector_id: str | None = Query(None, alias="sector_external_id", description="Filtrer par département"),
    publication_status: PublicationStatus | None = Query(None, alias="status", description="Filtrer par statut"),
    field_id: str | None = Query(None, description="Filtrer par champ disciplinaire"),
    _: bool = Depends(PermissionChecker("programs.view")),
) -> dict:
    """Liste les programmes avec pagination et filtres."""
    service = AcademicService(db)
    query = await service.get_programs(
        search=search,
        program_type=program_type,
        sector_id=sector_id,
        status=publication_status,
        field_id=field_id,
    )
    return await paginate(db, query, pagination, Program, ProgramRead)


@router.get("/{program_id}", response_model=ProgramWithDetails)
async def get_program(
    program_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.view")),
) -> Program:
    """Récupère un programme par son ID."""
    service = AcademicService(db)
    program = await service.get_program_by_id(program_id)
    if not program:
        raise NotFoundException("Programme non trouvé")
    return program


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_program(
    program_data: ProgramCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.create")),
) -> IdResponse:
    """Crée un nouveau programme."""
    service = AcademicService(db)
    program = await service.create_program(
        code=program_data.code,
        title=program_data.title,
        slug=program_data.slug,
        type=program_data.type,
        subtitle=program_data.subtitle,
        description=program_data.description,
        teaching_methods=program_data.teaching_methods,
        cover_image_external_id=program_data.cover_image_external_id,
        sector_external_id=program_data.sector_external_id,
        coordinator_external_id=program_data.coordinator_external_id,
        field_id=program_data.field_id,
        duration_months=program_data.duration_months,
        credits=program_data.credits,
        degree_awarded=program_data.degree_awarded,
        required_degree=program_data.required_degree,
        status=program_data.status,
        display_order=program_data.display_order,
    )
    return IdResponse(id=program.id, message="Programme créé avec succès")


@router.put("/{program_id}", response_model=ProgramRead)
async def update_program(
    program_id: str,
    program_data: ProgramUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> Program:
    """Met à jour un programme."""
    service = AcademicService(db)
    update_dict = program_data.model_dump(exclude_unset=True)
    return await service.update_program(program_id, **update_dict)


@router.delete("/{program_id}", response_model=MessageResponse)
async def delete_program(
    program_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.delete")),
) -> MessageResponse:
    """Supprime un programme."""
    service = AcademicService(db)
    await service.delete_program(program_id)
    return MessageResponse(message="Programme supprimé avec succès")


@router.post("/{program_id}/toggle-active", response_model=ProgramRead)
async def toggle_program_status(
    program_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> ProgramRead:
    """Bascule le statut de publication d'un programme entre 'published' et 'draft'."""
    service = AcademicService(db)
    # Récupérer le programme actuel
    program = await service.get_program_by_id(program_id)
    if not program:
        raise NotFoundException("Programme non trouvé")
    # Basculer le statut
    new_status = PublicationStatus.draft if program.status == PublicationStatus.published else PublicationStatus.published
    updated = await service.toggle_program_status(program_id, new_status)
    return ProgramRead.model_validate(updated)


@router.post("/{program_id}/duplicate", response_model=ProgramWithDetails, status_code=status.HTTP_201_CREATED)
async def duplicate_program(
    program_id: str,
    duplicate_data: ProgramDuplicate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.create")),
) -> Program:
    """Duplique un programme existant."""
    service = AcademicService(db)
    return await service.duplicate_program(
        program_id=program_id,
        new_code=duplicate_data.new_code,
        new_title=duplicate_data.new_title,
        new_slug=duplicate_data.new_slug,
    )


@router.put("/reorder", response_model=list[ProgramRead])
async def reorder_programs(
    reorder_data: ProgramReorder,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> list[Program]:
    """Réordonne les programmes."""
    service = AcademicService(db)
    return await service.reorder_programs(reorder_data.program_ids)


# =============================================================================
# PROGRAM SEMESTERS
# =============================================================================


@router.get("/{program_id}/semesters", response_model=list[ProgramSemesterWithCourses])
async def get_program_semesters(
    program_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.view")),
) -> list:
    """Récupère les semestres d'un programme."""
    service = AcademicService(db)
    program = await service.get_program_by_id(program_id)
    if not program:
        raise NotFoundException("Programme non trouvé")
    return program.semesters


# =============================================================================
# PROGRAM SKILLS
# =============================================================================


@router.get("/{program_id}/skills", response_model=list[ProgramSkillRead])
async def get_program_skills(
    program_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.view")),
) -> list:
    """Récupère les compétences d'un programme."""
    service = AcademicService(db)
    program = await service.get_program_by_id(program_id)
    if not program:
        raise NotFoundException("Programme non trouvé")
    return program.skills


# =============================================================================
# PROGRAM CAREER OPPORTUNITIES
# =============================================================================


@router.get("/{program_id}/career-opportunities", response_model=list[ProgramCareerOpportunityRead])
async def get_program_career_opportunities(
    program_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.view")),
) -> list:
    """Récupère les débouchés d'un programme."""
    service = AcademicService(db)
    program = await service.get_program_by_id(program_id)
    if not program:
        raise NotFoundException("Programme non trouvé")
    return program.career_opportunities


# =============================================================================
# PROGRAM CAMPUSES
# =============================================================================


@router.get("/{program_id}/campuses", response_model=list[str])
async def get_program_campuses(
    program_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.view")),
) -> list[str]:
    """Récupère les IDs de campus d'un programme."""
    service = AcademicService(db)
    return await service.get_program_campuses(program_id)


@router.post("/{program_id}/campuses", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_campus_to_program(
    program_id: str,
    campus_data: ProgramCampusCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> MessageResponse:
    """Ajoute un campus à un programme."""
    service = AcademicService(db)
    await service.add_campus_to_program(program_id, campus_data.campus_external_id)
    return MessageResponse(message="Campus ajouté au programme avec succès")


@router.delete("/{program_id}/campuses/{campus_id}", response_model=MessageResponse)
async def remove_campus_from_program(
    program_id: str,
    campus_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> MessageResponse:
    """Retire un campus d'un programme."""
    service = AcademicService(db)
    await service.remove_campus_from_program(program_id, campus_id)
    return MessageResponse(message="Campus retiré du programme avec succès")


# =============================================================================
# PROGRAM PARTNERS
# =============================================================================


@router.get("/{program_id}/partners", response_model=list[ProgramPartnerRead])
async def get_program_partners(
    program_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.view")),
) -> list:
    """Récupère les partenaires d'un programme."""
    service = AcademicService(db)
    return await service.get_program_partners(program_id)


@router.post("/{program_id}/partners", response_model=ProgramPartnerRead, status_code=status.HTTP_201_CREATED)
async def add_partner_to_program(
    program_id: str,
    partner_data: ProgramPartnerCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
):
    """Ajoute un partenaire à un programme."""
    service = AcademicService(db)
    return await service.add_partner_to_program(
        program_id=program_id,
        partner_external_id=partner_data.partner_external_id,
        partnership_type=partner_data.partnership_type,
    )


@router.put("/{program_id}/partners/{partner_id}", response_model=ProgramPartnerRead)
async def update_program_partner(
    program_id: str,
    partner_id: str,
    partner_data: ProgramPartnerUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
):
    """Met à jour un partenariat de programme."""
    service = AcademicService(db)
    update_dict = partner_data.model_dump(exclude_unset=True)
    return await service.update_program_partner(program_id, partner_id, **update_dict)


@router.delete("/{program_id}/partners/{partner_id}", response_model=MessageResponse)
async def remove_partner_from_program(
    program_id: str,
    partner_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> MessageResponse:
    """Retire un partenaire d'un programme."""
    service = AcademicService(db)
    await service.remove_partner_from_program(program_id, partner_id)
    return MessageResponse(message="Partenaire retiré du programme avec succès")
