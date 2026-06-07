"""
Service FAQ
===========

Logique métier pour la FAQ : arbre public (avec repli FR), CRUD admin.
"""

from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.faq import FaqCategory, FaqEntry
from app.schemas.faq import (
    CategoriesReorderRequest,
    EntriesReorderRequest,
    FaqCategoriesAdminList,
    FaqCategoryAdmin,
    FaqCategoryCreate,
    FaqCategoryPublic,
    FaqCategoryUpdate,
    FaqEntriesAdminPage,
    FaqEntryAdminFull,
    FaqEntryAdminListItem,
    FaqEntryCreate,
    FaqEntryPublic,
    FaqEntryPublishStatus,
    FaqEntryUpdate,
    FaqTranslateRequest,
    FaqTranslateResponse,
    FaqTreePublic,
    ReorderResponse,
)
from app.services.faq_slug import generate_slug
from app.services.identity_service import IdentityService
from app.services.translation_service import (
    SUPPORTED_TARGETS,
    translate_html,
    translate_text,
)


def _coalesce(*values: str | None) -> str:
    """Retourne la première valeur non vide (None ou '' ignorés)."""
    for v in values:
        if v:
            return v
    return ""


def _serialize_entry_public(entry: FaqEntry) -> FaqEntryPublic:
    """Sérialise une entrée avec repli FR sur les champs question/answer EN/AR."""
    return FaqEntryPublic(
        id=entry.id,
        slug=entry.slug,
        question_fr=entry.question_fr,
        question_en=_coalesce(entry.question_en, entry.question_fr),
        question_ar=_coalesce(entry.question_ar, entry.question_fr),
        answer_fr_html=entry.answer_fr_html,
        answer_en_html=_coalesce(entry.answer_en_html, entry.answer_fr_html),
        answer_ar_html=_coalesce(entry.answer_ar_html, entry.answer_fr_html),
        display_order=entry.display_order,
        published_at=entry.published_at,
    )


def _serialize_category_public(category: FaqCategory) -> FaqCategoryPublic:
    return FaqCategoryPublic(
        id=category.id,
        code=category.code,
        label_fr=category.label_fr,
        label_en=_coalesce(category.label_en, category.label_fr),
        label_ar=_coalesce(category.label_ar, category.label_fr),
        description_fr=category.description_fr,
        description_en=category.description_en,
        description_ar=category.description_ar,
        display_order=category.display_order,
        entries=[
            _serialize_entry_public(e)
            for e in sorted(
                (e for e in category.entries if e.is_published),
                key=lambda e: (e.display_order, e.published_at or e.created_at),
            )
        ],
    )


def _serialize_entry_list_item(
    entry: FaqEntry, category_code: str
) -> FaqEntryAdminListItem:
    return FaqEntryAdminListItem(
        id=entry.id,
        category_id=entry.category_id,
        category_code=category_code,
        slug=entry.slug,
        question_fr=entry.question_fr,
        question_en=entry.question_en,
        question_ar=entry.question_ar,
        is_published=entry.is_published,
        published_at=entry.published_at,
        display_order=entry.display_order,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def _serialize_entry_full(
    entry: FaqEntry, category_code: str
) -> FaqEntryAdminFull:
    return FaqEntryAdminFull(
        id=entry.id,
        category_id=entry.category_id,
        category_code=category_code,
        slug=entry.slug,
        question_fr=entry.question_fr,
        question_en=entry.question_en,
        question_ar=entry.question_ar,
        is_published=entry.is_published,
        published_at=entry.published_at,
        display_order=entry.display_order,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        answer_fr_md=entry.answer_fr_md,
        answer_fr_html=entry.answer_fr_html,
        answer_en_md=entry.answer_en_md,
        answer_en_html=entry.answer_en_html,
        answer_ar_md=entry.answer_ar_md,
        answer_ar_html=entry.answer_ar_html,
        created_by=entry.created_by,
        updated_by=entry.updated_by,
    )


def _serialize_category_admin(
    category: FaqCategory, entry_count: int
) -> FaqCategoryAdmin:
    return FaqCategoryAdmin(
        id=category.id,
        code=category.code,
        label_fr=category.label_fr,
        label_en=category.label_en,
        label_ar=category.label_ar,
        description_fr=category.description_fr,
        description_en=category.description_en,
        description_ar=category.description_ar,
        display_order=category.display_order,
        is_active=category.is_active,
        entry_count=entry_count,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


class FaqService:
    """Service métier pour la FAQ."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def get_public_tree(self) -> FaqTreePublic:
        """
        Récupère l'arborescence publique (catégories actives + entrées publiées).

        Applique le tri (display_order ASC, label_fr ASC) et le repli silencieux FR.
        """
        stmt = (
            select(FaqCategory)
            .where(FaqCategory.is_active.is_(True))
            .options(selectinload(FaqCategory.entries))
            .order_by(FaqCategory.display_order.asc(), FaqCategory.label_fr.asc())
        )
        result = await self.db.execute(stmt)
        categories = result.scalars().all()

        return FaqTreePublic(
            categories=[_serialize_category_public(c) for c in categories]
        )

    # ------------------------------------------------------------------
    # Helpers internes
    # ------------------------------------------------------------------

    async def _get_category_or_404(self, category_id: str) -> FaqCategory:
        result = await self.db.execute(
            select(FaqCategory).where(FaqCategory.id == category_id)
        )
        cat = result.scalar_one_or_none()
        if cat is None:
            raise NotFoundException("Catégorie FAQ introuvable")
        return cat

    async def _get_entry_or_404(self, entry_id: str) -> FaqEntry:
        result = await self.db.execute(
            select(FaqEntry)
            .options(selectinload(FaqEntry.category))
            .where(FaqEntry.id == entry_id)
        )
        entry = result.scalar_one_or_none()
        if entry is None:
            raise NotFoundException("Entrée FAQ introuvable")
        return entry

    async def _audit(
        self,
        action: str,
        user_id: str | None,
        record_id: str,
        table_name: str,
        old_values: dict | None = None,
        new_values: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        await IdentityService(self.db).create_audit_log(
            action=action,
            user_id=user_id,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    # ------------------------------------------------------------------
    # Traduction automatique (FR -> EN/AR)
    # ------------------------------------------------------------------

    async def _autofill_entry_translations(
        self, entry: FaqEntry, *, force: bool = False
    ) -> None:
        """
        Remplit les champs EN/AR d'une entrée à partir du FR.

        Par défaut, ne touche que les champs **vides** (les corrections manuelles
        sont préservées). Avec ``force=True``, retraduit tous les champs.
        N'échoue jamais : une traduction indisponible laisse le champ tel quel.
        """
        for lang in SUPPORTED_TARGETS:
            # Question (texte court)
            q_attr = f"question_{lang}"
            if (force or not getattr(entry, q_attr)) and entry.question_fr:
                translated = await translate_text(entry.question_fr, lang)
                if translated:
                    setattr(entry, q_attr, translated)

            # Réponse — HTML (rendu public, balises préservées)
            html_attr = f"answer_{lang}_html"
            if (force or not getattr(entry, html_attr)) and entry.answer_fr_html:
                translated_html = await translate_html(entry.answer_fr_html, lang)
                if translated_html:
                    setattr(entry, html_attr, translated_html)

            # Réponse — Markdown (source d'édition)
            md_attr = f"answer_{lang}_md"
            if (force or not getattr(entry, md_attr)) and entry.answer_fr_md:
                translated_md = await translate_text(entry.answer_fr_md, lang)
                if translated_md:
                    setattr(entry, md_attr, translated_md)

    async def translate_fields(
        self, data: FaqTranslateRequest
    ) -> FaqTranslateResponse:
        """
        Traduit des champs FR -> EN/AR sans persistance.

        Utilisé par le bouton « Traduire » du formulaire admin pour pré-remplir
        (et laisser corriger) les champs EN/AR avant la sauvegarde.
        """
        response = FaqTranslateResponse()
        for lang in SUPPORTED_TARGETS:
            if data.question_fr:
                setattr(
                    response,
                    f"question_{lang}",
                    await translate_text(data.question_fr, lang),
                )
            if data.answer_fr_html:
                setattr(
                    response,
                    f"answer_{lang}_html",
                    await translate_html(data.answer_fr_html, lang),
                )
            if data.answer_fr_md:
                setattr(
                    response,
                    f"answer_{lang}_md",
                    await translate_text(data.answer_fr_md, lang),
                )
        return response

    # ------------------------------------------------------------------
    # Admin — Catégories
    # ------------------------------------------------------------------

    async def list_categories(self) -> FaqCategoriesAdminList:
        stmt = (
            select(FaqCategory, func.count(FaqEntry.id))
            .outerjoin(FaqEntry, FaqEntry.category_id == FaqCategory.id)
            .group_by(FaqCategory.id)
            .order_by(FaqCategory.display_order.asc(), FaqCategory.label_fr.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return FaqCategoriesAdminList(
            categories=[_serialize_category_admin(cat, count) for cat, count in rows]
        )

    async def get_category(self, category_id: str) -> FaqCategoryAdmin:
        cat = await self._get_category_or_404(category_id)
        count_result = await self.db.execute(
            select(func.count(FaqEntry.id)).where(FaqEntry.category_id == cat.id)
        )
        count = count_result.scalar() or 0
        return _serialize_category_admin(cat, count)

    async def create_category(
        self,
        data: FaqCategoryCreate,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> FaqCategoryAdmin:
        # Unicité du code
        existing = await self.db.execute(
            select(FaqCategory.id).where(FaqCategory.code == data.code)
        )
        if existing.scalar_one_or_none():
            raise ConflictException(f"Code de catégorie déjà utilisé : {data.code}")

        # display_order = MAX + 1
        max_result = await self.db.execute(
            select(func.coalesce(func.max(FaqCategory.display_order), -1))
        )
        next_order = (max_result.scalar() or -1) + 1

        cat = FaqCategory(
            code=data.code,
            label_fr=data.label_fr,
            label_en=data.label_en,
            label_ar=data.label_ar,
            description_fr=data.description_fr,
            description_en=data.description_en,
            description_ar=data.description_ar,
            is_active=data.is_active,
            display_order=next_order,
        )
        self.db.add(cat)
        await self.db.flush()

        await self._audit(
            "faq.category.create",
            user_id=user_id,
            record_id=cat.id,
            table_name="faq_categories",
            new_values={
                "code": cat.code,
                "label_fr": cat.label_fr,
                "is_active": cat.is_active,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(cat)
        return _serialize_category_admin(cat, 0)

    async def update_category(
        self,
        category_id: str,
        data: FaqCategoryUpdate,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> FaqCategoryAdmin:
        cat = await self._get_category_or_404(category_id)
        old = {
            "label_fr": cat.label_fr,
            "label_en": cat.label_en,
            "label_ar": cat.label_ar,
            "is_active": cat.is_active,
        }
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(cat, key, value)
        await self.db.flush()

        await self._audit(
            "faq.category.update",
            user_id=user_id,
            record_id=cat.id,
            table_name="faq_categories",
            old_values=old,
            new_values=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()

        count_result = await self.db.execute(
            select(func.count(FaqEntry.id)).where(FaqEntry.category_id == cat.id)
        )
        count = count_result.scalar() or 0
        return _serialize_category_admin(cat, count)

    async def delete_category(
        self,
        category_id: str,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        cat = await self._get_category_or_404(category_id)
        if cat.code == "general":
            raise ConflictException(
                "Catégorie protégée : 'general' ne peut pas être supprimée"
            )

        count_result = await self.db.execute(
            select(func.count(FaqEntry.id)).where(FaqEntry.category_id == cat.id)
        )
        count = count_result.scalar() or 0
        if count > 0:
            raise ConflictException(
                f"Catégorie non vide : {count} entrée(s) rattachée(s)"
            )

        old = {"code": cat.code, "label_fr": cat.label_fr}
        await self.db.delete(cat)

        await self._audit(
            "faq.category.delete",
            user_id=user_id,
            record_id=category_id,
            table_name="faq_categories",
            old_values=old,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()

    async def reorder_categories(
        self,
        request: CategoriesReorderRequest,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ReorderResponse:
        updated = 0
        changes: list[dict] = []
        for item in request.items:
            result = await self.db.execute(
                update(FaqCategory)
                .where(FaqCategory.id == item.id)
                .values(display_order=item.display_order)
            )
            if result.rowcount:
                updated += result.rowcount
                changes.append({"id": item.id, "display_order": item.display_order})

        await self._audit(
            "faq.category.reorder",
            user_id=user_id,
            record_id="bulk",
            table_name="faq_categories",
            new_values={"items": changes},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        return ReorderResponse(updated=updated)

    # ------------------------------------------------------------------
    # Admin — Entrées
    # ------------------------------------------------------------------

    async def list_entries(
        self,
        *,
        category_id: str | None = None,
        is_published: bool | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> FaqEntriesAdminPage:
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        base = select(FaqEntry).options(selectinload(FaqEntry.category))
        count_query = select(func.count(FaqEntry.id))

        if category_id:
            base = base.where(FaqEntry.category_id == category_id)
            count_query = count_query.where(FaqEntry.category_id == category_id)
        if is_published is not None:
            base = base.where(FaqEntry.is_published.is_(is_published))
            count_query = count_query.where(FaqEntry.is_published.is_(is_published))
        if q:
            pattern = f"%{q}%"
            base = base.where(FaqEntry.question_fr.ilike(pattern))
            count_query = count_query.where(FaqEntry.question_fr.ilike(pattern))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(
            base.order_by(FaqEntry.display_order.asc(), FaqEntry.created_at.asc())
            .offset(offset)
            .limit(page_size)
        )
        entries = result.scalars().all()

        items = [_serialize_entry_list_item(e, e.category.code) for e in entries]
        return FaqEntriesAdminPage(
            items=items, total=total, page=page, page_size=page_size
        )

    async def get_entry(self, entry_id: str) -> FaqEntryAdminFull:
        entry = await self._get_entry_or_404(entry_id)
        return _serialize_entry_full(entry, entry.category.code)

    async def create_entry(
        self,
        data: FaqEntryCreate,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> FaqEntryAdminFull:
        # Validation FK catégorie
        cat_result = await self.db.execute(
            select(FaqCategory).where(FaqCategory.id == data.category_id)
        )
        category = cat_result.scalar_one_or_none()
        if category is None:
            raise ValidationException(
                f"Catégorie introuvable : {data.category_id}"
            )

        # Slug
        if data.slug:
            existing = await self.db.execute(
                select(FaqEntry.id).where(FaqEntry.slug == data.slug)
            )
            if existing.scalar_one_or_none():
                raise ConflictException(f"Slug déjà utilisé : {data.slug}")
            slug = data.slug
        else:
            slug = await generate_slug(data.question_fr, self.db)

        # display_order = MAX + 1 dans la catégorie
        max_result = await self.db.execute(
            select(func.coalesce(func.max(FaqEntry.display_order), -1)).where(
                FaqEntry.category_id == data.category_id
            )
        )
        next_order = (max_result.scalar() or -1) + 1

        entry = FaqEntry(
            category_id=data.category_id,
            slug=slug,
            question_fr=data.question_fr,
            question_en=data.question_en,
            question_ar=data.question_ar,
            answer_fr_md=data.answer_fr_md,
            answer_fr_html=data.answer_fr_html,
            answer_en_md=data.answer_en_md,
            answer_en_html=data.answer_en_html,
            answer_ar_md=data.answer_ar_md,
            answer_ar_html=data.answer_ar_html,
            is_published=False,
            display_order=next_order,
            created_by=user_id,
            updated_by=user_id,
        )
        # Remplissage auto des traductions EN/AR vides (non bloquant).
        await self._autofill_entry_translations(entry)
        self.db.add(entry)
        await self.db.flush()

        await self._audit(
            "faq.entry.create",
            user_id=user_id,
            record_id=entry.id,
            table_name="faq_entries",
            new_values={
                "slug": entry.slug,
                "category_id": entry.category_id,
                "question_fr": entry.question_fr,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(entry)
        return _serialize_entry_full(entry, category.code)

    async def update_entry(
        self,
        entry_id: str,
        data: FaqEntryUpdate,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> FaqEntryAdminFull:
        entry = await self._get_entry_or_404(entry_id)
        changes = data.model_dump(exclude_unset=True)

        if "category_id" in changes and changes["category_id"] != entry.category_id:
            cat_result = await self.db.execute(
                select(FaqCategory).where(FaqCategory.id == changes["category_id"])
            )
            new_cat = cat_result.scalar_one_or_none()
            if new_cat is None:
                raise ValidationException(
                    f"Catégorie introuvable : {changes['category_id']}"
                )

        if "slug" in changes and changes["slug"] and changes["slug"] != entry.slug:
            existing = await self.db.execute(
                select(FaqEntry.id).where(
                    FaqEntry.slug == changes["slug"], FaqEntry.id != entry.id
                )
            )
            if existing.scalar_one_or_none():
                raise ConflictException(f"Slug déjà utilisé : {changes['slug']}")

        old: dict = {}
        for key, value in changes.items():
            old[key] = getattr(entry, key)
            setattr(entry, key, value)
        entry.updated_by = user_id

        # Remplissage auto des traductions EN/AR encore vides (non bloquant).
        # Les valeurs déjà saisies (corrections manuelles) sont préservées.
        await self._autofill_entry_translations(entry)

        await self.db.flush()

        await self._audit(
            "faq.entry.update",
            user_id=user_id,
            record_id=entry.id,
            table_name="faq_entries",
            old_values=old,
            new_values=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(entry, attribute_names=["category"])
        return _serialize_entry_full(entry, entry.category.code)

    async def delete_entry(
        self,
        entry_id: str,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        entry = await self._get_entry_or_404(entry_id)
        old = {"slug": entry.slug, "question_fr": entry.question_fr}
        await self.db.delete(entry)

        await self._audit(
            "faq.entry.delete",
            user_id=user_id,
            record_id=entry_id,
            table_name="faq_entries",
            old_values=old,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()

    async def set_published(
        self,
        entry_id: str,
        is_published: bool,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> FaqEntryPublishStatus:
        entry = await self._get_entry_or_404(entry_id)

        if is_published:
            if not entry.answer_fr_html:
                raise ValidationException(
                    "Impossible de publier : answer_fr_html est vide"
                )
            if not entry.category or not entry.category.is_active:
                raise ValidationException(
                    "Impossible de publier : catégorie inactive"
                )
            if entry.published_at is None:
                entry.published_at = datetime.now(timezone.utc)

        old_status = entry.is_published
        entry.is_published = is_published
        entry.updated_by = user_id
        await self.db.flush()

        action = "faq.entry.publish" if is_published else "faq.entry.unpublish"
        await self._audit(
            action,
            user_id=user_id,
            record_id=entry.id,
            table_name="faq_entries",
            old_values={"is_published": old_status},
            new_values={"is_published": is_published},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(entry)
        return FaqEntryPublishStatus(
            id=entry.id,
            is_published=entry.is_published,
            published_at=entry.published_at,
            updated_at=entry.updated_at,
        )

    async def reorder_entries(
        self,
        request: EntriesReorderRequest,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ReorderResponse:
        # Vérifier que la catégorie existe
        await self._get_category_or_404(request.category_id)

        updated = 0
        changes: list[dict] = []
        for item in request.items:
            result = await self.db.execute(
                update(FaqEntry)
                .where(
                    FaqEntry.id == item.id,
                    FaqEntry.category_id == request.category_id,
                )
                .values(display_order=item.display_order)
            )
            if result.rowcount:
                updated += result.rowcount
                changes.append({"id": item.id, "display_order": item.display_order})

        await self._audit(
            "faq.entry.reorder",
            user_id=user_id,
            record_id=request.category_id,
            table_name="faq_entries",
            new_values={"category_id": request.category_id, "items": changes},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        return ReorderResponse(updated=updated)
