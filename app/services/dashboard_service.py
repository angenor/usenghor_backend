"""
Service Dashboard
=================

Service pour agréger les données du tableau de bord.
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import (
    Application,
    ApplicationCall,
    CallStatus,
    SubmittedApplicationStatus,
)
from app.models.base import PublicationStatus
from app.models.campus import Campus
from app.models.content import Event, News
from app.models.core import Country
from app.models.identity import AuditLog, User
from app.models.newsletter import (
    CampaignStatus,
    NewsletterCampaign,
    NewsletterSubscriber,
)
from app.models.organization import ProjectStatus
from app.models.partner import Partner
from app.models.academic import Program
from app.models.project import Project
from app.schemas.dashboard import (
    ApplicationCallStats,
    ApplicationStats,
    ContentStats,
    GlobalStats,
    NewsletterStats,
    PendingTaskCategory,
    PendingTaskItem,
    PendingTasksResponse,
    ProjectStats,
    RecentActivityItem,
    RecentActivityResponse,
    UserStats,
)


class DashboardService:
    """Service pour les données du tableau de bord."""

    def __init__(self, db: AsyncSession):
        """Initialise le service avec une session de base de données."""
        self.db = db

    # ========================================================================
    # Statistiques globales
    # ========================================================================

    async def get_global_stats(self) -> GlobalStats:
        """Récupère les statistiques globales."""
        stats = GlobalStats()

        # Statistiques utilisateurs
        stats.users = await self._get_user_stats()

        # Statistiques contenu
        stats.news = await self._get_news_stats()
        stats.events = await self._get_event_stats()

        # Statistiques candidatures
        stats.applications = await self._get_application_stats()
        stats.application_calls = await self._get_application_call_stats()

        # Statistiques newsletter
        stats.newsletter = await self._get_newsletter_stats()

        # Statistiques projets
        stats.projects = await self._get_project_stats()

        # Compteurs simples
        stats.total_programs = await self._count_model(Program)
        stats.total_partners = await self._count_model(Partner)
        stats.total_countries = await self._count_model(Country, active=True)
        stats.total_campuses = await self._count_model(Campus)

        return stats

    async def _count_model(self, model, active: bool | None = None) -> int:
        """Compte les enregistrements d'un modèle."""
        query = select(func.count()).select_from(model)
        if active is not None and hasattr(model, "active"):
            query = query.where(model.active == active)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _get_user_stats(self) -> UserStats:
        """Récupère les statistiques utilisateurs."""
        # Total
        total_result = await self.db.execute(
            select(func.count()).select_from(User)
        )
        total = total_result.scalar() or 0

        # Actifs
        active_result = await self.db.execute(
            select(func.count()).select_from(User).where(User.active == True)
        )
        active = active_result.scalar() or 0

        # Vérifiés
        verified_result = await self.db.execute(
            select(func.count())
            .select_from(User)
            .where(User.email_verified == True)
        )
        verified = verified_result.scalar() or 0

        return UserStats(
            total=total,
            active=active,
            inactive=total - active,
            verified=verified,
        )

    async def _get_news_stats(self) -> ContentStats:
        """Récupère les statistiques des actualités."""
        # Total
        total_result = await self.db.execute(
            select(func.count()).select_from(News)
        )
        total = total_result.scalar() or 0

        # Par statut
        published_result = await self.db.execute(
            select(func.count())
            .select_from(News)
            .where(News.status == PublicationStatus.PUBLISHED)
        )
        published = published_result.scalar() or 0

        draft_result = await self.db.execute(
            select(func.count())
            .select_from(News)
            .where(News.status == PublicationStatus.DRAFT)
        )
        draft = draft_result.scalar() or 0

        archived_result = await self.db.execute(
            select(func.count())
            .select_from(News)
            .where(News.status == PublicationStatus.ARCHIVED)
        )
        archived = archived_result.scalar() or 0

        return ContentStats(
            total=total,
            published=published,
            draft=draft,
            archived=archived,
        )

    async def _get_event_stats(self) -> ContentStats:
        """Récupère les statistiques des événements."""
        # Total
        total_result = await self.db.execute(
            select(func.count()).select_from(Event)
        )
        total = total_result.scalar() or 0

        # Par statut
        published_result = await self.db.execute(
            select(func.count())
            .select_from(Event)
            .where(Event.status == PublicationStatus.PUBLISHED)
        )
        published = published_result.scalar() or 0

        draft_result = await self.db.execute(
            select(func.count())
            .select_from(Event)
            .where(Event.status == PublicationStatus.DRAFT)
        )
        draft = draft_result.scalar() or 0

        archived_result = await self.db.execute(
            select(func.count())
            .select_from(Event)
            .where(Event.status == PublicationStatus.ARCHIVED)
        )
        archived = archived_result.scalar() or 0

        return ContentStats(
            total=total,
            published=published,
            draft=draft,
            archived=archived,
        )

    async def _get_application_stats(self) -> ApplicationStats:
        """Récupère les statistiques des candidatures."""
        # Total
        total_result = await self.db.execute(
            select(func.count()).select_from(Application)
        )
        total = total_result.scalar() or 0

        # Par statut
        stats = {}
        for status in SubmittedApplicationStatus:
            result = await self.db.execute(
                select(func.count())
                .select_from(Application)
                .where(Application.status == status)
            )
            stats[status.value] = result.scalar() or 0

        return ApplicationStats(
            total=total,
            submitted=stats.get("submitted", 0),
            under_review=stats.get("under_review", 0),
            accepted=stats.get("accepted", 0),
            rejected=stats.get("rejected", 0),
            waitlisted=stats.get("waitlisted", 0),
            incomplete=stats.get("incomplete", 0),
        )

    async def _get_application_call_stats(self) -> ApplicationCallStats:
        """Récupère les statistiques des appels à candidature."""
        # Total
        total_result = await self.db.execute(
            select(func.count()).select_from(ApplicationCall)
        )
        total = total_result.scalar() or 0

        # Par statut
        ongoing_result = await self.db.execute(
            select(func.count())
            .select_from(ApplicationCall)
            .where(ApplicationCall.status == CallStatus.ONGOING)
        )
        ongoing = ongoing_result.scalar() or 0

        upcoming_result = await self.db.execute(
            select(func.count())
            .select_from(ApplicationCall)
            .where(ApplicationCall.status == CallStatus.UPCOMING)
        )
        upcoming = upcoming_result.scalar() or 0

        closed_result = await self.db.execute(
            select(func.count())
            .select_from(ApplicationCall)
            .where(ApplicationCall.status == CallStatus.CLOSED)
        )
        closed = closed_result.scalar() or 0

        return ApplicationCallStats(
            total=total,
            ongoing=ongoing,
            upcoming=upcoming,
            closed=closed,
        )

    async def _get_newsletter_stats(self) -> NewsletterStats:
        """Récupère les statistiques newsletter."""
        # Abonnés
        total_subscribers_result = await self.db.execute(
            select(func.count()).select_from(NewsletterSubscriber)
        )
        total_subscribers = total_subscribers_result.scalar() or 0

        active_subscribers_result = await self.db.execute(
            select(func.count())
            .select_from(NewsletterSubscriber)
            .where(NewsletterSubscriber.active == True)
        )
        active_subscribers = active_subscribers_result.scalar() or 0

        # Campagnes
        total_campaigns_result = await self.db.execute(
            select(func.count()).select_from(NewsletterCampaign)
        )
        total_campaigns = total_campaigns_result.scalar() or 0

        sent_campaigns_result = await self.db.execute(
            select(func.count())
            .select_from(NewsletterCampaign)
            .where(NewsletterCampaign.status == CampaignStatus.SENT)
        )
        sent_campaigns = sent_campaigns_result.scalar() or 0

        return NewsletterStats(
            total_subscribers=total_subscribers,
            active_subscribers=active_subscribers,
            total_campaigns=total_campaigns,
            sent_campaigns=sent_campaigns,
        )

    async def _get_project_stats(self) -> ProjectStats:
        """Récupère les statistiques des projets institutionnels."""
        # Total
        total_result = await self.db.execute(
            select(func.count()).select_from(Project)
        )
        total = total_result.scalar() or 0

        # Publiés
        published_result = await self.db.execute(
            select(func.count())
            .select_from(Project)
            .where(Project.publication_status == PublicationStatus.PUBLISHED)
        )
        published = published_result.scalar() or 0

        # Par statut de projet
        ongoing_result = await self.db.execute(
            select(func.count())
            .select_from(Project)
            .where(Project.status == ProjectStatus.ONGOING)
        )
        ongoing = ongoing_result.scalar() or 0

        completed_result = await self.db.execute(
            select(func.count())
            .select_from(Project)
            .where(Project.status == ProjectStatus.COMPLETED)
        )
        completed = completed_result.scalar() or 0

        planned_result = await self.db.execute(
            select(func.count())
            .select_from(Project)
            .where(Project.status == ProjectStatus.PLANNED)
        )
        planned = planned_result.scalar() or 0

        return ProjectStats(
            total=total,
            published=published,
            ongoing=ongoing,
            completed=completed,
            planned=planned,
        )

    # ========================================================================
    # Activité récente
    # ========================================================================

    async def get_recent_activity(
        self,
        limit: int = 20,
        action: str | None = None,
        table_name: str | None = None,
    ) -> RecentActivityResponse:
        """
        Récupère l'activité récente depuis les logs d'audit.

        Args:
            limit: Nombre maximum d'éléments
            action: Filtrer par type d'action
            table_name: Filtrer par table
        """
        query = select(AuditLog).order_by(AuditLog.created_at.desc())

        if action:
            query = query.where(AuditLog.action == action)
        if table_name:
            query = query.where(AuditLog.table_name == table_name)

        query = query.limit(limit)

        result = await self.db.execute(query)
        logs = result.scalars().all()

        # Récupérer les noms d'utilisateurs
        user_ids = [log.user_id for log in logs if log.user_id]
        users_map = {}
        if user_ids:
            users_result = await self.db.execute(
                select(User).where(User.id.in_(user_ids))
            )
            for user in users_result.scalars().all():
                users_map[user.id] = user.full_name

        # Construire les éléments d'activité
        items = []
        for log in logs:
            user_name = users_map.get(log.user_id) if log.user_id else None
            description = self._build_activity_description(log)
            items.append(
                RecentActivityItem.from_audit_log(log, user_name, description)
            )

        # Compter le total
        count_query = select(func.count()).select_from(AuditLog)
        if action:
            count_query = count_query.where(AuditLog.action == action)
        if table_name:
            count_query = count_query.where(AuditLog.table_name == table_name)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return RecentActivityResponse(items=items, total=total)

    def _build_activity_description(self, log: AuditLog) -> str:
        """Construit une description lisible pour une action."""
        action_labels = {
            "create": "a créé",
            "update": "a modifié",
            "delete": "a supprimé",
            "login": "s'est connecté",
            "logout": "s'est déconnecté",
            "password_reset": "a réinitialisé son mot de passe",
        }

        table_labels = {
            "users": "un utilisateur",
            "news": "une actualité",
            "events": "un événement",
            "applications": "une candidature",
            "application_calls": "un appel à candidature",
            "programs": "un programme",
            "partners": "un partenaire",
            "projects": "un projet",
            "media": "un média",
            "newsletter_campaigns": "une campagne",
        }

        action_label = action_labels.get(log.action, log.action)
        table_label = table_labels.get(log.table_name, log.table_name)

        if log.table_name:
            return f"{action_label} {table_label}"
        return action_label

    # ========================================================================
    # Tâches en attente
    # ========================================================================

    async def get_pending_tasks(self) -> PendingTasksResponse:
        """Récupère les tâches en attente."""
        categories = []
        total = 0

        # 1. Actualités en brouillon
        news_tasks = await self._get_pending_news()
        if news_tasks.count > 0:
            categories.append(news_tasks)
            total += news_tasks.count

        # 2. Événements en brouillon
        event_tasks = await self._get_pending_events()
        if event_tasks.count > 0:
            categories.append(event_tasks)
            total += event_tasks.count

        # 3. Candidatures à examiner
        application_tasks = await self._get_pending_applications()
        if application_tasks.count > 0:
            categories.append(application_tasks)
            total += application_tasks.count

        # 4. Appels expirant bientôt
        expiring_calls = await self._get_expiring_calls()
        if expiring_calls.count > 0:
            categories.append(expiring_calls)
            total += expiring_calls.count

        # 5. Événements à venir
        upcoming_events = await self._get_upcoming_events()
        if upcoming_events.count > 0:
            categories.append(upcoming_events)
            total += upcoming_events.count

        return PendingTasksResponse(total=total, categories=categories)

    async def _get_pending_news(self) -> PendingTaskCategory:
        """Récupère les actualités en brouillon."""
        query = (
            select(News)
            .where(News.status == PublicationStatus.DRAFT)
            .order_by(News.created_at.desc())
            .limit(10)
        )
        result = await self.db.execute(query)
        news_list = result.scalars().all()

        # Count total
        count_result = await self.db.execute(
            select(func.count())
            .select_from(News)
            .where(News.status == PublicationStatus.DRAFT)
        )
        count = count_result.scalar() or 0

        items = [
            PendingTaskItem(
                id=news.id,
                type="news_draft",
                title=news.title,
                description="Actualité en attente de publication",
                priority="normal",
                created_at=news.created_at,
                link=f"/admin/news/{news.id}",
            )
            for news in news_list
        ]

        return PendingTaskCategory(
            category="news_draft",
            label="Actualités à publier",
            count=count,
            items=items,
        )

    async def _get_pending_events(self) -> PendingTaskCategory:
        """Récupère les événements en brouillon."""
        query = (
            select(Event)
            .where(Event.status == PublicationStatus.DRAFT)
            .order_by(Event.start_date.asc())
            .limit(10)
        )
        result = await self.db.execute(query)
        events = result.scalars().all()

        # Count total
        count_result = await self.db.execute(
            select(func.count())
            .select_from(Event)
            .where(Event.status == PublicationStatus.DRAFT)
        )
        count = count_result.scalar() or 0

        items = [
            PendingTaskItem(
                id=event.id,
                type="event_draft",
                title=event.title,
                description="Événement en attente de publication",
                priority="normal" if event.start_date > datetime.now() else "high",
                due_date=event.start_date,
                created_at=event.created_at,
                link=f"/admin/events/{event.id}",
            )
            for event in events
        ]

        return PendingTaskCategory(
            category="event_draft",
            label="Événements à publier",
            count=count,
            items=items,
        )

    async def _get_pending_applications(self) -> PendingTaskCategory:
        """Récupère les candidatures à examiner."""
        query = (
            select(Application)
            .where(
                Application.status.in_([
                    SubmittedApplicationStatus.SUBMITTED,
                    SubmittedApplicationStatus.UNDER_REVIEW,
                ])
            )
            .order_by(Application.submitted_at.asc())
            .limit(10)
        )
        result = await self.db.execute(query)
        applications = result.scalars().all()

        # Count total
        count_result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .where(
                Application.status.in_([
                    SubmittedApplicationStatus.SUBMITTED,
                    SubmittedApplicationStatus.UNDER_REVIEW,
                ])
            )
        )
        count = count_result.scalar() or 0

        items = [
            PendingTaskItem(
                id=app.id,
                type="application_review",
                title=f"{app.first_name} {app.last_name} ({app.reference_number})",
                description=f"Candidature {app.status.value}",
                priority="high" if app.status == SubmittedApplicationStatus.UNDER_REVIEW else "normal",
                created_at=app.submitted_at,
                link=f"/admin/applications/{app.id}",
            )
            for app in applications
        ]

        return PendingTaskCategory(
            category="application_review",
            label="Candidatures à examiner",
            count=count,
            items=items,
        )

    async def _get_expiring_calls(self) -> PendingTaskCategory:
        """Récupère les appels expirant dans les 7 prochains jours."""
        now = datetime.now()
        week_later = now + timedelta(days=7)

        query = (
            select(ApplicationCall)
            .where(
                ApplicationCall.status == CallStatus.ONGOING,
                ApplicationCall.deadline.isnot(None),
                ApplicationCall.deadline <= week_later,
                ApplicationCall.deadline >= now,
            )
            .order_by(ApplicationCall.deadline.asc())
            .limit(10)
        )
        result = await self.db.execute(query)
        calls = result.scalars().all()

        # Count total
        count_result = await self.db.execute(
            select(func.count())
            .select_from(ApplicationCall)
            .where(
                ApplicationCall.status == CallStatus.ONGOING,
                ApplicationCall.deadline.isnot(None),
                ApplicationCall.deadline <= week_later,
                ApplicationCall.deadline >= now,
            )
        )
        count = count_result.scalar() or 0

        items = [
            PendingTaskItem(
                id=call.id,
                type="call_expiring",
                title=call.title,
                description="Date limite proche",
                priority="urgent",
                due_date=call.deadline,
                created_at=call.created_at,
                link=f"/admin/application-calls/{call.id}",
            )
            for call in calls
        ]

        return PendingTaskCategory(
            category="call_expiring",
            label="Appels expirant bientôt",
            count=count,
            items=items,
        )

    async def _get_upcoming_events(self) -> PendingTaskCategory:
        """Récupère les événements à venir dans les 7 prochains jours."""
        now = datetime.now()
        week_later = now + timedelta(days=7)

        query = (
            select(Event)
            .where(
                Event.status == PublicationStatus.PUBLISHED,
                Event.start_date >= now,
                Event.start_date <= week_later,
            )
            .order_by(Event.start_date.asc())
            .limit(10)
        )
        result = await self.db.execute(query)
        events = result.scalars().all()

        # Count total
        count_result = await self.db.execute(
            select(func.count())
            .select_from(Event)
            .where(
                Event.status == PublicationStatus.PUBLISHED,
                Event.start_date >= now,
                Event.start_date <= week_later,
            )
        )
        count = count_result.scalar() or 0

        items = [
            PendingTaskItem(
                id=event.id,
                type="event_upcoming",
                title=event.title,
                description="Événement imminent",
                priority="high",
                due_date=event.start_date,
                created_at=event.created_at,
                link=f"/admin/events/{event.id}",
            )
            for event in events
        ]

        return PendingTaskCategory(
            category="event_upcoming",
            label="Événements cette semaine",
            count=count,
            items=items,
        )
