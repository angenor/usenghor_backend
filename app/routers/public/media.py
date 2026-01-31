"""
Router Public - Médias
======================

Endpoints publics pour l'accès aux fichiers médias.
"""

from typing import Literal

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.core.dependencies import DbSession
from app.services.media_service import MediaService

router = APIRouter(prefix="/media", tags=["Media"])


@router.get("/{media_id}/download", response_class=FileResponse)
async def download_media_public(
    media_id: str,
    db: DbSession,
    variant: Literal["low", "medium", "original"] | None = Query(
        None,
        description="Variante de l'image (low, medium, original). Si non spécifié, retourne l'original.",
    ),
):
    """
    Télécharge un fichier média (accès public).

    Cet endpoint permet d'afficher les images dans les balises <img>
    sans nécessiter d'authentification.

    Le paramètre `variant` permet de récupérer une version redimensionnée:
    - `low`: Version miniature (480px max)
    - `medium`: Version moyenne (1200px max)
    - `original`: Version originale (défaut)
    """
    service = MediaService(db)
    file_path, filename, mime_type = await service.get_download_info(
        media_id, variant=variant
    )
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=mime_type,
    )
