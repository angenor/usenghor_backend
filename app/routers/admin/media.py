"""
Router Admin - Médias
=====================

Endpoints pour la gestion des fichiers médias.
"""

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.pagination import PaginationParams, paginate
from app.models.base import MediaType
from app.models.media import Media
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.media import (
    MediaBulkDelete,
    MediaRead,
    MediaStatistics,
    MediaUpdate,
    MediaUploadResponse,
)
from app.services.media_service import MediaService

router = APIRouter(prefix="/media", tags=["Media"])


@router.get("", response_model=dict)
async def list_media(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur nom ou description"),
    type: MediaType | None = Query(None, description="Filtrer par type"),
    _: bool = Depends(PermissionChecker("media.view")),
) -> dict:
    """Liste les médias avec pagination et filtres."""
    service = MediaService(db)
    query = await service.get_media_list(search=search, media_type=type)
    return await paginate(db, query, pagination, Media)


@router.get("/statistics", response_model=MediaStatistics)
async def get_media_statistics(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.view")),
) -> dict:
    """Récupère les statistiques des médias."""
    service = MediaService(db)
    return await service.get_media_statistics()


@router.get("/{media_id}", response_model=MediaRead)
async def get_media(
    media_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.view")),
) -> Media:
    """Récupère un média par son ID."""
    service = MediaService(db)
    media = await service.get_media_by_id(media_id)
    if not media:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Média non trouvé")
    return media


@router.post("/upload", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    db: DbSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    folder: str = Form("general"),
    alt_text: str | None = Form(None),
    credits: str | None = Form(None),
    _: bool = Depends(PermissionChecker("media.create")),
) -> Media:
    """Upload un fichier média."""
    service = MediaService(db)
    return await service.upload_file(
        file=file,
        folder=folder,
        alt_text=alt_text,
        credits=credits,
    )


@router.post("/upload-multiple", response_model=list[MediaUploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_multiple_media(
    db: DbSession,
    current_user: CurrentUser,
    files: list[UploadFile] = File(...),
    folder: str = Form("general"),
    _: bool = Depends(PermissionChecker("media.create")),
) -> list[Media]:
    """Upload plusieurs fichiers médias."""
    service = MediaService(db)
    return await service.upload_multiple_files(files=files, folder=folder)


@router.put("/{media_id}", response_model=MediaRead)
async def update_media(
    media_id: str,
    media_data: MediaUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.edit")),
) -> Media:
    """Met à jour un média."""
    service = MediaService(db)
    update_dict = media_data.model_dump(exclude_unset=True)
    return await service.update_media(media_id, **update_dict)


@router.delete("/{media_id}", response_model=MessageResponse)
async def delete_media(
    media_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.delete")),
) -> MessageResponse:
    """Supprime un média."""
    service = MediaService(db)
    await service.delete_media(media_id)
    return MessageResponse(message="Média supprimé avec succès")


@router.post("/bulk-delete", response_model=MessageResponse)
async def bulk_delete_media(
    delete_data: MediaBulkDelete,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("media.delete")),
) -> MessageResponse:
    """Supprime plusieurs médias."""
    service = MediaService(db)
    count = await service.bulk_delete_media(delete_data.media_ids)
    return MessageResponse(message=f"{count} média(s) supprimé(s)")
