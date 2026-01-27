"""
Router Public - Médias
======================

Endpoints publics pour l'accès aux fichiers médias.
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.core.dependencies import DbSession
from app.services.media_service import MediaService

router = APIRouter(prefix="/media", tags=["Media"])


@router.get("/{media_id}/download", response_class=FileResponse)
async def download_media_public(
    media_id: str,
    db: DbSession,
):
    """
    Télécharge un fichier média (accès public).

    Cet endpoint permet d'afficher les images dans les balises <img>
    sans nécessiter d'authentification.
    """
    service = MediaService(db)
    file_path, filename, mime_type = await service.get_download_info(media_id)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=mime_type,
    )
