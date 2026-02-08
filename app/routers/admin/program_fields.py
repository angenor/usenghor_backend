"""
Router Admin - Champs disciplinaires
=====================================

Endpoints CRUD pour la gestion des champs disciplinaires (certificats).
"""

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.academic import ProgramField
from app.schemas.academic import (
    ProgramFieldCreate,
    ProgramFieldRead,
    ProgramFieldReorder,
    ProgramFieldUpdate,
)
from app.schemas.common import IdResponse, MessageResponse
from app.services.academic_service import AcademicService

router = APIRouter(prefix="/program-fields", tags=["Program Fields"])


@router.get("", response_model=dict)
async def list_fields(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    _: bool = Depends(PermissionChecker("programs.view")),
) -> dict:
    """Liste les champs disciplinaires avec pagination."""
    service = AcademicService(db)
    query = await service.get_fields()
    return await paginate(db, query, pagination, ProgramField, ProgramFieldRead)


@router.get("/{field_id}", response_model=ProgramFieldRead)
async def get_field(
    field_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.view")),
) -> ProgramField:
    """Récupère un champ disciplinaire par son ID."""
    service = AcademicService(db)
    field = await service.get_field_by_id(field_id)
    if not field:
        raise NotFoundException("Champ non trouvé")
    return field


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_field(
    field_data: ProgramFieldCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> IdResponse:
    """Crée un nouveau champ disciplinaire."""
    service = AcademicService(db)
    field = await service.create_field(
        name=field_data.name,
        slug=field_data.slug,
        description=field_data.description,
        display_order=field_data.display_order,
    )
    return IdResponse(id=field.id, message="Champ créé avec succès")


@router.put("/reorder", response_model=list[ProgramFieldRead])
async def reorder_fields(
    reorder_data: ProgramFieldReorder,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> list[ProgramField]:
    """Réordonne les champs disciplinaires."""
    service = AcademicService(db)
    return await service.reorder_fields(reorder_data.field_ids)


@router.put("/{field_id}", response_model=ProgramFieldRead)
async def update_field(
    field_id: str,
    field_data: ProgramFieldUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> ProgramField:
    """Met à jour un champ disciplinaire."""
    service = AcademicService(db)
    update_dict = field_data.model_dump(exclude_unset=True)
    return await service.update_field(field_id, **update_dict)


@router.delete("/{field_id}", response_model=MessageResponse)
async def delete_field(
    field_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("programs.edit")),
) -> MessageResponse:
    """Supprime un champ disciplinaire."""
    service = AcademicService(db)
    await service.delete_field(field_id)
    return MessageResponse(message="Champ supprimé avec succès")
