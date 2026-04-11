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
    download: bool = Query(
        False,
        description="Si true, force le téléchargement (Content-Disposition: attachment). Par défaut le fichier est affiché inline.",
    ),
):
    """
    Sert un fichier média (accès public).

    Par défaut le fichier est retourné avec `Content-Disposition: inline`
    pour permettre son affichage direct dans le navigateur (balises <img>,
    <video>, <iframe> pour les PDF, etc.). Ajouter `?download=1` pour
    forcer le téléchargement.

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
        content_disposition_type="attachment" if download else "inline",
    )
