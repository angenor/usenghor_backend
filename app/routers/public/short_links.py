"""
Router Public - Liens courts
==============================

Endpoint public pour la résolution des liens courts.
"""

from fastapi import APIRouter

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.schemas.short_links import ShortLinkPublicResolve
from app.services.short_links_service import ShortLinkService

router = APIRouter(prefix="/short-links", tags=["Short Links"])


@router.get("/{code}", response_model=ShortLinkPublicResolve)
async def resolve_short_link(
    code: str,
    db: DbSession,
) -> ShortLinkPublicResolve:
    """Récupère l'URL de destination pour un code court."""
    service = ShortLinkService(db)
    link = await service.get_by_code(code)
    if not link:
        raise NotFoundException("Lien court non trouvé")
    return ShortLinkPublicResolve(target_url=link.target_url)
