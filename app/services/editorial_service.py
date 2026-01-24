"""
Service Editorial
=================

Logique métier pour la gestion des contenus éditoriaux.
"""

from uuid import uuid4

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.editorial import (
    EditorialCategory,
    EditorialContent,
    EditorialContentHistory,
    EditorialValueType,
)


class EditorialService:
    """Service pour la gestion des contenus éditoriaux."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # CATEGORIES
    # =========================================================================

    async def get_categories(
        self,
        search: str | None = None,
    ) -> select:
        """Construit une requête pour lister les catégories."""
        query = select(EditorialCategory)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    EditorialCategory.code.ilike(search_filter),
                    EditorialCategory.name.ilike(search_filter),
                )
            )

        query = query.order_by(EditorialCategory.name)
        return query

    async def get_category_by_id(self, category_id: str) -> EditorialCategory | None:
        """Récupère une catégorie par son ID."""
        result = await self.db.execute(
            select(EditorialCategory)
            .options(selectinload(EditorialCategory.contents))
            .where(EditorialCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_category_by_code(self, code: str) -> EditorialCategory | None:
        """Récupère une catégorie par son code."""
        result = await self.db.execute(
            select(EditorialCategory).where(EditorialCategory.code == code)
        )
        return result.scalar_one_or_none()

    async def create_category(self, code: str, name: str, **kwargs) -> EditorialCategory:
        """Crée une nouvelle catégorie."""
        existing = await self.get_category_by_code(code)
        if existing:
            raise ConflictException(f"Une catégorie avec le code '{code}' existe déjà")

        category = EditorialCategory(
            id=str(uuid4()),
            code=code,
            name=name,
            **kwargs,
        )
        self.db.add(category)
        await self.db.flush()
        return category

    async def update_category(self, category_id: str, **kwargs) -> EditorialCategory:
        """Met à jour une catégorie."""
        category = await self.get_category_by_id(category_id)
        if not category:
            raise NotFoundException("Catégorie non trouvée")

        await self.db.execute(
            update(EditorialCategory)
            .where(EditorialCategory.id == category_id)
            .values(**kwargs)
        )
        await self.db.flush()
        return await self.get_category_by_id(category_id)

    async def delete_category(self, category_id: str) -> None:
        """Supprime une catégorie."""
        category = await self.get_category_by_id(category_id)
        if not category:
            raise NotFoundException("Catégorie non trouvée")

        await self.db.execute(
            delete(EditorialCategory).where(EditorialCategory.id == category_id)
        )
        await self.db.flush()

    async def get_categories_with_count(self) -> list[dict]:
        """Récupère les catégories avec le nombre de contenus."""
        result = await self.db.execute(
            select(
                EditorialCategory,
                func.count(EditorialContent.id).label("contents_count"),
            )
            .outerjoin(EditorialContent)
            .group_by(EditorialCategory.id)
            .order_by(EditorialCategory.name)
        )
        return [
            {
                "category": row[0],
                "contents_count": row[1],
            }
            for row in result.all()
        ]

    # =========================================================================
    # CONTENTS
    # =========================================================================

    async def get_contents(
        self,
        search: str | None = None,
        category_id: str | None = None,
        category_code: str | None = None,
        value_type: EditorialValueType | None = None,
        year: int | None = None,
        admin_editable: bool | None = None,
    ) -> select:
        """Construit une requête pour lister les contenus."""
        query = select(EditorialContent).options(
            selectinload(EditorialContent.category)
        )

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    EditorialContent.key.ilike(search_filter),
                    EditorialContent.description.ilike(search_filter),
                )
            )

        if category_id:
            query = query.where(EditorialContent.category_id == category_id)

        if category_code:
            query = query.join(EditorialCategory).where(
                EditorialCategory.code == category_code
            )

        if value_type:
            query = query.where(EditorialContent.value_type == value_type)

        if year:
            query = query.where(EditorialContent.year == year)

        if admin_editable is not None:
            query = query.where(EditorialContent.admin_editable == admin_editable)

        query = query.order_by(EditorialContent.key)
        return query

    async def get_content_by_id(self, content_id: str) -> EditorialContent | None:
        """Récupère un contenu par son ID."""
        result = await self.db.execute(
            select(EditorialContent)
            .options(
                selectinload(EditorialContent.category),
                selectinload(EditorialContent.history),
            )
            .where(EditorialContent.id == content_id)
        )
        return result.scalar_one_or_none()

    async def get_content_by_key(self, key: str) -> EditorialContent | None:
        """Récupère un contenu par sa clé."""
        result = await self.db.execute(
            select(EditorialContent)
            .options(selectinload(EditorialContent.category))
            .where(EditorialContent.key == key)
        )
        return result.scalar_one_or_none()

    async def get_contents_by_keys(self, keys: list[str]) -> list[EditorialContent]:
        """Récupère plusieurs contenus par leurs clés."""
        result = await self.db.execute(
            select(EditorialContent).where(EditorialContent.key.in_(keys))
        )
        return list(result.scalars().all())

    async def get_contents_by_category_code(
        self, category_code: str
    ) -> list[EditorialContent]:
        """Récupère tous les contenus d'une catégorie par son code."""
        result = await self.db.execute(
            select(EditorialContent)
            .join(EditorialCategory)
            .where(EditorialCategory.code == category_code)
            .order_by(EditorialContent.key)
        )
        return list(result.scalars().all())

    async def create_content(
        self,
        key: str,
        value: str | None = None,
        value_type: EditorialValueType = EditorialValueType.TEXT,
        modified_by_external_id: str | None = None,
        **kwargs,
    ) -> EditorialContent:
        """Crée un nouveau contenu."""
        existing = await self.get_content_by_key(key)
        if existing:
            raise ConflictException(f"Un contenu avec la clé '{key}' existe déjà")

        content = EditorialContent(
            id=str(uuid4()),
            key=key,
            value=value,
            value_type=value_type,
            **kwargs,
        )
        self.db.add(content)
        await self.db.flush()

        # Créer l'historique initial
        history = EditorialContentHistory(
            id=str(uuid4()),
            content_id=content.id,
            old_value=None,
            new_value=value,
            modified_by_external_id=modified_by_external_id,
        )
        self.db.add(history)
        await self.db.flush()

        return await self.get_content_by_id(content.id)

    async def update_content(
        self,
        content_id: str,
        modified_by_external_id: str | None = None,
        **kwargs,
    ) -> EditorialContent:
        """Met à jour un contenu et enregistre l'historique."""
        content = await self.get_content_by_id(content_id)
        if not content:
            raise NotFoundException("Contenu non trouvé")

        # Si la valeur change, enregistrer l'historique
        if "value" in kwargs and kwargs["value"] != content.value:
            history = EditorialContentHistory(
                id=str(uuid4()),
                content_id=content_id,
                old_value=content.value,
                new_value=kwargs["value"],
                modified_by_external_id=modified_by_external_id,
            )
            self.db.add(history)

        await self.db.execute(
            update(EditorialContent)
            .where(EditorialContent.id == content_id)
            .values(**kwargs)
        )
        await self.db.flush()
        return await self.get_content_by_id(content_id)

    async def delete_content(self, content_id: str) -> None:
        """Supprime un contenu."""
        content = await self.get_content_by_id(content_id)
        if not content:
            raise NotFoundException("Contenu non trouvé")

        await self.db.execute(
            delete(EditorialContent).where(EditorialContent.id == content_id)
        )
        await self.db.flush()

    async def bulk_update_contents(
        self,
        updates: list[dict],
        modified_by_external_id: str | None = None,
    ) -> dict:
        """Met à jour plusieurs contenus par leurs clés."""
        updated = 0
        not_found = 0
        errors = 0

        for item in updates:
            try:
                key = item.get("key")
                value = item.get("value")

                content = await self.get_content_by_key(key)
                if not content:
                    not_found += 1
                    continue

                await self.update_content(
                    content.id,
                    value=value,
                    modified_by_external_id=modified_by_external_id,
                )
                updated += 1
            except Exception:
                errors += 1

        return {
            "total": len(updates),
            "updated": updated,
            "not_found": not_found,
            "errors": errors,
        }

    # =========================================================================
    # HISTORY
    # =========================================================================

    async def get_content_history(
        self, content_id: str, limit: int = 50
    ) -> list[EditorialContentHistory]:
        """Récupère l'historique des modifications d'un contenu."""
        content = await self.get_content_by_id(content_id)
        if not content:
            raise NotFoundException("Contenu non trouvé")

        result = await self.db.execute(
            select(EditorialContentHistory)
            .where(EditorialContentHistory.content_id == content_id)
            .order_by(EditorialContentHistory.modified_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_history(self, limit: int = 50) -> list[EditorialContentHistory]:
        """Récupère les modifications récentes de tous les contenus."""
        result = await self.db.execute(
            select(EditorialContentHistory)
            .options(selectinload(EditorialContentHistory.content))
            .order_by(EditorialContentHistory.modified_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # =========================================================================
    # PUBLIC ACCESS
    # =========================================================================

    async def get_public_content_by_key(self, key: str) -> EditorialContent | None:
        """Récupère un contenu public par sa clé."""
        return await self.get_content_by_key(key)

    async def get_public_contents_by_category(
        self, category_code: str
    ) -> list[EditorialContent]:
        """Récupère les contenus publics d'une catégorie."""
        return await self.get_contents_by_category_code(category_code)

    async def get_public_contents_by_year(self, year: int) -> list[EditorialContent]:
        """Récupère les contenus publics d'une année."""
        result = await self.db.execute(
            select(EditorialContent)
            .where(EditorialContent.year == year)
            .order_by(EditorialContent.key)
        )
        return list(result.scalars().all())
