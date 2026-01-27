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
    MediaRead,
)
from app.services.media_service import MediaService

router = APIRouter(prefix="/albums", tags=["Albums"])


def _album_to_schema(album: Album) -> AlbumWithMedia:
    """Convertit un Album SQLAlchemy en schéma Pydantic AlbumWithMedia."""
    return AlbumWithMedia(
        id=album.id,
        title=album.title,
        description=album.description,
        status=album.status,
        created_at=album.created_at,
        updated_at=album.updated_at,
        media_items=[MediaRead.model_validate(m) for m in album.media_items],
    )


def _album_to_read_schema(album: Album) -> AlbumRead:
    """Convertit un Album SQLAlchemy en schéma Pydantic AlbumRead."""
    return AlbumRead.model_validate(album)


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
    return await paginate(db, query, pagination, Album, AlbumRead)


@router.get("/{album_id}", response_model=AlbumWithMedia)
async def get_album(
    album_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.view")),
) -> AlbumWithMedia:
    """Récupère un album par son ID."""
    service = MediaService(db)
    album = await service.get_album_by_id(album_id)
    if not album:
        from app.core.exceptions import NotFoundException

        raise NotFoundException("Album non trouvé")
    return _album_to_schema(album)


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
) -> AlbumRead:
    """Met à jour un album."""
    service = MediaService(db)
    update_dict = album_data.model_dump(exclude_unset=True)
    album = await service.update_album(album_id, **update_dict)
    return _album_to_read_schema(album)


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
) -> AlbumWithMedia:
    """Ajoute des médias à un album."""
    service = MediaService(db)
    album = await service.add_media_to_album(album_id, media_data.media_ids)
    return _album_to_schema(album)


@router.delete("/{album_id}/media/{media_id}", response_model=AlbumWithMedia)
async def remove_media_from_album(
    album_id: str,
    media_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.edit")),
) -> AlbumWithMedia:
    """Retire un média d'un album."""
    service = MediaService(db)
    album = await service.remove_media_from_album(album_id, media_id)
    return _album_to_schema(album)


@router.put("/{album_id}/media/reorder", response_model=AlbumWithMedia)
async def reorder_album_media(
    album_id: str,
    reorder_data: AlbumMediaReorder,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.edit")),
) -> AlbumWithMedia:
    """Réordonne les médias d'un album."""
    service = MediaService(db)
    album = await service.reorder_album_media(album_id, reorder_data.media_order)
    return _album_to_schema(album)
