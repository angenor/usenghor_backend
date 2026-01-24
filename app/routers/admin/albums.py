"""
Router Admin - Albums
=====================

Endpoints pour la gestion des albums.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.pagination import PaginationParams, paginate
from app.models.base import PublicationStatus
from app.models.media import Album
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.media import (
    AlbumCreate,
    AlbumMediaAdd,
    AlbumMediaReorder,
    AlbumRead,
    AlbumUpdate,
    AlbumWithMedia,
)
from app.services.media_service import MediaService

router = APIRouter(prefix="/albums", tags=["Albums"])


@router.get("", response_model=dict)
async def list_albums(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur titre ou description"),
    status: PublicationStatus | None = Query(None, description="Filtrer par statut"),
    _: bool = Depends(PermissionChecker("media.view")),
) -> dict:
    """Liste les albums avec pagination et filtres."""
    service = MediaService(db)
    query = await service.get_albums(search=search, status=status)
    return await paginate(db, query, pagination, Album)


@router.get("/{album_id}", response_model=AlbumWithMedia)
async def get_album(
    album_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.view")),
) -> Album:
    """Récupère un album par son ID."""
    service = MediaService(db)
    album = await service.get_album_by_id(album_id)
    if not album:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Album non trouvé")
    return album


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_album(
    album_data: AlbumCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.create")),
) -> IdResponse:
    """Crée un nouvel album."""
    service = MediaService(db)
    album = await service.create_album(
        title=album_data.title,
        description=album_data.description,
        status=album_data.status,
    )
    return IdResponse(id=album.id, message="Album créé avec succès")


@router.put("/{album_id}", response_model=AlbumRead)
async def update_album(
    album_id: str,
    album_data: AlbumUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.edit")),
) -> Album:
    """Met à jour un album."""
    service = MediaService(db)
    update_dict = album_data.model_dump(exclude_unset=True)
    return await service.update_album(album_id, **update_dict)


@router.delete("/{album_id}", response_model=MessageResponse)
async def delete_album(
    album_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.delete")),
) -> MessageResponse:
    """Supprime un album."""
    service = MediaService(db)
    await service.delete_album(album_id)
    return MessageResponse(message="Album supprimé avec succès")


@router.post("/{album_id}/media", response_model=AlbumWithMedia)
async def add_media_to_album(
    album_id: str,
    media_data: AlbumMediaAdd,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.edit")),
) -> Album:
    """Ajoute des médias à un album."""
    service = MediaService(db)
    return await service.add_media_to_album(album_id, media_data.media_ids)


@router.delete("/{album_id}/media/{media_id}", response_model=AlbumWithMedia)
async def remove_media_from_album(
    album_id: str,
    media_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.edit")),
) -> Album:
    """Retire un média d'un album."""
    service = MediaService(db)
    return await service.remove_media_from_album(album_id, media_id)


@router.put("/{album_id}/media/reorder", response_model=AlbumWithMedia)
async def reorder_album_media(
    album_id: str,
    reorder_data: AlbumMediaReorder,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.edit")),
) -> Album:
    """Réordonne les médias d'un album."""
    service = MediaService(db)
    return await service.reorder_album_media(album_id, reorder_data.media_order)
