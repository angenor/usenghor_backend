"""
Utilitaires de pagination
=========================

Classes et fonctions pour la pagination des requêtes.
"""

from math import ceil
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PaginationParams:
    """Paramètres de pagination injectables via Depends."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Numéro de page"),
        limit: int = Query(20, ge=1, le=500, description="Nombre d'éléments par page"),
        sort_by: str = Query("created_at", description="Champ de tri"),
        sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Ordre de tri"),
    ):
        self.page = page
        self.limit = limit
        self.sort_by = sort_by
        self.sort_order = sort_order

    @property
    def offset(self) -> int:
        """Calcule l'offset pour la requête SQL."""
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    """Réponse paginée générique typée."""

    items: list[T]
    total: int
    page: int
    limit: int
    pages: int

    model_config = {"from_attributes": True}


async def paginate(
    db: AsyncSession,
    query: Select,
    pagination: PaginationParams,
    model_class: type,
    schema_class: type | None = None,
) -> dict:
    """
    Pagine une requête SQLAlchemy.

    Args:
        db: Session de base de données.
        query: Requête SQLAlchemy Select.
        pagination: Paramètres de pagination.
        model_class: Classe du modèle pour le tri.
        schema_class: Classe Pydantic optionnelle pour la conversion des items.

    Returns:
        Dictionnaire avec items, total, page, limit, pages.
    """
    # Compter le total - utiliser le modèle directement pour éviter les problèmes
    # avec les options d'eager loading dans les subqueries
    # Note: Ceci compte tous les éléments sans les filtres de la requête originale
    # Pour un comptage précis, les filtres devraient être passés séparément
    count_query = select(func.count()).select_from(model_class)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Appliquer le tri
    sort_column = getattr(model_class, pagination.sort_by, None)
    if sort_column is not None:
        if pagination.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

    # Appliquer la pagination
    query = query.offset(pagination.offset).limit(pagination.limit)

    # Exécuter la requête
    result = await db.execute(query)
    items = result.scalars().all()

    # Convertir en schémas Pydantic si spécifié
    if schema_class is not None:
        items = [schema_class.model_validate(item) for item in items]
    else:
        items = list(items)

    # Calculer le nombre de pages
    pages = ceil(total / pagination.limit) if pagination.limit > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit,
        "pages": pages,
    }
