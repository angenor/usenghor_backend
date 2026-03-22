"""
Service Fundraising (Levées de fonds)
======================================

Logique métier pour campagnes, contributeurs, manifestations d'intérêt,
sections éditoriales et médiathèque.
"""

import csv
import io
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Select, String, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.content import News
from app.models.fundraising import (
    ContributorCategory,
    Fundraiser,
    FundraiserContributor,
    FundraiserEditorialItem,
    FundraiserEditorialSection,
    FundraiserInterestExpression,
    FundraiserMedia,
    FundraiserNews,
    FundraiserStatus,
    InterestExpressionStatus,
)


class FundraisingService:
    """Service pour la gestion des levées de fonds."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Helpers ──────────────────────────────────────────────────────

    def _resolve_media_url(self, external_id: str | None) -> str | None:
        if not external_id:
            return None
        return f"/api/public/media/{external_id}/download"

    def _compute_totals(self, fundraiser: Fundraiser) -> dict:
        """Calcule total_raised, progress_percentage, contributor_count."""
        total = sum(float(c.amount or 0) for c in fundraiser.contributors)
        goal = float(fundraiser.goal_amount or 0)
        return {
            "total_raised": total,
            "progress_percentage": round((total / goal) * 100, 1) if goal > 0 else 0,
            "contributor_count": len(fundraiser.contributors),
        }

    def _enrich_fundraiser_public(self, fundraiser: Fundraiser) -> dict:
        """Enrichit une campagne avec les totaux pour la vue publique."""
        totals = self._compute_totals(fundraiser)
        return {
            "id": fundraiser.id,
            "title": fundraiser.title,
            "slug": fundraiser.slug,
            "cover_image_url": self._resolve_media_url(fundraiser.cover_image_external_id),
            "goal_amount": float(fundraiser.goal_amount),
            "total_raised": totals["total_raised"],
            "progress_percentage": totals["progress_percentage"],
            "contributor_count": totals["contributor_count"],
            "status": fundraiser.status,
            "created_at": fundraiser.created_at,
        }

    def _enrich_fundraiser_public_detail(self, fundraiser: Fundraiser) -> dict:
        """Enrichit une campagne avec tous les détails publics."""
        totals = self._compute_totals(fundraiser)

        # Contributeurs avec logique show_amount_publicly
        contributors = []
        for c in fundraiser.contributors:
            contributors.append({
                "id": c.id,
                "name": c.name,
                "name_en": c.name_en,
                "name_ar": c.name_ar,
                "category": c.category,
                "amount": float(c.amount) if c.show_amount_publicly else None,
                "logo_url": self._resolve_media_url(c.logo_external_id),
                "display_order": c.display_order,
            })

        # Médias
        media = []
        for m in fundraiser.media_items:
            media.append({
                "id": m.id,
                "media_url": self._resolve_media_url(m.media_external_id),
                "media_external_id": m.media_external_id,
                "caption_fr": m.caption_fr,
                "caption_en": m.caption_en,
                "caption_ar": m.caption_ar,
                "display_order": m.display_order,
                "created_at": m.created_at,
            })

        return {
            "id": fundraiser.id,
            "title": fundraiser.title,
            "slug": fundraiser.slug,
            "description_html": fundraiser.description_html,
            "description_en_html": fundraiser.description_en_html,
            "description_ar_html": fundraiser.description_ar_html,
            "reason_html": fundraiser.reason_html,
            "reason_en_html": fundraiser.reason_en_html,
            "reason_ar_html": fundraiser.reason_ar_html,
            "cover_image_url": self._resolve_media_url(fundraiser.cover_image_external_id),
            "goal_amount": float(fundraiser.goal_amount),
            "total_raised": totals["total_raised"],
            "progress_percentage": totals["progress_percentage"],
            "contributor_count": totals["contributor_count"],
            "status": fundraiser.status,
            "contributors": contributors,
            "media": media,
            "news": [],  # Rempli par le routeur avec les news réelles
        }

    # ── CRUD Fundraisers ─────────────────────────────────────────────

    async def get_fundraisers(
        self,
        search: str | None = None,
        status: str | None = None,
    ) -> Select:
        """Retourne une requête paginable de campagnes."""
        query = select(Fundraiser)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Fundraiser.title.ilike(search_filter),
                    Fundraiser.slug.ilike(search_filter),
                )
            )

        if status:
            query = query.where(Fundraiser.status == status)

        query = query.order_by(Fundraiser.created_at.desc())
        return query

    async def get_published_fundraisers(
        self,
        status: str | None = None,
    ) -> Select:
        """Retourne une requête de campagnes publiées (active + completed)."""
        query = select(Fundraiser).where(
            Fundraiser.status.in_(["active", "completed"])
        )

        if status and status in ("active", "completed"):
            query = query.where(Fundraiser.status == status)

        query = query.order_by(Fundraiser.created_at.desc())
        return query

    async def get_fundraiser_by_id(self, fundraiser_id: str) -> Fundraiser | None:
        result = await self.db.execute(
            select(Fundraiser).where(Fundraiser.id == fundraiser_id)
        )
        return result.scalar_one_or_none()

    async def get_fundraiser_by_slug(self, slug: str) -> Fundraiser | None:
        result = await self.db.execute(
            select(Fundraiser).where(Fundraiser.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_fundraiser(self, **kwargs) -> Fundraiser:
        fundraiser = Fundraiser(id=str(uuid4()), **kwargs)
        self.db.add(fundraiser)
        await self.db.flush()
        return fundraiser

    async def update_fundraiser(self, fundraiser_id: str, **kwargs) -> Fundraiser:
        fundraiser = await self.get_fundraiser_by_id(fundraiser_id)
        if not fundraiser:
            raise NotFoundException("Campagne non trouvée")

        if kwargs:
            await self.db.execute(
                update(Fundraiser).where(Fundraiser.id == fundraiser_id).values(**kwargs)
            )
            await self.db.flush()

        return await self.get_fundraiser_by_id(fundraiser_id)

    async def delete_fundraiser(self, fundraiser_id: str) -> None:
        fundraiser = await self.get_fundraiser_by_id(fundraiser_id)
        if not fundraiser:
            raise NotFoundException("Campagne non trouvée")

        await self.db.execute(
            delete(Fundraiser).where(Fundraiser.id == fundraiser_id)
        )
        await self.db.flush()

    # ── CRUD Contributors ────────────────────────────────────────────

    async def get_contributors(self, fundraiser_id: str) -> list[FundraiserContributor]:
        result = await self.db.execute(
            select(FundraiserContributor)
            .where(FundraiserContributor.fundraiser_id == fundraiser_id)
            .order_by(FundraiserContributor.display_order)
        )
        return list(result.scalars().all())

    async def add_contributor(self, fundraiser_id: str, **kwargs) -> FundraiserContributor:
        fundraiser = await self.get_fundraiser_by_id(fundraiser_id)
        if not fundraiser:
            raise NotFoundException("Campagne non trouvée")

        contributor = FundraiserContributor(
            id=str(uuid4()),
            fundraiser_id=fundraiser_id,
            **kwargs,
        )
        self.db.add(contributor)
        await self.db.flush()
        return contributor

    async def update_contributor(self, contributor_id: str, **kwargs) -> FundraiserContributor:
        result = await self.db.execute(
            select(FundraiserContributor).where(FundraiserContributor.id == contributor_id)
        )
        contributor = result.scalar_one_or_none()
        if not contributor:
            raise NotFoundException("Contributeur non trouvé")

        if kwargs:
            await self.db.execute(
                update(FundraiserContributor)
                .where(FundraiserContributor.id == contributor_id)
                .values(**kwargs)
            )
            await self.db.flush()

        result = await self.db.execute(
            select(FundraiserContributor).where(FundraiserContributor.id == contributor_id)
        )
        return result.scalar_one_or_none()

    async def delete_contributor(self, contributor_id: str) -> None:
        result = await self.db.execute(
            select(FundraiserContributor).where(FundraiserContributor.id == contributor_id)
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Contributeur non trouvé")

        await self.db.execute(
            delete(FundraiserContributor).where(FundraiserContributor.id == contributor_id)
        )
        await self.db.flush()

    # ── Statistics ───────────────────────────────────────────────────

    async def get_statistics(self) -> dict:
        """Statistiques pour le dashboard admin."""
        result = await self.db.execute(
            select(
                func.count(Fundraiser.id).label("total"),
                func.count().filter(Fundraiser.status == "active").label("active"),
                func.count().filter(Fundraiser.status == "completed").label("completed"),
                func.count().filter(Fundraiser.status == "draft").label("draft"),
            )
        )
        row = result.one()

        # Total raised
        raised_result = await self.db.execute(
            select(func.coalesce(func.sum(FundraiserContributor.amount), 0))
        )
        total_raised = float(raised_result.scalar() or 0)

        # Total contributors
        contrib_result = await self.db.execute(
            select(func.count(FundraiserContributor.id))
        )
        total_contributors = contrib_result.scalar() or 0

        # Interest expressions
        interest_result = await self.db.execute(
            select(
                func.count(FundraiserInterestExpression.id).label("total"),
                func.count().filter(FundraiserInterestExpression.status == "new").label("new"),
            )
        )
        interest_row = interest_result.one()

        return {
            "total_campaigns": row.total,
            "active_campaigns": row.active,
            "completed_campaigns": row.completed,
            "draft_campaigns": row.draft,
            "total_raised": total_raised,
            "total_contributors": total_contributors,
            "total_interest_expressions": interest_row.total,
            "new_interest_expressions": interest_row[1],
        }

    async def get_global_stats(self) -> dict:
        """Statistiques agrégées publiques."""
        # Total raised (campagnes active + completed uniquement)
        raised_result = await self.db.execute(
            select(func.coalesce(func.sum(FundraiserContributor.amount), 0))
            .select_from(FundraiserContributor)
            .join(Fundraiser, FundraiserContributor.fundraiser_id == Fundraiser.id)
            .where(Fundraiser.status.in_(["active", "completed"]))
        )
        total_raised = float(raised_result.scalar() or 0)

        # Unique contributor names
        contrib_result = await self.db.execute(
            select(func.count(func.distinct(FundraiserContributor.name)))
            .select_from(FundraiserContributor)
            .join(Fundraiser, FundraiserContributor.fundraiser_id == Fundraiser.id)
            .where(Fundraiser.status.in_(["active", "completed"]))
        )
        total_contributors = contrib_result.scalar() or 0

        # Campagnes actives / complétées
        counts_result = await self.db.execute(
            select(
                func.count().filter(Fundraiser.status == "active").label("active"),
                func.count().filter(Fundraiser.status == "completed").label("completed"),
            )
        )
        counts_row = counts_result.one()

        return {
            "total_raised_all_campaigns": total_raised,
            "total_contributors": total_contributors,
            "active_campaigns_count": counts_row.active,
            "completed_campaigns_count": counts_row.completed,
        }

    async def get_all_contributors(self) -> Select:
        """Retourne une requête pour les contributeurs agrégés (toutes campagnes)."""
        # Agrégation par nom de contributeur
        query = (
            select(
                FundraiserContributor.name,
                FundraiserContributor.category,
                func.sum(FundraiserContributor.amount).label("total_amount"),
                func.bool_and(FundraiserContributor.show_amount_publicly).label("show_amount_publicly"),
                func.max(FundraiserContributor.logo_external_id.cast(String)).label("logo_external_id"),
                func.count(func.distinct(FundraiserContributor.fundraiser_id)).label("campaigns_count"),
            )
            .select_from(FundraiserContributor)
            .join(Fundraiser, FundraiserContributor.fundraiser_id == Fundraiser.id)
            .where(Fundraiser.status.in_(["active", "completed"]))
            .group_by(FundraiserContributor.name, FundraiserContributor.category)
            .order_by(func.sum(FundraiserContributor.amount).desc())
        )
        return query

    # ── News Associations ────────────────────────────────────────────

    async def associate_news(self, fundraiser_id: str, news_id: str) -> None:
        fundraiser = await self.get_fundraiser_by_id(fundraiser_id)
        if not fundraiser:
            raise NotFoundException("Campagne non trouvée")

        existing = await self.db.execute(
            select(FundraiserNews).where(
                FundraiserNews.fundraiser_id == fundraiser_id,
                FundraiserNews.news_id == news_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Actualité déjà associée")

        max_order = await self.db.execute(
            select(func.coalesce(func.max(FundraiserNews.display_order), -1))
            .where(FundraiserNews.fundraiser_id == fundraiser_id)
        )
        next_order = (max_order.scalar() or 0) + 1

        news_assoc = FundraiserNews(
            fundraiser_id=fundraiser_id,
            news_id=news_id,
            display_order=next_order,
        )
        self.db.add(news_assoc)
        await self.db.flush()

    async def dissociate_news(self, fundraiser_id: str, news_id: str) -> None:
        await self.db.execute(
            delete(FundraiserNews).where(
                FundraiserNews.fundraiser_id == fundraiser_id,
                FundraiserNews.news_id == news_id,
            )
        )
        await self.db.flush()

    async def get_fundraiser_news(self, fundraiser_id: str) -> list[dict]:
        """Récupère les actualités associées à une campagne."""
        result = await self.db.execute(
            select(FundraiserNews)
            .where(FundraiserNews.fundraiser_id == fundraiser_id)
            .order_by(FundraiserNews.display_order)
        )
        associations = result.scalars().all()

        news_list = []
        for assoc in associations:
            news_result = await self.db.execute(
                select(News).where(News.id == assoc.news_id)
            )
            news = news_result.scalar_one_or_none()
            if news:
                news_list.append({
                    "id": news.id,
                    "title": news.title,
                    "slug": news.slug,
                    "cover_image_url": self._resolve_media_url(
                        getattr(news, "cover_image_external_id", None)
                    ),
                    "published_at": getattr(news, "published_at", news.created_at),
                })
        return news_list

    # ── Interest Expressions ─────────────────────────────────────────

    async def create_or_update_interest_expression(
        self, fundraiser_id: str, full_name: str, email: str, message: str | None = None
    ) -> tuple[FundraiserInterestExpression, bool]:
        """Crée ou met à jour une manifestation d'intérêt. Retourne (expression, is_new)."""
        # Vérifier si doublon
        result = await self.db.execute(
            select(FundraiserInterestExpression).where(
                FundraiserInterestExpression.email == email,
                FundraiserInterestExpression.fundraiser_id == fundraiser_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            await self.db.execute(
                update(FundraiserInterestExpression)
                .where(FundraiserInterestExpression.id == existing.id)
                .values(full_name=full_name, message=message)
            )
            await self.db.flush()
            result = await self.db.execute(
                select(FundraiserInterestExpression)
                .where(FundraiserInterestExpression.id == existing.id)
            )
            return result.scalar_one(), False

        expression = FundraiserInterestExpression(
            id=str(uuid4()),
            fundraiser_id=fundraiser_id,
            full_name=full_name,
            email=email,
            message=message,
        )
        self.db.add(expression)
        await self.db.flush()
        return expression, True

    async def get_interest_expressions(
        self,
        fundraiser_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> Select:
        """Retourne une requête paginable de manifestations d'intérêt."""
        query = select(FundraiserInterestExpression)

        if fundraiser_id:
            query = query.where(FundraiserInterestExpression.fundraiser_id == fundraiser_id)

        if status:
            query = query.where(FundraiserInterestExpression.status == status)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    FundraiserInterestExpression.full_name.ilike(search_filter),
                    FundraiserInterestExpression.email.ilike(search_filter),
                )
            )

        query = query.order_by(FundraiserInterestExpression.created_at.desc())
        return query

    async def update_interest_status(self, expression_id: str, status: str) -> FundraiserInterestExpression:
        result = await self.db.execute(
            select(FundraiserInterestExpression)
            .where(FundraiserInterestExpression.id == expression_id)
        )
        expression = result.scalar_one_or_none()
        if not expression:
            raise NotFoundException("Manifestation d'intérêt non trouvée")

        await self.db.execute(
            update(FundraiserInterestExpression)
            .where(FundraiserInterestExpression.id == expression_id)
            .values(status=status)
        )
        await self.db.flush()

        result = await self.db.execute(
            select(FundraiserInterestExpression)
            .where(FundraiserInterestExpression.id == expression_id)
        )
        return result.scalar_one()

    async def export_interest_expressions_csv(
        self,
        fundraiser_id: str | None = None,
        status: str | None = None,
    ) -> str:
        """Exporte les manifestations d'intérêt en CSV."""
        query = (
            select(FundraiserInterestExpression, Fundraiser.title)
            .join(Fundraiser, FundraiserInterestExpression.fundraiser_id == Fundraiser.id)
        )

        if fundraiser_id:
            query = query.where(FundraiserInterestExpression.fundraiser_id == fundraiser_id)
        if status:
            query = query.where(FundraiserInterestExpression.status == status)

        query = query.order_by(FundraiserInterestExpression.created_at.desc())
        result = await self.db.execute(query)
        rows = result.all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Nom", "Email", "Message", "Campagne", "Statut", "Date"])

        for expr, fundraiser_title in rows:
            writer.writerow([
                expr.full_name,
                expr.email,
                expr.message or "",
                fundraiser_title,
                expr.status,
                expr.created_at.strftime("%Y-%m-%d") if expr.created_at else "",
            ])

        return output.getvalue()

    # ── Editorial Sections ───────────────────────────────────────────

    async def get_all_sections_with_items(self) -> list[FundraiserEditorialSection]:
        result = await self.db.execute(
            select(FundraiserEditorialSection)
            .options(selectinload(FundraiserEditorialSection.items))
            .order_by(FundraiserEditorialSection.display_order)
        )
        return list(result.scalars().all())

    async def get_active_sections_with_items(self) -> list[FundraiserEditorialSection]:
        result = await self.db.execute(
            select(FundraiserEditorialSection)
            .where(FundraiserEditorialSection.is_active.is_(True))
            .options(selectinload(FundraiserEditorialSection.items))
            .order_by(FundraiserEditorialSection.display_order)
        )
        sections = list(result.scalars().all())
        # Filtrer les items inactifs
        for section in sections:
            section.items = [item for item in section.items if item.is_active]
        return sections

    async def update_section(self, section_id: str, **kwargs) -> FundraiserEditorialSection:
        result = await self.db.execute(
            select(FundraiserEditorialSection)
            .where(FundraiserEditorialSection.id == section_id)
        )
        section = result.scalar_one_or_none()
        if not section:
            raise NotFoundException("Section non trouvée")

        if kwargs:
            await self.db.execute(
                update(FundraiserEditorialSection)
                .where(FundraiserEditorialSection.id == section_id)
                .values(**kwargs)
            )
            await self.db.flush()

        result = await self.db.execute(
            select(FundraiserEditorialSection)
            .where(FundraiserEditorialSection.id == section_id)
            .options(selectinload(FundraiserEditorialSection.items))
        )
        return result.scalar_one()

    async def create_item(self, section_id: str, **kwargs) -> FundraiserEditorialItem:
        result = await self.db.execute(
            select(FundraiserEditorialSection)
            .where(FundraiserEditorialSection.id == section_id)
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Section non trouvée")

        item = FundraiserEditorialItem(
            id=str(uuid4()),
            section_id=section_id,
            **kwargs,
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def update_item(self, item_id: str, **kwargs) -> FundraiserEditorialItem:
        result = await self.db.execute(
            select(FundraiserEditorialItem).where(FundraiserEditorialItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise NotFoundException("Item non trouvé")

        if kwargs:
            await self.db.execute(
                update(FundraiserEditorialItem)
                .where(FundraiserEditorialItem.id == item_id)
                .values(**kwargs)
            )
            await self.db.flush()

        result = await self.db.execute(
            select(FundraiserEditorialItem).where(FundraiserEditorialItem.id == item_id)
        )
        return result.scalar_one()

    async def delete_item(self, item_id: str) -> None:
        result = await self.db.execute(
            select(FundraiserEditorialItem).where(FundraiserEditorialItem.id == item_id)
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Item non trouvé")

        await self.db.execute(
            delete(FundraiserEditorialItem).where(FundraiserEditorialItem.id == item_id)
        )
        await self.db.flush()

    # ── Fundraiser Media ─────────────────────────────────────────────

    async def list_media(self, fundraiser_id: str) -> list[FundraiserMedia]:
        result = await self.db.execute(
            select(FundraiserMedia)
            .where(FundraiserMedia.fundraiser_id == fundraiser_id)
            .order_by(FundraiserMedia.display_order)
        )
        return list(result.scalars().all())

    async def add_media(self, fundraiser_id: str, **kwargs) -> FundraiserMedia:
        fundraiser = await self.get_fundraiser_by_id(fundraiser_id)
        if not fundraiser:
            raise NotFoundException("Campagne non trouvée")

        media = FundraiserMedia(
            id=str(uuid4()),
            fundraiser_id=fundraiser_id,
            **kwargs,
        )
        self.db.add(media)
        await self.db.flush()
        return media

    async def update_media(self, media_id: str, **kwargs) -> FundraiserMedia:
        result = await self.db.execute(
            select(FundraiserMedia).where(FundraiserMedia.id == media_id)
        )
        media = result.scalar_one_or_none()
        if not media:
            raise NotFoundException("Média non trouvé")

        if kwargs:
            await self.db.execute(
                update(FundraiserMedia)
                .where(FundraiserMedia.id == media_id)
                .values(**kwargs)
            )
            await self.db.flush()

        result = await self.db.execute(
            select(FundraiserMedia).where(FundraiserMedia.id == media_id)
        )
        return result.scalar_one()

    async def remove_media(self, media_id: str) -> None:
        result = await self.db.execute(
            select(FundraiserMedia).where(FundraiserMedia.id == media_id)
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Média non trouvé")

        await self.db.execute(
            delete(FundraiserMedia).where(FundraiserMedia.id == media_id)
        )
        await self.db.flush()
