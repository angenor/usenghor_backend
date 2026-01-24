"""
Service Newsletter
==================

Logique métier pour la gestion de la newsletter.
"""

import secrets
from datetime import datetime
from uuid import uuid4

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.newsletter import (
    CampaignStatus,
    NewsletterCampaign,
    NewsletterSend,
    NewsletterSubscriber,
    SendStatus,
)


class NewsletterService:
    """Service pour la gestion de la newsletter."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # SUBSCRIBERS
    # =========================================================================

    async def get_subscribers(
        self,
        search: str | None = None,
        active: bool | None = None,
        source: str | None = None,
    ) -> select:
        """Construit une requête pour lister les abonnés."""
        query = select(NewsletterSubscriber)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    NewsletterSubscriber.email.ilike(search_filter),
                    NewsletterSubscriber.first_name.ilike(search_filter),
                    NewsletterSubscriber.last_name.ilike(search_filter),
                )
            )

        if active is not None:
            query = query.where(NewsletterSubscriber.active == active)

        if source:
            query = query.where(NewsletterSubscriber.source == source)

        query = query.order_by(NewsletterSubscriber.subscribed_at.desc())
        return query

    async def get_subscriber_by_id(self, subscriber_id: str) -> NewsletterSubscriber | None:
        """Récupère un abonné par son ID."""
        result = await self.db.execute(
            select(NewsletterSubscriber).where(NewsletterSubscriber.id == subscriber_id)
        )
        return result.scalar_one_or_none()

    async def get_subscriber_by_email(self, email: str) -> NewsletterSubscriber | None:
        """Récupère un abonné par son email."""
        result = await self.db.execute(
            select(NewsletterSubscriber).where(
                NewsletterSubscriber.email.ilike(email)
            )
        )
        return result.scalar_one_or_none()

    async def get_subscriber_by_token(self, token: str) -> NewsletterSubscriber | None:
        """Récupère un abonné par son token de désinscription."""
        result = await self.db.execute(
            select(NewsletterSubscriber).where(
                NewsletterSubscriber.unsubscribe_token == token
            )
        )
        return result.scalar_one_or_none()

    async def subscribe(self, email: str, **kwargs) -> NewsletterSubscriber:
        """Crée un nouvel abonnement ou réactive un abonnement existant."""
        existing = await self.get_subscriber_by_email(email)

        if existing:
            if existing.active:
                raise ConflictException("Cette adresse email est déjà abonnée")

            # Réactiver l'abonnement
            await self.db.execute(
                update(NewsletterSubscriber)
                .where(NewsletterSubscriber.id == existing.id)
                .values(
                    active=True,
                    unsubscribed_at=None,
                    subscribed_at=datetime.now(),
                    unsubscribe_token=self._generate_token(),
                    **kwargs,
                )
            )
            await self.db.flush()
            return await self.get_subscriber_by_id(existing.id)

        subscriber = NewsletterSubscriber(
            id=str(uuid4()),
            email=email.lower(),
            unsubscribe_token=self._generate_token(),
            **kwargs,
        )
        self.db.add(subscriber)
        await self.db.flush()
        return subscriber

    async def update_subscriber(self, subscriber_id: str, **kwargs) -> NewsletterSubscriber:
        """Met à jour un abonné."""
        subscriber = await self.get_subscriber_by_id(subscriber_id)
        if not subscriber:
            raise NotFoundException("Abonné non trouvé")

        await self.db.execute(
            update(NewsletterSubscriber)
            .where(NewsletterSubscriber.id == subscriber_id)
            .values(**kwargs)
        )
        await self.db.flush()
        return await self.get_subscriber_by_id(subscriber_id)

    async def unsubscribe(self, subscriber_id: str) -> NewsletterSubscriber:
        """Désabonne un abonné."""
        subscriber = await self.get_subscriber_by_id(subscriber_id)
        if not subscriber:
            raise NotFoundException("Abonné non trouvé")

        await self.db.execute(
            update(NewsletterSubscriber)
            .where(NewsletterSubscriber.id == subscriber_id)
            .values(active=False, unsubscribed_at=datetime.now())
        )
        await self.db.flush()
        return await self.get_subscriber_by_id(subscriber_id)

    async def unsubscribe_by_token(self, token: str) -> NewsletterSubscriber:
        """Désabonne un abonné via son token."""
        subscriber = await self.get_subscriber_by_token(token)
        if not subscriber:
            raise NotFoundException("Token de désinscription invalide")

        return await self.unsubscribe(subscriber.id)

    async def delete_subscriber(self, subscriber_id: str) -> None:
        """Supprime définitivement un abonné."""
        subscriber = await self.get_subscriber_by_id(subscriber_id)
        if not subscriber:
            raise NotFoundException("Abonné non trouvé")

        await self.db.execute(
            delete(NewsletterSubscriber).where(NewsletterSubscriber.id == subscriber_id)
        )
        await self.db.flush()

    async def import_subscribers(
        self,
        subscribers: list[dict],
        source: str | None = None,
    ) -> dict:
        """Importe des abonnés en masse."""
        imported = 0
        duplicates = 0
        errors = 0

        for data in subscribers:
            try:
                email = data.get("email", "").lower()
                if not email:
                    errors += 1
                    continue

                existing = await self.get_subscriber_by_email(email)
                if existing:
                    duplicates += 1
                    continue

                subscriber = NewsletterSubscriber(
                    id=str(uuid4()),
                    email=email,
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    source=source,
                    unsubscribe_token=self._generate_token(),
                )
                self.db.add(subscriber)
                imported += 1
            except Exception:
                errors += 1

        await self.db.flush()
        return {
            "total": len(subscribers),
            "imported": imported,
            "duplicates": duplicates,
            "errors": errors,
        }

    async def get_active_subscribers(self) -> list[NewsletterSubscriber]:
        """Récupère tous les abonnés actifs."""
        result = await self.db.execute(
            select(NewsletterSubscriber)
            .where(NewsletterSubscriber.active == True)  # noqa: E712
            .order_by(NewsletterSubscriber.email)
        )
        return list(result.scalars().all())

    # =========================================================================
    # CAMPAIGNS
    # =========================================================================

    async def get_campaigns(
        self,
        search: str | None = None,
        status: CampaignStatus | None = None,
    ) -> select:
        """Construit une requête pour lister les campagnes."""
        query = select(NewsletterCampaign)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    NewsletterCampaign.title.ilike(search_filter),
                    NewsletterCampaign.subject.ilike(search_filter),
                )
            )

        if status:
            query = query.where(NewsletterCampaign.status == status)

        query = query.order_by(NewsletterCampaign.created_at.desc())
        return query

    async def get_campaign_by_id(self, campaign_id: str) -> NewsletterCampaign | None:
        """Récupère une campagne par son ID."""
        result = await self.db.execute(
            select(NewsletterCampaign)
            .options(selectinload(NewsletterCampaign.sends))
            .where(NewsletterCampaign.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def create_campaign(self, title: str, subject: str, **kwargs) -> NewsletterCampaign:
        """Crée une nouvelle campagne."""
        campaign = NewsletterCampaign(
            id=str(uuid4()),
            title=title,
            subject=subject,
            **kwargs,
        )
        self.db.add(campaign)
        await self.db.flush()
        return campaign

    async def update_campaign(self, campaign_id: str, **kwargs) -> NewsletterCampaign:
        """Met à jour une campagne."""
        campaign = await self.get_campaign_by_id(campaign_id)
        if not campaign:
            raise NotFoundException("Campagne non trouvée")

        if campaign.status == CampaignStatus.SENT:
            raise ConflictException("Impossible de modifier une campagne déjà envoyée")

        await self.db.execute(
            update(NewsletterCampaign)
            .where(NewsletterCampaign.id == campaign_id)
            .values(**kwargs)
        )
        await self.db.flush()
        return await self.get_campaign_by_id(campaign_id)

    async def delete_campaign(self, campaign_id: str) -> None:
        """Supprime une campagne."""
        campaign = await self.get_campaign_by_id(campaign_id)
        if not campaign:
            raise NotFoundException("Campagne non trouvée")

        if campaign.status == CampaignStatus.SENT:
            raise ConflictException("Impossible de supprimer une campagne déjà envoyée")

        await self.db.execute(
            delete(NewsletterCampaign).where(NewsletterCampaign.id == campaign_id)
        )
        await self.db.flush()

    async def schedule_campaign(
        self,
        campaign_id: str,
        scheduled_send_at: datetime,
    ) -> NewsletterCampaign:
        """Programme l'envoi d'une campagne."""
        campaign = await self.get_campaign_by_id(campaign_id)
        if not campaign:
            raise NotFoundException("Campagne non trouvée")

        if campaign.status == CampaignStatus.SENT:
            raise ConflictException("Cette campagne a déjà été envoyée")

        await self.db.execute(
            update(NewsletterCampaign)
            .where(NewsletterCampaign.id == campaign_id)
            .values(
                status=CampaignStatus.SCHEDULED,
                scheduled_send_at=scheduled_send_at,
            )
        )
        await self.db.flush()
        return await self.get_campaign_by_id(campaign_id)

    async def cancel_schedule(self, campaign_id: str) -> NewsletterCampaign:
        """Annule la programmation d'une campagne."""
        campaign = await self.get_campaign_by_id(campaign_id)
        if not campaign:
            raise NotFoundException("Campagne non trouvée")

        if campaign.status != CampaignStatus.SCHEDULED:
            raise ConflictException("Cette campagne n'est pas programmée")

        await self.db.execute(
            update(NewsletterCampaign)
            .where(NewsletterCampaign.id == campaign_id)
            .values(
                status=CampaignStatus.DRAFT,
                scheduled_send_at=None,
            )
        )
        await self.db.flush()
        return await self.get_campaign_by_id(campaign_id)

    async def send_campaign(self, campaign_id: str) -> NewsletterCampaign:
        """
        Envoie une campagne immédiatement.

        Note: L'envoi réel des emails doit être effectué par un service externe.
        Cette méthode crée les enregistrements d'envoi et met à jour le statut.
        """
        campaign = await self.get_campaign_by_id(campaign_id)
        if not campaign:
            raise NotFoundException("Campagne non trouvée")

        if campaign.status == CampaignStatus.SENT:
            raise ConflictException("Cette campagne a déjà été envoyée")

        # Récupérer les abonnés actifs
        subscribers = await self.get_active_subscribers()

        if not subscribers:
            raise ConflictException("Aucun abonné actif")

        # Créer les enregistrements d'envoi
        for subscriber in subscribers:
            send = NewsletterSend(
                id=str(uuid4()),
                campaign_id=campaign_id,
                subscriber_id=subscriber.id,
                email=subscriber.email,
            )
            self.db.add(send)

        # Mettre à jour la campagne
        await self.db.execute(
            update(NewsletterCampaign)
            .where(NewsletterCampaign.id == campaign_id)
            .values(
                status=CampaignStatus.SENT,
                sent_at=datetime.now(),
                recipient_count=len(subscribers),
            )
        )
        await self.db.flush()
        return await self.get_campaign_by_id(campaign_id)

    async def duplicate_campaign(self, campaign_id: str) -> NewsletterCampaign:
        """Duplique une campagne."""
        campaign = await self.get_campaign_by_id(campaign_id)
        if not campaign:
            raise NotFoundException("Campagne non trouvée")

        new_campaign = NewsletterCampaign(
            id=str(uuid4()),
            title=f"{campaign.title} (copie)",
            subject=campaign.subject,
            html_content=campaign.html_content,
            text_content=campaign.text_content,
            created_by_external_id=campaign.created_by_external_id,
        )
        self.db.add(new_campaign)
        await self.db.flush()
        return new_campaign

    async def get_campaign_statistics(self, campaign_id: str) -> dict:
        """Calcule les statistiques d'une campagne."""
        campaign = await self.get_campaign_by_id(campaign_id)
        if not campaign:
            raise NotFoundException("Campagne non trouvée")

        # Compter les différents statuts
        result = await self.db.execute(
            select(
                func.count(NewsletterSend.id).label("sent_count"),
                func.sum(
                    func.cast(NewsletterSend.status == SendStatus.OPENED, Integer)
                    + func.cast(NewsletterSend.status == SendStatus.CLICKED, Integer)
                ).label("open_count"),
                func.sum(
                    func.cast(NewsletterSend.status == SendStatus.CLICKED, Integer)
                ).label("click_count"),
                func.sum(
                    func.cast(NewsletterSend.status == SendStatus.ERROR, Integer)
                ).label("error_count"),
            ).where(NewsletterSend.campaign_id == campaign_id)
        )
        row = result.one()

        sent_count = row.sent_count or 0
        open_count = row.open_count or 0
        click_count = row.click_count or 0
        error_count = row.error_count or 0

        open_rate = (open_count / sent_count * 100) if sent_count > 0 else 0
        click_rate = (click_count / sent_count * 100) if sent_count > 0 else 0

        return {
            "campaign_id": campaign_id,
            "recipient_count": campaign.recipient_count,
            "sent_count": sent_count,
            "open_count": open_count,
            "click_count": click_count,
            "error_count": error_count,
            "open_rate": round(open_rate, 2),
            "click_rate": round(click_rate, 2),
        }

    # =========================================================================
    # SENDS
    # =========================================================================

    async def get_sends_by_campaign(self, campaign_id: str) -> list[NewsletterSend]:
        """Récupère les envois d'une campagne."""
        result = await self.db.execute(
            select(NewsletterSend)
            .options(selectinload(NewsletterSend.subscriber))
            .where(NewsletterSend.campaign_id == campaign_id)
            .order_by(NewsletterSend.sent_at.desc())
        )
        return list(result.scalars().all())

    async def get_send_by_id(self, send_id: str) -> NewsletterSend | None:
        """Récupère un envoi par son ID."""
        result = await self.db.execute(
            select(NewsletterSend)
            .options(selectinload(NewsletterSend.subscriber))
            .where(NewsletterSend.id == send_id)
        )
        return result.scalar_one_or_none()

    async def track_open(self, send_id: str) -> NewsletterSend | None:
        """Enregistre l'ouverture d'un email."""
        send = await self.get_send_by_id(send_id)
        if not send:
            return None

        if send.opened_at is None:
            await self.db.execute(
                update(NewsletterSend)
                .where(NewsletterSend.id == send_id)
                .values(
                    status=SendStatus.OPENED,
                    opened_at=datetime.now(),
                )
            )

            # Incrémenter le compteur de la campagne
            await self.db.execute(
                update(NewsletterCampaign)
                .where(NewsletterCampaign.id == send.campaign_id)
                .values(open_count=NewsletterCampaign.open_count + 1)
            )
            await self.db.flush()

        return await self.get_send_by_id(send_id)

    async def track_click(self, send_id: str) -> NewsletterSend | None:
        """Enregistre un clic dans un email."""
        send = await self.get_send_by_id(send_id)
        if not send:
            return None

        if send.clicked_at is None:
            # Enregistrer l'ouverture si pas encore fait
            if send.opened_at is None:
                await self.track_open(send_id)
                send = await self.get_send_by_id(send_id)

            await self.db.execute(
                update(NewsletterSend)
                .where(NewsletterSend.id == send_id)
                .values(
                    status=SendStatus.CLICKED,
                    clicked_at=datetime.now(),
                )
            )

            # Incrémenter le compteur de la campagne
            await self.db.execute(
                update(NewsletterCampaign)
                .where(NewsletterCampaign.id == send.campaign_id)
                .values(click_count=NewsletterCampaign.click_count + 1)
            )
            await self.db.flush()

        return await self.get_send_by_id(send_id)

    async def mark_send_error(self, send_id: str, error_message: str) -> NewsletterSend | None:
        """Marque un envoi comme erreur."""
        send = await self.get_send_by_id(send_id)
        if not send:
            return None

        await self.db.execute(
            update(NewsletterSend)
            .where(NewsletterSend.id == send_id)
            .values(
                status=SendStatus.ERROR,
                error_message=error_message,
            )
        )
        await self.db.flush()
        return await self.get_send_by_id(send_id)

    # =========================================================================
    # GLOBAL STATISTICS
    # =========================================================================

    async def get_statistics(self) -> dict:
        """Calcule les statistiques globales de la newsletter."""
        # Total abonnés
        total_result = await self.db.execute(
            select(func.count(NewsletterSubscriber.id))
        )
        total_subscribers = total_result.scalar() or 0

        # Abonnés actifs
        active_result = await self.db.execute(
            select(func.count(NewsletterSubscriber.id)).where(
                NewsletterSubscriber.active == True  # noqa: E712
            )
        )
        active_subscribers = active_result.scalar() or 0

        # Total campagnes
        campaigns_result = await self.db.execute(
            select(func.count(NewsletterCampaign.id))
        )
        total_campaigns = campaigns_result.scalar() or 0

        # Campagnes envoyées
        sent_result = await self.db.execute(
            select(func.count(NewsletterCampaign.id)).where(
                NewsletterCampaign.status == CampaignStatus.SENT
            )
        )
        sent_campaigns = sent_result.scalar() or 0

        # Total envois
        sends_result = await self.db.execute(
            select(func.count(NewsletterSend.id))
        )
        total_sends = sends_result.scalar() or 0

        # Moyennes des taux
        avg_open_rate = 0.0
        avg_click_rate = 0.0

        if sent_campaigns > 0:
            rate_result = await self.db.execute(
                select(
                    func.avg(
                        func.cast(NewsletterCampaign.open_count, Integer)
                        * 100.0
                        / func.nullif(NewsletterCampaign.recipient_count, 0)
                    ),
                    func.avg(
                        func.cast(NewsletterCampaign.click_count, Integer)
                        * 100.0
                        / func.nullif(NewsletterCampaign.recipient_count, 0)
                    ),
                ).where(NewsletterCampaign.status == CampaignStatus.SENT)
            )
            row = rate_result.one()
            avg_open_rate = round(row[0] or 0, 2)
            avg_click_rate = round(row[1] or 0, 2)

        return {
            "total_subscribers": total_subscribers,
            "active_subscribers": active_subscribers,
            "total_campaigns": total_campaigns,
            "sent_campaigns": sent_campaigns,
            "total_sends": total_sends,
            "average_open_rate": avg_open_rate,
            "average_click_rate": avg_click_rate,
        }

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _generate_token(self) -> str:
        """Génère un token de désinscription sécurisé."""
        return secrets.token_urlsafe(32)
