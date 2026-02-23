"""
Router Public - Candidatures spontanées
========================================

Endpoints publics pour soumettre une candidature spontanée (enseignant, etc.)
et uploader un document (CV) sans authentification.
"""

from fastapi import APIRouter, File, UploadFile, status
from pydantic import BaseModel

from app.core.dependencies import DbSession
from app.core.exceptions import ValidationException
from app.schemas.application import ApplicationCreate
from app.services.application_service import ApplicationService
from app.services.media_service import MediaService

router = APIRouter(prefix="/applications", tags=["Applications"])


# ── Schémas de réponse ──────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    """Réponse après upload d'un document public."""

    id: str
    url: str


class SpontaneousApplicationResponse(BaseModel):
    """Réponse après soumission d'une candidature spontanée."""

    id: str
    reference_number: str
    message: str


# ── Endpoints ────────────────────────────────────────────────────────

@router.post(
    "/upload-document",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document_public(
    db: DbSession,
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """
    Upload public d'un document (PDF uniquement, max 5 Mo).

    Utilisé pour les candidatures spontanées.
    Retourne un media_id à inclure dans la soumission de candidature.
    """
    # Validation stricte : PDF uniquement
    if file.content_type != "application/pdf":
        raise ValidationException("Seuls les fichiers PDF sont acceptés")

    # Vérification taille (5 Mo max)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise ValidationException("Le fichier ne doit pas dépasser 5 Mo")
    await file.seek(0)

    service = MediaService(db)
    media = await service.upload_file(file=file, folder="candidatures")

    return DocumentUploadResponse(
        id=media.id,
        url=f"/api/public/media/{media.id}/download",
    )


@router.post(
    "/spontaneous",
    response_model=SpontaneousApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_spontaneous_application(
    application_data: ApplicationCreate,
    db: DbSession,
) -> SpontaneousApplicationResponse:
    """
    Soumet une candidature spontanée (sans appel à candidature associé).

    Le champ call_id est forcé à None. La candidature est identifiable
    dans le tableau de bord admin par l'absence de call_id.
    """
    service = ApplicationService(db)

    data = application_data.model_dump(exclude_unset=True)
    data["call_id"] = None

    application = await service.create_application(data)

    return SpontaneousApplicationResponse(
        id=application.id,
        reference_number=application.reference_number,
        message="Candidature soumise avec succès",
    )
