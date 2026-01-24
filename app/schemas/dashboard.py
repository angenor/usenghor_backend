"""
Schémas Dashboard
=================

Schémas Pydantic pour les données du tableau de bord.
"""

from datetime import datetime
from pydantic import BaseModel


# ============================================================================
# Statistiques globales
# ============================================================================


class UserStats(BaseModel):
    """Statistiques utilisateurs."""

    total: int = 0
    active: int = 0
    inactive: int = 0
    verified: int = 0


class ContentStats(BaseModel):
    """Statistiques contenu (news/events)."""

    total: int = 0
    published: int = 0
    draft: int = 0
    archived: int = 0


class ApplicationStats(BaseModel):
    """Statistiques candidatures."""

    total: int = 0
    submitted: int = 0
    under_review: int = 0
    accepted: int = 0
    rejected: int = 0
    waitlisted: int = 0
    incomplete: int = 0


class ApplicationCallStats(BaseModel):
    """Statistiques appels à candidature."""

    total: int = 0
    ongoing: int = 0
    upcoming: int = 0
    closed: int = 0


class NewsletterStats(BaseModel):
    """Statistiques newsletter."""

    total_subscribers: int = 0
    active_subscribers: int = 0
    total_campaigns: int = 0
    sent_campaigns: int = 0


class ProjectStats(BaseModel):
    """Statistiques projets institutionnels."""

    total: int = 0
    published: int = 0
    ongoing: int = 0
    completed: int = 0
    planned: int = 0


class GlobalStats(BaseModel):
    """Statistiques globales du dashboard."""

    users: UserStats = UserStats()
    news: ContentStats = ContentStats()
    events: ContentStats = ContentStats()
    applications: ApplicationStats = ApplicationStats()
    application_calls: ApplicationCallStats = ApplicationCallStats()
    newsletter: NewsletterStats = NewsletterStats()
    projects: ProjectStats = ProjectStats()
    total_programs: int = 0
    total_partners: int = 0
    total_countries: int = 0
    total_campuses: int = 0


# ============================================================================
# Activité récente
# ============================================================================


class RecentActivityItem(BaseModel):
    """Élément d'activité récente."""

    model_config = {"from_attributes": True}

    id: str
    user_id: str | None = None
    user_name: str | None = None
    action: str
    table_name: str | None = None
    record_id: str | None = None
    description: str | None = None
    created_at: datetime

    @classmethod
    def from_audit_log(
        cls, log, user_name: str | None = None, description: str | None = None
    ) -> "RecentActivityItem":
        """Crée un élément d'activité à partir d'un log d'audit."""
        return cls(
            id=log.id,
            user_id=log.user_id,
            user_name=user_name,
            action=log.action,
            table_name=log.table_name,
            record_id=log.record_id,
            description=description,
            created_at=log.created_at,
        )


class RecentActivityResponse(BaseModel):
    """Réponse activité récente."""

    items: list[RecentActivityItem] = []
    total: int = 0


# ============================================================================
# Tâches en attente
# ============================================================================


class PendingTaskItem(BaseModel):
    """Élément de tâche en attente."""

    id: str
    type: str  # news_draft, event_draft, application_review, etc.
    title: str
    description: str | None = None
    priority: str = "normal"  # low, normal, high, urgent
    due_date: datetime | None = None
    created_at: datetime | None = None
    link: str | None = None


class PendingTaskCategory(BaseModel):
    """Catégorie de tâches en attente."""

    category: str
    label: str
    count: int = 0
    items: list[PendingTaskItem] = []


class PendingTasksResponse(BaseModel):
    """Réponse tâches en attente."""

    total: int = 0
    categories: list[PendingTaskCategory] = []


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "UserStats",
    "ContentStats",
    "ApplicationStats",
    "ApplicationCallStats",
    "NewsletterStats",
    "ProjectStats",
    "GlobalStats",
    "RecentActivityItem",
    "RecentActivityResponse",
    "PendingTaskItem",
    "PendingTaskCategory",
    "PendingTasksResponse",
]
