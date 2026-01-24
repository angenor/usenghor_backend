"""
Router Public - Editorial
=========================

Endpoints publics pour accéder aux contenus éditoriaux.
"""

from fastapi import APIRouter, Query

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.schemas.editorial import ContentPublic
from app.services.editorial_service import EditorialService

router = APIRouter(prefix="/editorial", tags=["Editorial"])


@router.get("/content/{key}", response_model=ContentPublic)
async def get_content_by_key(
    key: str,
    db: DbSession,
) -> ContentPublic:
    """
    Récupère un contenu par sa clé.

    Utile pour afficher des valeurs de configuration sur le site
    (statistiques, paramètres, textes dynamiques, etc.)
    """
    service = EditorialService(db)
    content = await service.get_public_content_by_key(key)
    if not content:
        raise NotFoundException("Contenu non trouvé")
    return ContentPublic.model_validate(content)


@router.get("/contents", response_model=list[ContentPublic])
async def get_contents_by_keys(
    keys: str = Query(..., description="Clés séparées par des virgules"),
    db: DbSession = None,
) -> list[ContentPublic]:
    """
    Récupère plusieurs contenus par leurs clés.

    Permet de récupérer plusieurs valeurs en une seule requête.
    """
    service = EditorialService(db)
    key_list = [k.strip() for k in keys.split(",") if k.strip()]
    contents = await service.get_contents_by_keys(key_list)
    return [ContentPublic.model_validate(c) for c in contents]


@router.get("/category/{category_code}", response_model=list[ContentPublic])
async def get_contents_by_category(
    category_code: str,
    db: DbSession,
) -> list[ContentPublic]:
    """
    Récupère tous les contenus d'une catégorie.

    Utile pour charger tous les contenus d'un groupe
    (ex: statistiques de l'université, paramètres d'une page, etc.)
    """
    service = EditorialService(db)
    contents = await service.get_public_contents_by_category(category_code)
    return [ContentPublic.model_validate(c) for c in contents]


@router.get("/year/{year}", response_model=list[ContentPublic])
async def get_contents_by_year(
    year: int,
    db: DbSession,
) -> list[ContentPublic]:
    """
    Récupère tous les contenus associés à une année.

    Utile pour afficher des statistiques annuelles
    (ex: nombre d'étudiants 2024, diplômés 2023, etc.)
    """
    service = EditorialService(db)
    contents = await service.get_public_contents_by_year(year)
    return [ContentPublic.model_validate(c) for c in contents]
