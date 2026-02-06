"""
Router Admin - Campus
=====================

Endpoints CRUD pour la gestion des campus.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.campus import Campus
from app.schemas.campus import (
    CampusCreate,
    CampusMediaLibraryCreate,
    CampusPartnerCreate,
    CampusPartnerRead,
    CampusPartnerUpdate,
    CampusRead,
    CampusTeamCreate,
    CampusTeamRead,
    CampusTeamUpdate,
    CampusUpdate,
    CampusWithTeam,
)
from app.schemas.common import IdResponse, MessageResponse
from app.services.campus_service import CampusService

router = APIRouter(prefix="/campuses", tags=["Campuses"])


@router.get("", response_model=dict)
async def list_campuses(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur code, nom, ville"),
    country_id: str | None = Query(None, description="Filtrer par pays"),
    active: bool | None = Query(None, description="Filtrer par statut actif"),
    is_headquarters: bool | None = Query(None, description="Filtrer par siège principal"),
    _: bool = Depends(PermissionChecker("campuses.view")),
) -> dict:
    """Liste les campus avec pagination et filtres."""
    service = CampusService(db)
    query = await service.get_campuses(
        search=search,
        country_id=country_id,
        active=active,
        is_headquarters=is_headquarters,
    )
    return await paginate(db, query, pagination, Campus, CampusRead)


@router.get("/{campus_id}", response_model=CampusWithTeam)
async def get_campus(
    campus_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.view")),
) -> Campus:
    """Récupère un campus par son ID."""
    service = CampusService(db)
    campus = await service.get_campus_by_id(campus_id)
    if not campus:
        raise NotFoundException("Campus non trouvé")
    return campus


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_campus(
    campus_data: CampusCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.create")),
) -> IdResponse:
    """Crée un nouveau campus."""
    service = CampusService(db)
    campus = await service.create_campus(
        code=campus_data.code,
        name=campus_data.name,
        description=campus_data.description,
        cover_image_external_id=campus_data.cover_image_external_id,
        country_external_id=campus_data.country_external_id,
        head_external_id=campus_data.head_external_id,
        album_external_id=campus_data.album_external_id,
        email=campus_data.email,
        phone=campus_data.phone,
        city=campus_data.city,
        address=campus_data.address,
        postal_code=campus_data.postal_code,
        latitude=campus_data.latitude,
        longitude=campus_data.longitude,
        is_headquarters=campus_data.is_headquarters,
        active=campus_data.active,
    )
    return IdResponse(id=campus.id, message="Campus créé avec succès")


@router.put("/{campus_id}", response_model=CampusRead)
async def update_campus(
    campus_id: str,
    campus_data: CampusUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
) -> Campus:
    """Met à jour un campus."""
    service = CampusService(db)
    update_dict = campus_data.model_dump(exclude_unset=True)
    return await service.update_campus(campus_id, **update_dict)


@router.delete("/{campus_id}", response_model=MessageResponse)
async def delete_campus(
    campus_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.delete")),
) -> MessageResponse:
    """Supprime un campus."""
    service = CampusService(db)
    await service.delete_campus(campus_id)
    return MessageResponse(message="Campus supprimé avec succès")


@router.post("/{campus_id}/toggle-active", response_model=CampusRead)
async def toggle_campus_active(
    campus_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
) -> Campus:
    """Bascule le statut actif d'un campus."""
    service = CampusService(db)
    return await service.toggle_campus_active(campus_id)


# =============================================================================
# CAMPUS TEAM
# =============================================================================


@router.get("/team/user/{user_id}", response_model=list[CampusTeamRead])
async def get_user_campus_affectations(
    user_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.view")),
) -> list:
    """Récupère les affectations campus d'un utilisateur."""
    from app.models.campus import CampusTeam

    service = CampusService(db)
    query = await service.get_campus_team()
    query = query.where(CampusTeam.user_external_id == user_id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{campus_id}/team", response_model=list[CampusTeamRead])
async def get_campus_team(
    campus_id: str,
    db: DbSession,
    current_user: CurrentUser,
    active: bool | None = Query(None, description="Filtrer par statut actif"),
    _: bool = Depends(PermissionChecker("campuses.view")),
) -> list:
    """Récupère l'équipe d'un campus."""
    service = CampusService(db)

    # Vérifier que le campus existe
    campus = await service.get_campus_by_id(campus_id)
    if not campus:
        raise NotFoundException("Campus non trouvé")

    query = await service.get_campus_team(campus_id=campus_id, active=active)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/{campus_id}/team", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def add_campus_team_member(
    campus_id: str,
    team_data: CampusTeamCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
) -> IdResponse:
    """Ajoute un membre à l'équipe d'un campus."""
    service = CampusService(db)

    # Vérifier que le campus existe
    campus = await service.get_campus_by_id(campus_id)
    if not campus:
        raise NotFoundException("Campus non trouvé")

    team_member = await service.create_team_member(
        campus_id=campus_id,
        user_external_id=team_data.user_external_id,
        position=team_data.position,
        display_order=team_data.display_order,
        start_date=team_data.start_date,
        end_date=team_data.end_date,
        active=team_data.active,
    )
    return IdResponse(id=team_member.id, message="Membre ajouté à l'équipe avec succès")


@router.put("/{campus_id}/team/{member_id}", response_model=CampusTeamRead)
async def update_campus_team_member(
    campus_id: str,
    member_id: str,
    team_data: CampusTeamUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
) -> CampusTeamRead:
    """Met à jour un membre de l'équipe d'un campus."""
    service = CampusService(db)

    # Vérifier que le campus existe
    campus = await service.get_campus_by_id(campus_id)
    if not campus:
        raise NotFoundException("Campus non trouvé")

    update_dict = team_data.model_dump(exclude_unset=True)
    return await service.update_team_member(member_id, **update_dict)


@router.delete("/{campus_id}/team/{member_id}", response_model=MessageResponse)
async def delete_campus_team_member(
    campus_id: str,
    member_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
) -> MessageResponse:
    """Supprime un membre de l'équipe d'un campus."""
    service = CampusService(db)

    # Vérifier que le campus existe
    campus = await service.get_campus_by_id(campus_id)
    if not campus:
        raise NotFoundException("Campus non trouvé")

    await service.delete_team_member(member_id)
    return MessageResponse(message="Membre retiré de l'équipe avec succès")


# =============================================================================
# CAMPUS PARTNERS
# =============================================================================


@router.get("/{campus_id}/partners", response_model=list[CampusPartnerRead])
async def get_campus_partners(
    campus_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.view")),
) -> list:
    """Récupère les partenaires d'un campus."""
    service = CampusService(db)
    return await service.get_campus_partners(campus_id)


@router.post("/{campus_id}/partners", response_model=CampusPartnerRead, status_code=status.HTTP_201_CREATED)
async def add_campus_partner(
    campus_id: str,
    partner_data: CampusPartnerCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
):
    """Ajoute un partenaire à un campus."""
    service = CampusService(db)
    return await service.add_partner_to_campus(
        campus_id=campus_id,
        partner_external_id=partner_data.partner_external_id,
        start_date=partner_data.start_date,
        end_date=partner_data.end_date,
    )


@router.put("/{campus_id}/partners/{partner_id}", response_model=CampusPartnerRead)
async def update_campus_partner(
    campus_id: str,
    partner_id: str,
    partner_data: CampusPartnerUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
):
    """Met à jour un partenariat de campus."""
    service = CampusService(db)
    update_dict = partner_data.model_dump(exclude_unset=True)
    return await service.update_campus_partner(campus_id, partner_id, **update_dict)


@router.delete("/{campus_id}/partners/{partner_id}", response_model=MessageResponse)
async def remove_campus_partner(
    campus_id: str,
    partner_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
) -> MessageResponse:
    """Retire un partenaire d'un campus."""
    service = CampusService(db)
    await service.remove_partner_from_campus(campus_id, partner_id)
    return MessageResponse(message="Partenaire retiré du campus avec succès")


# =============================================================================
# CAMPUS MEDIA LIBRARY
# =============================================================================


@router.get("/{campus_id}/media-library", response_model=list[str])
async def get_campus_media_library(
    campus_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.view")),
) -> list[str]:
    """Récupère les IDs d'albums de la médiathèque d'un campus."""
    service = CampusService(db)
    return await service.get_campus_albums(campus_id)


@router.post("/{campus_id}/media-library", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_album_to_campus(
    campus_id: str,
    album_data: CampusMediaLibraryCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
) -> MessageResponse:
    """Ajoute un album à la médiathèque d'un campus."""
    service = CampusService(db)
    await service.add_album_to_campus(campus_id, album_data.album_external_id)
    return MessageResponse(message="Album ajouté à la médiathèque avec succès")


@router.delete("/{campus_id}/media-library/{album_id}", response_model=MessageResponse)
async def remove_album_from_campus(
    campus_id: str,
    album_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("campuses.edit")),
) -> MessageResponse:
    """Retire un album de la médiathèque d'un campus."""
    service = CampusService(db)
    await service.remove_album_from_campus(campus_id, album_id)
    return MessageResponse(message="Album retiré de la médiathèque avec succès")
