"""
Tests unitaires - DashboardService
==================================

Tests du service de tableau de bord.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import User, AuditLog
from app.models.content import News, Event, EventType
from app.models.base import PublicationStatus
from app.services.dashboard_service import DashboardService


class TestDashboardServiceStats:
    """Tests pour les statistiques globales."""

    @pytest.mark.asyncio
    async def test_get_global_stats_empty(self, db_session: AsyncSession):
        """Test des statistiques avec base vide."""
        service = DashboardService(db_session)

        stats = await service.get_global_stats()

        assert stats is not None
        assert stats.users.total == 0
        assert stats.news.total == 0
        assert stats.events.total == 0

    @pytest.mark.asyncio
    async def test_get_global_stats_with_users(
        self, db_session: AsyncSession, sample_users: list[User]
    ):
        """Test des statistiques avec des utilisateurs."""
        service = DashboardService(db_session)

        stats = await service.get_global_stats()

        # 5 utilisateurs créés, 3 actifs
        assert stats.users.total == 5
        assert stats.users.active == 3
        assert stats.users.inactive == 2


class TestDashboardServiceRecentActivity:
    """Tests pour l'activité récente."""

    @pytest_asyncio.fixture
    async def audit_logs(self, db_session: AsyncSession, test_user: User) -> list[AuditLog]:
        """Crée des logs d'audit de test."""
        logs = []
        actions = ["create", "update", "delete", "login"]
        tables = ["users", "news", "events", None]

        for i in range(10):
            log = AuditLog(
                id=str(uuid4()),
                user_id=test_user.id,
                action=actions[i % len(actions)],
                table_name=tables[i % len(tables)],
                record_id=str(uuid4()) if tables[i % len(tables)] else None,
                ip_address="127.0.0.1",
                created_at=datetime.now(timezone.utc) - timedelta(hours=i),
            )
            db_session.add(log)
            logs.append(log)

        await db_session.commit()
        return logs

    @pytest.mark.asyncio
    async def test_get_recent_activity(
        self, db_session: AsyncSession, audit_logs: list[AuditLog]
    ):
        """Test de récupération de l'activité récente."""
        service = DashboardService(db_session)

        response = await service.get_recent_activity(limit=5)

        assert response is not None
        assert len(response.items) == 5
        assert response.total == 10

    @pytest.mark.asyncio
    async def test_get_recent_activity_filter_action(
        self, db_session: AsyncSession, audit_logs: list[AuditLog]
    ):
        """Test de filtrage par action."""
        service = DashboardService(db_session)

        response = await service.get_recent_activity(action="create")

        # 10 logs avec rotation sur 4 actions = ~2-3 "create"
        assert all(item.action == "create" for item in response.items)

    @pytest.mark.asyncio
    async def test_get_recent_activity_filter_table(
        self, db_session: AsyncSession, audit_logs: list[AuditLog]
    ):
        """Test de filtrage par table."""
        service = DashboardService(db_session)

        response = await service.get_recent_activity(table_name="users")

        assert all(item.table_name == "users" for item in response.items)


class TestDashboardServicePendingTasks:
    """Tests pour les tâches en attente."""

    @pytest_asyncio.fixture
    async def draft_news(self, db_session: AsyncSession) -> list[News]:
        """Crée des actualités en brouillon."""
        news_items = []
        for i in range(3):
            news = News(
                id=str(uuid4()),
                title=f"Actualité brouillon {i}",
                slug=f"actualite-brouillon-{i}",
                status=PublicationStatus.DRAFT,
                created_at=datetime.now(timezone.utc),
            )
            db_session.add(news)
            news_items.append(news)

        await db_session.commit()
        return news_items

    @pytest_asyncio.fixture
    async def upcoming_events(self, db_session: AsyncSession) -> list[Event]:
        """Crée des événements à venir."""
        events = []
        for i in range(2):
            event = Event(
                id=str(uuid4()),
                title=f"Événement à venir {i}",
                slug=f"evenement-a-venir-{i}",
                type=EventType.CONFERENCE,
                status=PublicationStatus.PUBLISHED,
                start_date=datetime.now(timezone.utc) + timedelta(days=i + 1),
                end_date=datetime.now(timezone.utc) + timedelta(days=i + 2),
                created_at=datetime.now(timezone.utc),
            )
            db_session.add(event)
            events.append(event)

        await db_session.commit()
        return events

    @pytest.mark.asyncio
    async def test_get_pending_tasks_empty(self, db_session: AsyncSession):
        """Test des tâches en attente avec base vide."""
        service = DashboardService(db_session)

        response = await service.get_pending_tasks()

        assert response is not None
        assert response.total == 0
        assert len(response.categories) == 0

    @pytest.mark.asyncio
    async def test_get_pending_tasks_with_drafts(
        self, db_session: AsyncSession, draft_news: list[News]
    ):
        """Test des tâches avec actualités en brouillon."""
        service = DashboardService(db_session)

        response = await service.get_pending_tasks()

        # Vérifier que les brouillons apparaissent dans les catégories
        news_category = next(
            (c for c in response.categories if c.category == "news_draft"), None
        )
        assert news_category is not None
        assert news_category.count == 3

    @pytest.mark.asyncio
    async def test_get_pending_tasks_with_upcoming_events(
        self, db_session: AsyncSession, upcoming_events: list[Event]
    ):
        """Test des tâches avec événements à venir."""
        service = DashboardService(db_session)

        response = await service.get_pending_tasks()

        # Vérifier les événements à venir
        event_category = next(
            (c for c in response.categories if c.category == "event_upcoming"), None
        )
        assert event_category is not None
        assert event_category.count >= 1
