"""
Router Admin - Semestres de programme
=====================================

Endpoints CRUD pour la gestion des semestres et cours.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.academic import ProgramSemester
from app.schemas.academic import (
    ProgramCourseCreate,
    ProgramCourseRead,
    ProgramCourseReorder,
    ProgramCourseUpdate,
    ProgramSemesterCreate,
    ProgramSemesterRead,
    ProgramSemesterUpdate,
    ProgramSemesterWithCourses,
)
from app.schemas.common import IdResponse, MessageResponse
from app.services.academic_service import AcademicService

router = APIRouter(prefix="/program-semesters", tags=["Program Semesters"])


@router.get("", response_model=dict)
async def list_semesters(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    program_id: str | None = Query(None, description="Filtrer par programme"),
    _: bool = Depends(PermissionChecker("programs.view")),
) -> dict:
    """Liste les semestres avec pagination et filtres."""
    service = AcademicService(db)
    query = await service.get_semesters(program_id=program_id)
    return await paginate(db, query, pagination, ProgramSemester, ProgramSemesterRead)


@router.get("/{semester_id}", response_model=ProgramSemesterWithCourses)
async def get_semester(
    semester_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.view")),
) -> ProgramSemesterWithCourses:
    """Récupère un semestre par son ID."""
    service = AcademicService(db)
    semester = await service.get_semester_by_id(semester_id)
    if not semester:
        raise NotFoundException("Semestre non trouvé")
    return ProgramSemesterWithCourses.model_validate(semester)


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_semester(
    semester_data: ProgramSemesterCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> IdResponse:
    """Crée un nouveau semestre."""
    service = AcademicService(db)
    semester = await service.create_semester(
        program_id=semester_data.program_id,
        number=semester_data.number,
        title=semester_data.title,
        credits=semester_data.credits,
        display_order=semester_data.display_order,
    )
    return IdResponse(id=semester.id, message="Semestre créé avec succès")


@router.put("/{semester_id}", response_model=ProgramSemesterRead)
async def update_semester(
    semester_id: str,
    semester_data: ProgramSemesterUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> ProgramSemesterRead:
    """Met à jour un semestre."""
    service = AcademicService(db)
    update_dict = semester_data.model_dump(exclude_unset=True)
    semester = await service.update_semester(semester_id, **update_dict)
    return ProgramSemesterRead.model_validate(semester)


@router.delete("/{semester_id}", response_model=MessageResponse)
async def delete_semester(
    semester_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> MessageResponse:
    """Supprime un semestre."""
    service = AcademicService(db)
    await service.delete_semester(semester_id)
    return MessageResponse(message="Semestre supprimé avec succès")


# =============================================================================
# COURSES
# =============================================================================


@router.get("/{semester_id}/courses", response_model=list[ProgramCourseRead])
async def get_semester_courses(
    semester_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.view")),
) -> list[ProgramCourseRead]:
    """Récupère les cours d'un semestre."""
    service = AcademicService(db)
    courses = await service.get_semester_courses(semester_id)
    return [ProgramCourseRead.model_validate(c) for c in courses]


@router.post("/{semester_id}/courses", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    semester_id: str,
    course_data: ProgramCourseCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> IdResponse:
    """Crée un nouveau cours."""
    service = AcademicService(db)
    course = await service.create_course(
        semester_id=semester_id,
        title=course_data.title,
        code=course_data.code,
        description=course_data.description,
        credits=course_data.credits,
        lecture_hours=course_data.lecture_hours,
        tutorial_hours=course_data.tutorial_hours,
        practical_hours=course_data.practical_hours,
        coefficient=course_data.coefficient,
        display_order=course_data.display_order,
    )
    return IdResponse(id=course.id, message="Cours créé avec succès")


@router.put("/{semester_id}/courses/{course_id}", response_model=ProgramCourseRead)
async def update_course(
    semester_id: str,
    course_id: str,
    course_data: ProgramCourseUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> ProgramCourseRead:
    """Met à jour un cours."""
    service = AcademicService(db)

    # Vérifier que le semestre existe
    semester = await service.get_semester_by_id(semester_id)
    if not semester:
        raise NotFoundException("Semestre non trouvé")

    update_dict = course_data.model_dump(exclude_unset=True)
    course = await service.update_course(course_id, **update_dict)
    return ProgramCourseRead.model_validate(course)


@router.delete("/{semester_id}/courses/{course_id}", response_model=MessageResponse)
async def delete_course(
    semester_id: str,
    course_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> MessageResponse:
    """Supprime un cours."""
    service = AcademicService(db)

    # Vérifier que le semestre existe
    semester = await service.get_semester_by_id(semester_id)
    if not semester:
        raise NotFoundException("Semestre non trouvé")

    await service.delete_course(course_id)
    return MessageResponse(message="Cours supprimé avec succès")


@router.put("/{semester_id}/courses/reorder", response_model=list[ProgramCourseRead])
async def reorder_courses(
    semester_id: str,
    reorder_data: ProgramCourseReorder,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> list[ProgramCourseRead]:
    """Réordonne les cours d'un semestre."""
    service = AcademicService(db)

    # Vérifier que le semestre existe
    semester = await service.get_semester_by_id(semester_id)
    if not semester:
        raise NotFoundException("Semestre non trouvé")

    courses = await service.reorder_courses(reorder_data.course_ids)
    return [ProgramCourseRead.model_validate(c) for c in courses]
