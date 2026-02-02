"""
Router Public - Albums
======================

Endpoints publics pour les albums.
"""

from fastapi import APIRouter

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.models.base import PublicationStatus
from app.schemas.media import AlbumWithMedia, MediaRead
from app.services.media_service import MediaService

router = APIRouter(prefix="/albums", tags=["Albums"])


@router.get("/{album_id}", response_model=AlbumWithMedia)
async def get_album_public(
    album_id: str,
    db: DbSession,
) -> AlbumWithMedia:
    """
    Récupère un album publié par son ID avec ses médias.

    Seuls les albums publiés sont accessibles via cet endpoint.
    """
    service = MediaService(db)
    album = await service.get_album_by_id(album_id)

    if not album:
        raise NotFoundException("Album non trouvé")

    # Vérifier que l'album est publié
    if album.status != PublicationStatus.PUBLISHED:
        raise NotFoundException("Album non trouvé")

    return AlbumWithMedia(
        id=album.id,
        title=album.title,
        description=album.description,
        status=album.status,
        created_at=album.created_at,
        updated_at=album.updated_at,
        media_items=[MediaRead.model_validate(m) for m in album.media_items],
    )
