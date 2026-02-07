"""
Service Content
================

Logique métier pour la gestion des actualités et événements.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.base import PublicationStatus
from app.models.campus import Campus
from app.models.content import (
    Event,
    EventMediaLibrary,
    EventPartner,
    EventRegistration,
    News,
    NewsHighlightStatus,
    NewsMedia,
    NewsTag,
    RegistrationStatus,
    Tag,
)
from app.models.identity import User
from app.models.organization import Sector, Service
from app.models.project import Project


def add_months(date: datetime, months: int) -> datetime:
    """Ajoute des mois à une date (sans dateutil)."""
    month = date.month - 1 + months
    year = date.year + month // 12
    month = month % 12 + 1
    # Gérer les jours qui dépassent le mois
    day = min(date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                         31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date.replace(year=year, month=month, day=day)


class ContentService:
    """Service pour la gestion des actualités et événements."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # TAGS
    # =========================================================================

    async def get_tags(self, search: str | None = None) -> select:
        """Construit une requête pour lister les tags."""
        query = select(Tag)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Tag.name.ilike(search_filter),
                    Tag.slug.ilike(search_filter),
                )
            )

        query = query.order_by(Tag.name)
        return query

    async def get_tag_by_id(self, tag_id: str) -> Tag | None:
        """Récupère un tag par son ID."""
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        return result.scalar_one_or_none()

    async def get_tag_by_slug(self, slug: str) -> Tag | None:
        """Récupère un tag par son slug."""
        result = await self.db.execute(select(Tag).where(Tag.slug == slug))
        return result.scalar_one_or_none()

    async def create_tag(self, name: str, slug: str, **kwargs) -> Tag:
        """Crée un nouveau tag."""
        # Vérifier l'unicité
        existing = await self.get_tag_by_slug(slug)
        if existing:
            raise ConflictException(f"Un tag avec le slug '{slug}' existe déjà")

        result = await self.db.execute(select(Tag).where(Tag.name == name))
        if result.scalar_one_or_none():
            raise ConflictException(f"Un tag avec le nom '{name}' existe déjà")

        tag = Tag(id=str(uuid4()), name=name, slug=slug, **kwargs)
        self.db.add(tag)
        await self.db.flush()
        return tag

    async def update_tag(self, tag_id: str, **kwargs) -> Tag:
        """Met à jour un tag."""
        tag = await self.get_tag_by_id(tag_id)
        if not tag:
            raise NotFoundException("Tag non trouvé")

        # Vérifier l'unicité si modifié
        if "slug" in kwargs and kwargs["slug"] and kwargs["slug"] != tag.slug:
            existing = await self.get_tag_by_slug(kwargs["slug"])
            if existing:
                raise ConflictException(
                    f"Un tag avec le slug '{kwargs['slug']}' existe déjà"
                )

        if "name" in kwargs and kwargs["name"] and kwargs["name"] != tag.name:
            result = await self.db.execute(
                select(Tag).where(Tag.name == kwargs["name"])
            )
            if result.scalar_one_or_none():
                raise ConflictException(
                    f"Un tag avec le nom '{kwargs['name']}' existe déjà"
                )

        await self.db.execute(update(Tag).where(Tag.id == tag_id).values(**kwargs))
        await self.db.flush()
        return await self.get_tag_by_id(tag_id)

    async def delete_tag(self, tag_id: str) -> None:
        """Supprime un tag."""
        tag = await self.get_tag_by_id(tag_id)
        if not tag:
            raise NotFoundException("Tag non trouvé")

        await self.db.execute(delete(Tag).where(Tag.id == tag_id))
        await self.db.flush()

    async def merge_tags(self, source_tag_ids: list[str], target_tag_id: str) -> Tag:
        """Fusionne plusieurs tags vers un tag cible."""
        target_tag = await self.get_tag_by_id(target_tag_id)
        if not target_tag:
            raise NotFoundException("Tag cible non trouvé")

        # Transférer les associations
        for source_id in source_tag_ids:
            if source_id == target_tag_id:
                continue

            # Mettre à jour les news_tags
            await self.db.execute(
                update(NewsTag)
                .where(NewsTag.tag_id == source_id)
                .values(tag_id=target_tag_id)
            )

            # Supprimer le tag source
            await self.db.execute(delete(Tag).where(Tag.id == source_id))

        await self.db.flush()
        return target_tag

    async def get_tag_usage(self, tag_id: str) -> dict:
        """Retourne les statistiques d'utilisation d'un tag."""
        tag = await self.get_tag_by_id(tag_id)
        if not tag:
            raise NotFoundException("Tag non trouvé")

        result = await self.db.execute(
            select(func.count(NewsTag.news_id)).where(NewsTag.tag_id == tag_id)
        )
        news_count = result.scalar() or 0

        return {"tag_id": tag_id, "news_count": news_count}

    # =========================================================================
    # EVENTS
    # =========================================================================

    async def get_events(
        self,
        search: str | None = None,
        status: PublicationStatus | None = None,
        event_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        campus_id: str | None = None,
    ) -> select:
        """Construit une requête pour lister les événements."""
        query = select(Event).options(selectinload(Event.registrations))

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Event.title.ilike(search_filter),
                    Event.description.ilike(search_filter),
                    Event.venue.ilike(search_filter),
                )
            )

        if status:
            query = query.where(Event.status == status)

        if event_type:
            query = query.where(Event.type == event_type)

        if from_date:
            query = query.where(Event.start_date >= from_date)

        if to_date:
            query = query.where(Event.start_date <= to_date)

        if campus_id:
            query = query.where(Event.campus_external_id == campus_id)

        query = query.order_by(Event.start_date.desc())
        return query

    async def get_event_by_id(self, event_id: str) -> Event | None:
        """Récupère un événement par son ID."""
        result = await self.db.execute(
            select(Event)
            .options(selectinload(Event.registrations))
            .where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_event_by_slug(self, slug: str) -> Event | None:
        """Récupère un événement par son slug."""
        result = await self.db.execute(
            select(Event)
            .options(selectinload(Event.registrations))
            .where(Event.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_event(self, title: str, slug: str, **kwargs) -> Event:
        """Crée un nouvel événement."""
        existing = await self.get_event_by_slug(slug)
        if existing:
            raise ConflictException(f"Un événement avec le slug '{slug}' existe déjà")

        event = Event(id=str(uuid4()), title=title, slug=slug, **kwargs)
        self.db.add(event)
        await self.db.flush()
        return event

    async def update_event(self, event_id: str, **kwargs) -> Event:
        """Met à jour un événement."""
        event = await self.get_event_by_id(event_id)
        if not event:
            raise NotFoundException("Événement non trouvé")

        if "slug" in kwargs and kwargs["slug"] and kwargs["slug"] != event.slug:
            existing = await self.get_event_by_slug(kwargs["slug"])
            if existing:
                raise ConflictException(
                    f"Un événement avec le slug '{kwargs['slug']}' existe déjà"
                )

        await self.db.execute(
            update(Event).where(Event.id == event_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_event_by_id(event_id)

    async def delete_event(self, event_id: str) -> None:
        """Supprime un événement."""
        event = await self.get_event_by_id(event_id)
        if not event:
            raise NotFoundException("Événement non trouvé")

        await self.db.execute(delete(Event).where(Event.id == event_id))
        await self.db.flush()

    async def publish_event(self, event_id: str) -> Event:
        """Publie un événement."""
        event = await self.get_event_by_id(event_id)
        if not event:
            raise NotFoundException("Événement non trouvé")

        await self.db.execute(
            update(Event)
            .where(Event.id == event_id)
            .values(status=PublicationStatus.PUBLISHED)
        )
        await self.db.flush()
        return await self.get_event_by_id(event_id)

    async def cancel_event(self, event_id: str) -> Event:
        """Annule un événement (archive)."""
        event = await self.get_event_by_id(event_id)
        if not event:
            raise NotFoundException("Événement non trouvé")

        await self.db.execute(
            update(Event)
            .where(Event.id == event_id)
            .values(status=PublicationStatus.ARCHIVED)
        )
        await self.db.flush()
        return await self.get_event_by_id(event_id)

    async def duplicate_event(self, event_id: str, new_slug: str) -> Event:
        """Duplique un événement."""
        event = await self.get_event_by_id(event_id)
        if not event:
            raise NotFoundException("Événement non trouvé")

        existing = await self.get_event_by_slug(new_slug)
        if existing:
            raise ConflictException(f"Un événement avec le slug '{new_slug}' existe déjà")

        new_event = Event(
            id=str(uuid4()),
            title=f"{event.title} (copie)",
            slug=new_slug,
            description=event.description,
            content=event.content,
            type=event.type,
            type_other=event.type_other,
            start_date=event.start_date,
            end_date=event.end_date,
            venue=event.venue,
            address=event.address,
            city=event.city,
            latitude=event.latitude,
            longitude=event.longitude,
            is_online=event.is_online,
            video_conference_link=event.video_conference_link,
            registration_required=event.registration_required,
            max_attendees=event.max_attendees,
            cover_image_external_id=event.cover_image_external_id,
            country_external_id=event.country_external_id,
            campus_external_id=event.campus_external_id,
            service_external_id=event.service_external_id,
            status=PublicationStatus.DRAFT,
        )
        self.db.add(new_event)
        await self.db.flush()
        return new_event

    # =========================================================================
    # EVENT REGISTRATIONS
    # =========================================================================

    async def get_event_registrations(
        self, event_id: str | None = None, status: RegistrationStatus | None = None
    ) -> list[EventRegistration]:
        """Récupère les inscriptions, optionnellement filtrées par événement."""
        query = select(EventRegistration)

        if event_id:
            event = await self.get_event_by_id(event_id)
            if not event:
                raise NotFoundException("Événement non trouvé")
            query = query.where(EventRegistration.event_id == event_id)

        if status:
            query = query.where(EventRegistration.status == status)

        query = query.order_by(EventRegistration.registered_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def register_to_event(
        self, event_id: str, email: str, **kwargs
    ) -> EventRegistration:
        """Inscrit quelqu'un à un événement."""
        event = await self.get_event_by_id(event_id)
        if not event:
            raise NotFoundException("Événement non trouvé")

        # Vérifier si déjà inscrit
        result = await self.db.execute(
            select(EventRegistration).where(
                EventRegistration.event_id == event_id,
                EventRegistration.email == email,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException("Cette adresse email est déjà inscrite")

        # Vérifier la capacité
        if event.max_attendees:
            count_result = await self.db.execute(
                select(func.count(EventRegistration.id)).where(
                    EventRegistration.event_id == event_id,
                    EventRegistration.status != RegistrationStatus.CANCELLED,
                )
            )
            current_count = count_result.scalar() or 0
            if current_count >= event.max_attendees:
                raise ConflictException("Capacité maximale atteinte")

        registration = EventRegistration(
            id=str(uuid4()),
            event_id=event_id,
            email=email,
            status=RegistrationStatus.REGISTERED,
            **kwargs,
        )
        self.db.add(registration)
        await self.db.flush()
        return registration

    async def update_registration(
        self, registration_id: str, **kwargs
    ) -> EventRegistration:
        """Met à jour une inscription."""
        result = await self.db.execute(
            select(EventRegistration).where(EventRegistration.id == registration_id)
        )
        registration = result.scalar_one_or_none()
        if not registration:
            raise NotFoundException("Inscription non trouvée")

        await self.db.execute(
            update(EventRegistration)
            .where(EventRegistration.id == registration_id)
            .values(**kwargs)
        )
        await self.db.flush()

        result = await self.db.execute(
            select(EventRegistration).where(EventRegistration.id == registration_id)
        )
        return result.scalar_one()

    async def delete_registration(self, registration_id: str) -> None:
        """Supprime une inscription."""
        result = await self.db.execute(
            select(EventRegistration).where(EventRegistration.id == registration_id)
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Inscription non trouvée")

        await self.db.execute(
            delete(EventRegistration).where(EventRegistration.id == registration_id)
        )
        await self.db.flush()

    async def confirm_registration(self, registration_id: str) -> EventRegistration:
        """Confirme une inscription."""
        return await self.update_registration(
            registration_id, status=RegistrationStatus.CONFIRMED
        )

    async def cancel_registration(self, registration_id: str) -> EventRegistration:
        """Annule une inscription."""
        return await self.update_registration(
            registration_id, status=RegistrationStatus.CANCELLED
        )

    async def bulk_action_registrations(
        self, registration_ids: list[str], action: str
    ) -> int:
        """Effectue une action en masse sur les inscriptions."""
        if action == "confirm":
            new_status = RegistrationStatus.CONFIRMED
        elif action == "cancel":
            new_status = RegistrationStatus.CANCELLED
        else:
            raise ValueError(f"Action inconnue: {action}")

        result = await self.db.execute(
            update(EventRegistration)
            .where(EventRegistration.id.in_(registration_ids))
            .values(status=new_status)
        )
        await self.db.flush()
        return result.rowcount

    # =========================================================================
    # NEWS
    # =========================================================================

    async def get_news(
        self,
        search: str | None = None,
        status: PublicationStatus | None = None,
        highlight_status: str | None = None,
        tag_id: str | None = None,
        campus_id: str | None = None,
        sector_id: str | None = None,
        service_id: str | None = None,
        project_id: str | None = None,
        event_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> select:
        """Construit une requête pour lister les actualités."""
        query = select(News).options(selectinload(News.tags))

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    News.title.ilike(search_filter),
                    News.summary.ilike(search_filter),
                )
            )

        if status:
            query = query.where(News.status == status)

        if highlight_status:
            query = query.where(News.highlight_status == highlight_status)

        if tag_id:
            query = query.join(NewsTag).where(NewsTag.tag_id == tag_id)

        if campus_id:
            query = query.where(News.campus_external_id == campus_id)

        if sector_id:
            query = query.where(News.sector_external_id == sector_id)

        if service_id:
            query = query.where(News.service_external_id == service_id)

        if project_id:
            query = query.where(News.project_external_id == project_id)

        if event_id:
            query = query.where(News.event_external_id == event_id)

        if from_date:
            query = query.where(News.published_at >= from_date)

        if to_date:
            query = query.where(News.published_at <= to_date)

        query = query.order_by(News.published_at.desc().nullslast(), News.created_at.desc())
        return query

    async def enrich_news_with_names(self, news_list: list[News]) -> list[dict]:
        """Enrichit une liste d'actualités avec les noms des entités associées.

        Cette méthode effectue des requêtes batch pour éviter les problèmes N+1.

        Args:
            news_list: Liste des actualités à enrichir

        Returns:
            Liste de dictionnaires avec les actualités enrichies
        """
        if not news_list:
            return []

        # 1. Collecter tous les IDs uniques
        campus_ids = {n.campus_external_id for n in news_list if n.campus_external_id}
        sector_ids = {n.sector_external_id for n in news_list if n.sector_external_id}
        service_ids = {n.service_external_id for n in news_list if n.service_external_id}
        project_ids = {n.project_external_id for n in news_list if n.project_external_id}
        event_ids = {n.event_external_id for n in news_list if n.event_external_id}
        author_ids = {n.author_external_id for n in news_list if n.author_external_id}

        # 2. Charger les entités en batch (éviter N+1 queries)
        campus_map: dict[str, str] = {}
        sector_map: dict[str, str] = {}
        service_map: dict[str, str] = {}
        project_map: dict[str, str] = {}
        event_map: dict[str, str] = {}
        author_map: dict[str, str] = {}

        if campus_ids:
            result = await self.db.execute(
                select(Campus.id, Campus.name).where(Campus.id.in_(campus_ids))
            )
            campus_map = {str(row.id): row.name for row in result.fetchall()}

        if sector_ids:
            result = await self.db.execute(
                select(Sector.id, Sector.name).where(Sector.id.in_(sector_ids))
            )
            sector_map = {str(row.id): row.name for row in result.fetchall()}

        if service_ids:
            result = await self.db.execute(
                select(Service.id, Service.name).where(Service.id.in_(service_ids))
            )
            service_map = {str(row.id): row.name for row in result.fetchall()}

        if project_ids:
            result = await self.db.execute(
                select(Project.id, Project.title).where(Project.id.in_(project_ids))
            )
            project_map = {str(row.id): row.title for row in result.fetchall()}

        if event_ids:
            result = await self.db.execute(
                select(Event.id, Event.title).where(Event.id.in_(event_ids))
            )
            event_map = {str(row.id): row.title for row in result.fetchall()}

        if author_ids:
            result = await self.db.execute(
                select(User.id, User.first_name, User.last_name).where(User.id.in_(author_ids))
            )
            author_map = {
                str(row.id): f"{row.first_name} {row.last_name}".strip()
                for row in result.fetchall()
            }

        # 3. Mapper les noms sur les actualités
        enriched_list = []
        for news in news_list:
            # Convertir les tags en dictionnaires
            tags_data = [
                {
                    "id": tag.id,
                    "name": tag.name,
                    "slug": tag.slug,
                    "icon": tag.icon,
                    "description": tag.description,
                    "created_at": tag.created_at,
                }
                for tag in news.tags
            ]

            enriched = {
                "id": news.id,
                "title": news.title,
                "slug": news.slug,
                "summary": news.summary,
                "content": news.content,
                "video_url": news.video_url,
                "highlight_status": news.highlight_status,
                "cover_image_external_id": news.cover_image_external_id,
                "campus_external_id": news.campus_external_id,
                "sector_external_id": news.sector_external_id,
                "service_external_id": news.service_external_id,
                "event_external_id": news.event_external_id,
                "project_external_id": news.project_external_id,
                "author_external_id": news.author_external_id,
                "status": news.status,
                "published_at": news.published_at,
                "visible_from": news.visible_from,
                "created_at": news.created_at,
                "updated_at": news.updated_at,
                "tags": tags_data,
                # Noms résolus (conversion en str pour correspondre aux clés du map)
                "campus_name": campus_map.get(str(news.campus_external_id)) if news.campus_external_id else None,
                "sector_name": sector_map.get(str(news.sector_external_id)) if news.sector_external_id else None,
                "service_name": service_map.get(str(news.service_external_id)) if news.service_external_id else None,
                "project_name": project_map.get(str(news.project_external_id)) if news.project_external_id else None,
                "event_name": event_map.get(str(news.event_external_id)) if news.event_external_id else None,
                "author_name": author_map.get(str(news.author_external_id)) if news.author_external_id else None,
            }
            enriched_list.append(enriched)

        return enriched_list

    async def get_news_by_id(self, news_id: str) -> News | None:
        """Récupère une actualité par son ID."""
        result = await self.db.execute(
            select(News).options(selectinload(News.tags)).where(News.id == news_id)
        )
        return result.scalar_one_or_none()

    async def get_news_by_slug(self, slug: str) -> News | None:
        """Récupère une actualité par son slug."""
        result = await self.db.execute(
            select(News).options(selectinload(News.tags)).where(News.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_news(
        self, title: str, slug: str, tag_ids: list[str] | None = None, **kwargs
    ) -> News:
        """Crée une nouvelle actualité."""
        existing = await self.get_news_by_slug(slug)
        if existing:
            raise ConflictException(f"Une actualité avec le slug '{slug}' existe déjà")

        news = News(id=str(uuid4()), title=title, slug=slug, **kwargs)
        self.db.add(news)
        await self.db.flush()

        # Ajouter les tags
        if tag_ids:
            for tag_id in tag_ids:
                news_tag = NewsTag(news_id=news.id, tag_id=tag_id)
                self.db.add(news_tag)
            await self.db.flush()

        return await self.get_news_by_id(news.id)

    async def update_news(
        self, news_id: str, tag_ids: list[str] | None = None, **kwargs
    ) -> News:
        """Met à jour une actualité."""
        news = await self.get_news_by_id(news_id)
        if not news:
            raise NotFoundException("Actualité non trouvée")

        if "slug" in kwargs and kwargs["slug"] and kwargs["slug"] != news.slug:
            existing = await self.get_news_by_slug(kwargs["slug"])
            if existing:
                raise ConflictException(
                    f"Une actualité avec le slug '{kwargs['slug']}' existe déjà"
                )

        if kwargs:
            await self.db.execute(
                update(News).where(News.id == news_id).values(**kwargs)
            )

        # Mettre à jour les tags si fournis
        if tag_ids is not None:
            await self.db.execute(delete(NewsTag).where(NewsTag.news_id == news_id))
            for tag_id in tag_ids:
                news_tag = NewsTag(news_id=news_id, tag_id=tag_id)
                self.db.add(news_tag)

        await self.db.flush()
        return await self.get_news_by_id(news_id)

    async def delete_news(self, news_id: str) -> None:
        """Supprime une actualité."""
        news = await self.get_news_by_id(news_id)
        if not news:
            raise NotFoundException("Actualité non trouvée")

        await self.db.execute(delete(News).where(News.id == news_id))
        await self.db.flush()

    async def publish_news(
        self, news_id: str, published_at: datetime | None = None
    ) -> News:
        """Publie une actualité."""
        news = await self.get_news_by_id(news_id)
        if not news:
            raise NotFoundException("Actualité non trouvée")

        await self.db.execute(
            update(News)
            .where(News.id == news_id)
            .values(
                status=PublicationStatus.PUBLISHED,
                published_at=published_at or datetime.now(),
            )
        )
        await self.db.flush()
        return await self.get_news_by_id(news_id)

    async def unpublish_news(self, news_id: str) -> News:
        """Dépublie une actualité."""
        news = await self.get_news_by_id(news_id)
        if not news:
            raise NotFoundException("Actualité non trouvée")

        await self.db.execute(
            update(News)
            .where(News.id == news_id)
            .values(status=PublicationStatus.DRAFT)
        )
        await self.db.flush()
        return await self.get_news_by_id(news_id)

    async def duplicate_news(self, news_id: str, new_slug: str) -> News:
        """Duplique une actualité."""
        news = await self.get_news_by_id(news_id)
        if not news:
            raise NotFoundException("Actualité non trouvée")

        existing = await self.get_news_by_slug(new_slug)
        if existing:
            raise ConflictException(
                f"Une actualité avec le slug '{new_slug}' existe déjà"
            )

        new_news = News(
            id=str(uuid4()),
            title=f"{news.title} (copie)",
            slug=new_slug,
            summary=news.summary,
            content=news.content,
            video_url=news.video_url,
            cover_image_external_id=news.cover_image_external_id,
            campus_external_id=news.campus_external_id,
            sector_external_id=news.sector_external_id,
            service_external_id=news.service_external_id,
            highlight_status=news.highlight_status,
            status=PublicationStatus.DRAFT,
        )
        self.db.add(new_news)
        await self.db.flush()

        # Copier les tags
        for tag in news.tags:
            news_tag = NewsTag(news_id=new_news.id, tag_id=tag.id)
            self.db.add(news_tag)

        await self.db.flush()
        return await self.get_news_by_id(new_news.id)

    # =========================================================================
    # NEWS MEDIA
    # =========================================================================

    async def add_media_to_news(
        self, news_id: str, media_external_id: str, display_order: int = 0
    ) -> None:
        """Ajoute un média à une actualité."""
        news = await self.get_news_by_id(news_id)
        if not news:
            raise NotFoundException("Actualité non trouvée")

        result = await self.db.execute(
            select(NewsMedia).where(
                NewsMedia.news_id == news_id,
                NewsMedia.media_external_id == media_external_id,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException("Ce média est déjà associé à l'actualité")

        link = NewsMedia(
            news_id=news_id,
            media_external_id=media_external_id,
            display_order=display_order,
        )
        self.db.add(link)
        await self.db.flush()

    async def remove_media_from_news(
        self, news_id: str, media_external_id: str
    ) -> None:
        """Retire un média d'une actualité."""
        result = await self.db.execute(
            select(NewsMedia).where(
                NewsMedia.news_id == news_id,
                NewsMedia.media_external_id == media_external_id,
            )
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Cette association n'existe pas")

        await self.db.execute(
            delete(NewsMedia).where(
                NewsMedia.news_id == news_id,
                NewsMedia.media_external_id == media_external_id,
            )
        )
        await self.db.flush()

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_events_statistics(self, months: int = 12) -> dict:
        """Calcule les statistiques des événements."""
        now = datetime.now()

        # Comptage par statut
        total_result = await self.db.execute(select(func.count(Event.id)))
        total = total_result.scalar() or 0

        published_result = await self.db.execute(
            select(func.count(Event.id)).where(Event.status == PublicationStatus.PUBLISHED)
        )
        published = published_result.scalar() or 0

        draft_result = await self.db.execute(
            select(func.count(Event.id)).where(Event.status == PublicationStatus.DRAFT)
        )
        draft = draft_result.scalar() or 0

        archived_result = await self.db.execute(
            select(func.count(Event.id)).where(Event.status == PublicationStatus.ARCHIVED)
        )
        archived = archived_result.scalar() or 0

        # Événements à venir vs passés
        upcoming_result = await self.db.execute(
            select(func.count(Event.id)).where(
                Event.start_date >= now,
                Event.status == PublicationStatus.PUBLISHED,
            )
        )
        upcoming = upcoming_result.scalar() or 0

        past_result = await self.db.execute(
            select(func.count(Event.id)).where(
                Event.start_date < now,
                Event.status == PublicationStatus.PUBLISHED,
            )
        )
        past = past_result.scalar() or 0

        # Comptage par type
        type_results = await self.db.execute(
            select(Event.type, func.count(Event.id))
            .where(Event.status == PublicationStatus.PUBLISHED)
            .group_by(Event.type)
        )
        by_type = {row[0]: row[1] for row in type_results.all()}

        # Timeline - événements créés par mois (derniers N mois)
        timeline = []
        start_date = add_months(now, -(months - 1))
        start_date = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        for i in range(months):
            period_start = add_months(start_date, i)
            period_end = add_months(period_start, 1)

            count_result = await self.db.execute(
                select(func.count(Event.id)).where(
                    Event.start_date >= period_start,
                    Event.start_date < period_end,
                )
            )
            count = count_result.scalar() or 0
            timeline.append({
                "period": period_start.strftime("%Y-%m"),
                "count": count,
            })

        return {
            "total": total,
            "published": published,
            "draft": draft,
            "archived": archived,
            "upcoming": upcoming,
            "past": past,
            "by_type": by_type,
            "timeline": timeline,
        }

    async def get_news_statistics(self, months: int = 6) -> dict:
        """Calcule les statistiques des actualités."""
        now = datetime.now()

        # Comptage par statut
        total_result = await self.db.execute(select(func.count(News.id)))
        total = total_result.scalar() or 0

        published_result = await self.db.execute(
            select(func.count(News.id)).where(News.status == PublicationStatus.PUBLISHED)
        )
        published = published_result.scalar() or 0

        draft_result = await self.db.execute(
            select(func.count(News.id)).where(News.status == PublicationStatus.DRAFT)
        )
        draft = draft_result.scalar() or 0

        archived_result = await self.db.execute(
            select(func.count(News.id)).where(News.status == PublicationStatus.ARCHIVED)
        )
        archived = archived_result.scalar() or 0

        # Comptage par highlight status
        headline_result = await self.db.execute(
            select(func.count(News.id)).where(
                News.status == PublicationStatus.PUBLISHED,
                News.highlight_status == NewsHighlightStatus.HEADLINE,
            )
        )
        headline = headline_result.scalar() or 0

        featured_result = await self.db.execute(
            select(func.count(News.id)).where(
                News.status == PublicationStatus.PUBLISHED,
                News.highlight_status == NewsHighlightStatus.FEATURED,
            )
        )
        featured = featured_result.scalar() or 0

        # Timeline - publications par mois (derniers N mois)
        timeline = []
        start_date = add_months(now, -(months - 1))
        start_date = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        for i in range(months):
            period_start = add_months(start_date, i)
            period_end = add_months(period_start, 1)

            count_result = await self.db.execute(
                select(func.count(News.id)).where(
                    News.published_at >= period_start,
                    News.published_at < period_end,
                    News.status == PublicationStatus.PUBLISHED,
                )
            )
            count = count_result.scalar() or 0
            timeline.append({
                "period": period_start.strftime("%Y-%m"),
                "count": count,
            })

        return {
            "total": total,
            "published": published,
            "draft": draft,
            "archived": archived,
            "headline": headline,
            "featured": featured,
            "timeline": timeline,
        }
