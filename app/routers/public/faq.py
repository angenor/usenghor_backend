"""
Router Public - FAQ
====================

Endpoint public pour l'arborescence FAQ (catégories actives + entrées publiées,
avec repli silencieux FR sur les champs trilingues).
"""

from fastapi import APIRouter, Query, Response

from app.core.dependencies import DbSession
from app.schemas.faq import FaqTreePublic
from app.services.faq_service import FaqService

router = APIRouter(prefix="/faq", tags=["FAQ"])


@router.get("", response_model=FaqTreePublic)
async def get_faq_tree(
    db: DbSession,
    response: Response,
    category_prefix: str | None = Query(
        None,
        pattern=r"^[a-z0-9_-]{1,60}$",
        description="Préfixe de code de catégorie (ex. see-)",
    ),
) -> FaqTreePublic:
    """
    Retourne l'arborescence FAQ (catégories actives, entrées publiées).

    Applique le repli silencieux FR pour les langues manquantes. Avec
    ``category_prefix``, seules les catégories dont le code commence par la
    valeur sont renvoyées (ex. ``see-`` pour la page Statut Étudiant-Entrepreneur).
    """
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    service = FaqService(db)
    return await service.get_public_tree(category_prefix=category_prefix)
