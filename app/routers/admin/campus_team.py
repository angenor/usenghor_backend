"""
Router Admin - Équipes Campus
=============================

Endpoints CRUD pour la gestion des équipes de campus.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.campus import CampusTeam
from app.schemas.campus import (
    CampusTeamCreate,
    CampusTeamRead,
    CampusTeamReorder,
    CampusTeamUpdate,
)
from app.schemas.common import IdResponse, MessageResponse
from app.services.campus_service import CampusService

router = APIRouter(prefix="/campus-team", tags=["Campus Team"])


@router.get("", response_model=dict)
async def list_campus_team(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(100, ge=1, le=200, description="Nombre d'éléments par page"),
    campus_id: str | None = Query(None, description="Filtrer par campus"),
    active: bool | None = Query(None, description="Filtrer par statut actif"),
    _: bool = Depends(PermissionChecker("campuses.view")),
) -> dict:
    """Liste les membres d'équipe avec pagination et filtres."""
    service = CampusService(db)
    query = await service.get_campus_team(campus_id=campus_id, active=active)

    # Pagination personnalisée avec tri par display_order
    pagination = PaginationParams(page=page, limit=limit, sort_by="display_order", sort_order="asc")
    return await paginate(db, query, pagination, CampusTeam, CampusTeamRead)


@router.get("/{team_member_id}", response_model=CampusTeamRead)
async def get_team_member(
    team_member_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.view")),
) -> CampusTeam:
    """Récupère un membre d'équipe par son ID."""
    service = CampusService(db)
    team_member = await service.get_team_member_by_id(team_member_id)
    if not team_member:
        raise NotFoundException("Membre d'équipe non trouvé")
    return team_member


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_team_member(
    team_data: CampusTeamCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
) -> IdResponse:
    """Ajoute un membre à l'équipe d'un campus."""
    service = CampusService(db)
    team_member = await service.create_team_member(
        campus_id=team_data.campus_id,
        user_external_id=team_data.user_external_id,
        position=team_data.position,
        display_order=team_data.display_order,
        start_date=team_data.start_date,
        end_date=team_data.end_date,
        active=team_data.active,
    )
    return IdResponse(id=team_member.id, message="Membre ajouté à l'équipe avec succès")


@router.put("/{team_member_id}", response_model=CampusTeamRead)
async def update_team_member(
    team_member_id: str,
    team_data: CampusTeamUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
) -> CampusTeam:
    """Met à jour un membre d'équipe."""
    service = CampusService(db)
    update_dict = team_data.model_dump(exclude_unset=True)
    return await service.update_team_member(team_member_id, **update_dict)


@router.delete("/{team_member_id}", response_model=MessageResponse)
async def delete_team_member(
    team_member_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
) -> MessageResponse:
    """Supprime un membre d'équipe."""
    service = CampusService(db)
    await service.delete_team_member(team_member_id)
    return MessageResponse(message="Membre retiré de l'équipe avec succès")


@router.post("/{team_member_id}/toggle-active", response_model=CampusTeamRead)
async def toggle_team_member_active(
    team_member_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
) -> CampusTeam:
    """Bascule le statut actif d'un membre d'équipe."""
    service = CampusService(db)
    return await service.toggle_team_member_active(team_member_id)


@router.put("/reorder", response_model=list[CampusTeamRead])
async def reorder_team_members(
    reorder_data: CampusTeamReorder,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
) -> list[CampusTeam]:
    """Réordonne les membres d'équipe."""
    service = CampusService(db)
    return await service.reorder_team_members(reorder_data.team_member_ids)
