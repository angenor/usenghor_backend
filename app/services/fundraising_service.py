"""
Service Fundraising
====================

Logique métier pour la gestion des levées de fonds.
"""

from decimal import Decimal
from uuid import uuid4

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.content import News
from app.models.base import PublicationStatus
from app.models.fundraising import (
    ContributorCategory,
    Fundraiser,
    FundraiserContributor,
    FundraiserNews,
    FundraiserStatus,
)


class FundraisingService:
    """Service pour la gestion des levées de fonds."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # HELPERS
    # =========================================================================

    async def _compute_totals(self, fundraiser_id: str) -> tuple[Decimal, int]:
        """Calcule le total levé et le nombre de contributeurs."""
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(FundraiserContributor.amount), 0),
                func.count(FundraiserContributor.id),
            ).where(FundraiserContributor.fundraiser_id == fundraiser_id)
        )
        row = result.one()
        return Decimal(str(row[0])), row[1]

    def _enrich_fundraiser(
        self, fundraiser: Fundraiser, total_raised: Decimal, contributor_count: int
    ) -> dict:
        """Enrichit un objet fundraiser avec les totaux calculés."""
        goal = fundraiser.goal_amount or Decimal("1")
        progress = float(total_raised / goal * 100) if goal > 0 else 0.0
        return {
            "total_raised": total_raised,
            "progress_percentage": round(min(progress, 100.0), 2),
            "contributor_count": contributor_count,
        }

    # =========================================================================
    # FUNDRAISERS - READ
    # =========================================================================

    async def get_fundraisers(
        self,
        search: str | None = None,
        status: FundraiserStatus | None = None,
    ) -> select:
        """Construit une requête pour lister les levées de fonds."""
        query = select(Fundraiser)

        if search:
            search_filter = f"%{search}%"
            query = query.where(Fundraiser.title.ilike(search_filter))

        if status:
            query = query.where(Fundraiser.status == status)

        query = query.order_by(Fundraiser.created_at.desc())
        return query

    async def get_public_fundraisers(
        self,
        status: FundraiserStatus | None = None,
    ) -> select:
        """Construit une requête pour les levées de fonds publiques (active/completed)."""
        query = select(Fundraiser).where(
            Fundraiser.status.in_([FundraiserStatus.ACTIVE, FundraiserStatus.COMPLETED])
        )

        if status:
            query = query.where(Fundraiser.status == status)

        query = query.order_by(Fundraiser.created_at.desc())
        return query

    async def get_fundraiser_by_id(self, fundraiser_id: str) -> Fundraiser | None:
        """Récupère une levée de fonds par son ID."""
        result = await self.db.execute(
            select(Fundraiser)
            .options(selectinload(Fundraiser.contributors))
            .options(selectinload(Fundraiser.fundraiser_news))
            .where(Fundraiser.id == fundraiser_id)
        )
        return result.scalar_one_or_none()

    async def get_fundraiser_by_slug(self, slug: str) -> Fundraiser | None:
        """Récupère une levée de fonds par son slug."""
        result = await self.db.execute(
            select(Fundraiser)
            .options(selectinload(Fundraiser.contributors))
            .options(selectinload(Fundraiser.fundraiser_news))
            .where(Fundraiser.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_fundraiser_public_detail(self, slug: str) -> dict | None:
        """Récupère le détail public d'une levée de fonds avec contributeurs et actualités."""
        fundraiser = await self.get_fundraiser_by_slug(slug)
        if not fundraiser:
            return None
        if fundraiser.status == FundraiserStatus.DRAFT:
            return None

        total_raised, contributor_count = await self._compute_totals(fundraiser.id)
        enrichment = self._enrich_fundraiser(fundraiser, total_raised, contributor_count)

        # Contributeurs triés par montant décroissant
        contributors = sorted(
            fundraiser.contributors,
            key=lambda c: c.amount,
            reverse=True,
        )

        # Actualités associées (récupérer les news publiées)
        news_list = []
        if fundraiser.fundraiser_news:
            news_ids = [fn.news_id for fn in fundraiser.fundraiser_news]
            result = await self.db.execute(
                select(News).where(
                    News.id.in_(news_ids),
                    News.status == PublicationStatus.PUBLISHED,
                )
            )
            published_news = result.scalars().all()
            # Garder l'ordre de display_order
            news_order = {fn.news_id: fn.display_order for fn in fundraiser.fundraiser_news}
            published_news = sorted(published_news, key=lambda n: news_order.get(n.id, 0))
            news_list = [
                {
                    "id": n.id,
                    "title": n.title,
                    "slug": n.slug,
                    "summary": n.summary,
                    "cover_image_external_id": n.cover_image_external_id,
                    "published_at": n.published_at.isoformat() if n.published_at else None,
                }
                for n in published_news
            ]

        return {
            "id": fundraiser.id,
            "title": fundraiser.title,
            "slug": fundraiser.slug,
            "description_html": fundraiser.description_html,
            "description_en_html": fundraiser.description_en_html,
            "description_ar_html": fundraiser.description_ar_html,
            "cover_image_external_id": fundraiser.cover_image_external_id,
            "goal_amount": fundraiser.goal_amount,
            "total_raised": enrichment["total_raised"],
            "progress_percentage": enrichment["progress_percentage"],
            "status": fundraiser.status.value,
            "contributors": contributors,
            "news": news_list,
            "created_at": fundraiser.created_at,
        }

    # =========================================================================
    # FUNDRAISERS - WRITE
    # =========================================================================

    async def create_fundraiser(self, **kwargs) -> Fundraiser:
        """Crée une nouvelle levée de fonds."""
        # Vérifier l'unicité du slug
        existing = await self.db.execute(
            select(Fundraiser).where(Fundraiser.slug == kwargs.get("slug"))
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Une levée de fonds avec ce slug existe déjà")

        fundraiser = Fundraiser(id=str(uuid4()), **kwargs)
        self.db.add(fundraiser)
        await self.db.flush()
        return fundraiser

    async def update_fundraiser(self, fundraiser_id: str, **kwargs) -> Fundraiser:
        """Met à jour une levée de fonds."""
        fundraiser = await self.get_fundraiser_by_id(fundraiser_id)
        if not fundraiser:
            raise NotFoundException("Levée de fonds non trouvée")

        # Vérifier l'unicité du slug si modifié
        if "slug" in kwargs and kwargs["slug"] != fundraiser.slug:
            existing = await self.db.execute(
                select(Fundraiser).where(
                    Fundraiser.slug == kwargs["slug"],
                    Fundraiser.id != fundraiser_id,
                )
            )
            if existing.scalar_one_or_none():
                raise ConflictException("Une levée de fonds avec ce slug existe déjà")

        if kwargs:
            await self.db.execute(
                update(Fundraiser).where(Fundraiser.id == fundraiser_id).values(**kwargs)
            )
            await self.db.flush()

        return await self.get_fundraiser_by_id(fundraiser_id)

    async def delete_fundraiser(self, fundraiser_id: str) -> None:
        """Supprime une levée de fonds."""
        fundraiser = await self.get_fundraiser_by_id(fundraiser_id)
        if not fundraiser:
            raise NotFoundException("Levée de fonds non trouvée")

        await self.db.execute(
            delete(Fundraiser).where(Fundraiser.id == fundraiser_id)
        )
        await self.db.flush()

    # =========================================================================
    # CONTRIBUTORS
    # =========================================================================

    async def get_contributor_by_id(self, contributor_id: str) -> FundraiserContributor | None:
        """Récupère un contributeur par son ID."""
        result = await self.db.execute(
            select(FundraiserContributor).where(FundraiserContributor.id == contributor_id)
        )
        return result.scalar_one_or_none()

    async def add_contributor(self, fundraiser_id: str, **kwargs) -> FundraiserContributor:
        """Ajoute un contributeur à une levée de fonds."""
        fundraiser = await self.get_fundraiser_by_id(fundraiser_id)
        if not fundraiser:
            raise NotFoundException("Levée de fonds non trouvée")

        contributor = FundraiserContributor(
            id=str(uuid4()), fundraiser_id=fundraiser_id, **kwargs
        )
        self.db.add(contributor)
        await self.db.flush()
        return contributor

    async def update_contributor(self, contributor_id: str, **kwargs) -> FundraiserContributor:
        """Met à jour un contributeur."""
        contributor = await self.get_contributor_by_id(contributor_id)
        if not contributor:
            raise NotFoundException("Contributeur non trouvé")

        if kwargs:
            await self.db.execute(
                update(FundraiserContributor)
                .where(FundraiserContributor.id == contributor_id)
                .values(**kwargs)
            )
            await self.db.flush()

        return await self.get_contributor_by_id(contributor_id)

    async def delete_contributor(self, contributor_id: str) -> None:
        """Supprime un contributeur."""
        contributor = await self.get_contributor_by_id(contributor_id)
        if not contributor:
            raise NotFoundException("Contributeur non trouvé")

        await self.db.execute(
            delete(FundraiserContributor).where(FundraiserContributor.id == contributor_id)
        )
        await self.db.flush()

    # =========================================================================
    # NEWS ASSOCIATIONS
    # =========================================================================

    async def associate_news(self, fundraiser_id: str, news_id: str) -> None:
        """Associe une actualité à une levée de fonds."""
        fundraiser = await self.get_fundraiser_by_id(fundraiser_id)
        if not fundraiser:
            raise NotFoundException("Levée de fonds non trouvée")

        # Vérifier que l'association n'existe pas déjà
        result = await self.db.execute(
            select(FundraiserNews).where(
                FundraiserNews.fundraiser_id == fundraiser_id,
                FundraiserNews.news_id == news_id,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException("Cette actualité est déjà associée")

        association = FundraiserNews(
            fundraiser_id=fundraiser_id,
            news_id=news_id,
        )
        self.db.add(association)
        await self.db.flush()

    async def dissociate_news(self, fundraiser_id: str, news_id: str) -> None:
        """Dissocie une actualité d'une levée de fonds."""
        result = await self.db.execute(
            select(FundraiserNews).where(
                FundraiserNews.fundraiser_id == fundraiser_id,
                FundraiserNews.news_id == news_id,
            )
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Association non trouvée")

        await self.db.execute(
            delete(FundraiserNews).where(
                FundraiserNews.fundraiser_id == fundraiser_id,
                FundraiserNews.news_id == news_id,
            )
        )
        await self.db.flush()

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_statistics(self) -> dict:
        """Retourne les statistiques des levées de fonds."""
        # Comptes par statut
        result = await self.db.execute(
            select(
                func.count(Fundraiser.id).label("total"),
                func.count(Fundraiser.id).filter(Fundraiser.status == FundraiserStatus.DRAFT).label("draft"),
                func.count(Fundraiser.id).filter(Fundraiser.status == FundraiserStatus.ACTIVE).label("active"),
                func.count(Fundraiser.id).filter(Fundraiser.status == FundraiserStatus.COMPLETED).label("completed"),
                func.coalesce(func.sum(Fundraiser.goal_amount), 0).label("total_goal"),
            )
        )
        row = result.one()

        # Total levé (somme de tous les contributeurs)
        raised_result = await self.db.execute(
            select(func.coalesce(func.sum(FundraiserContributor.amount), 0))
        )
        total_raised = raised_result.scalar()

        return {
            "total": row.total,
            "draft": row.draft,
            "active": row.active,
            "completed": row.completed,
            "total_goal": Decimal(str(row.total_goal)),
            "total_raised": Decimal(str(total_raised)),
        }
