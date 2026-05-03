"""
Router Public - FAQ
====================

Endpoint public pour l'arborescence FAQ (catégories actives + entrées publiées,
avec repli silencieux FR sur les champs trilingues).
"""

from fastapi import APIRouter, Response

from app.core.dependencies import DbSession
from app.schemas.faq import FaqTreePublic
from app.services.faq_service import FaqService

router = APIRouter(prefix="/faq", tags=["FAQ"])


@router.get("", response_model=FaqTreePublic)
async def get_faq_tree(db: DbSession, response: Response) -> FaqTreePublic:
    """
    Retourne l'arborescence complète FAQ (catégories actives, entrées publiées).

    Applique le repli silencieux FR pour les langues manquantes.
    """
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    service = FaqService(db)
    return await service.get_public_tree()
