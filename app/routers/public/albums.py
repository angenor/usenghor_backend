"""
Router Public - Albums
======================

Endpoints publics pour les albums et la médiathèque.
"""

from fastapi import APIRouter, Query

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.models.base import PublicationStatus
from app.schemas.media import AlbumWithMedia, MediaRead, PublicAlbumListResponse
from app.services.media_service import MediaService

router = APIRouter(prefix="/albums", tags=["Albums"])


@router.get("", response_model=PublicAlbumListResponse)
async def list_public_albums(
    db: DbSession,
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(24, ge=1, le=100, description="Nombre d'albums par page"),
    search: str | None = Query(None, description="Recherche textuelle sur titre et description"),
    media_type: str | None = Query(None, description="Filtre par type de média: image, video, audio, document"),
) -> PublicAlbumListResponse:
    """
    Liste les albums publiés non vides pour la médiathèque publique.

    Supporte la pagination, la recherche et le filtrage par type de média.
    """
    service = MediaService(db)
    result = await service.get_published_albums_list(
        page=page,
        limit=limit,
        search=search,
        media_type=media_type,
    )
    return PublicAlbumListResponse(**result)


@router.get("/by-slug/{slug}", response_model=AlbumWithMedia)
async def get_album_by_slug(
    slug: str,
    db: DbSession,
) -> AlbumWithMedia:
    """
    Récupère un album publié par son slug avec ses médias.

    Retourne 404 si l'album n'existe pas, est en brouillon ou est vide.
    """
    service = MediaService(db)
    album = await service.get_album_by_slug(slug)

    if not album:
        raise NotFoundException("Album non trouvé")

    # Vérifier que l'album a des médias
    if not album.media_items:
        raise NotFoundException("Album non trouvé")

    return AlbumWithMedia(
        id=album.id,
        title=album.title,
        description=album.description,
        slug=album.slug,
        status=album.status,
        created_at=album.created_at,
        updated_at=album.updated_at,
        media_items=[MediaRead.model_validate(m) for m in album.media_items],
    )


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

    if album.status != PublicationStatus.PUBLISHED:
        raise NotFoundException("Album non trouvé")

    return AlbumWithMedia(
        id=album.id,
        title=album.title,
        description=album.description,
        slug=album.slug,
        status=album.status,
        created_at=album.created_at,
        updated_at=album.updated_at,
        media_items=[MediaRead.model_validate(m) for m in album.media_items],
    )
