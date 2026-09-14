"""
Tests d'intégration — API publique des événements : filtre par service et tri
=============================================================================

Spec : specs/023-pei-public-home-activities/contracts/public-api.md
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import PublicationStatus
from app.models.content import Event, EventType

BASE = "/api/public/events"


def _event(slug: str, start: datetime, service_id: str, status=PublicationStatus.PUBLISHED) -> Event:
    return Event(
        id=str(uuid4()),
        title=f"Événement {slug}",
        slug=slug,
        type=EventType.CONFERENCE,
        start_date=start,
        service_external_id=service_id,
        status=status,
    )


async def _seed_events(db: AsyncSession) -> dict:
    service_a = str(uuid4())
    service_b = str(uuid4())
    now = datetime.now(timezone.utc)
    db.add_all(
        [
            _event("a-proche", now + timedelta(days=5), service_a),
            _event("a-passe", now - timedelta(days=10), service_a),
            _event("b-futur", now + timedelta(days=3), service_b),
            _event("a-brouillon", now + timedelta(days=8), service_a, PublicationStatus.DRAFT),
        ]
    )
    await db.commit()
    return {"a": service_a, "b": service_b}


def _slugs(response) -> list[str]:
    return [item["slug"] for item in response.json()["items"]]


@pytest.mark.asyncio
async def test_filter_by_service(client: AsyncClient, db_session: AsyncSession):
    services = await _seed_events(db_session)

    response = await client.get(BASE, params={"service_id": services["a"]})
    assert response.status_code == 200
    assert sorted(_slugs(response)) == ["a-passe", "a-proche"]
    assert response.json()["total"] == 2


@pytest.mark.asyncio
async def test_filter_by_service_upcoming(client: AsyncClient, db_session: AsyncSession):
    services = await _seed_events(db_session)

    response = await client.get(BASE, params={"service_id": services["a"], "upcoming": "true"})
    assert response.status_code == 200
    assert _slugs(response) == ["a-proche"]


@pytest.mark.asyncio
async def test_order_asc_and_default_desc(client: AsyncClient, db_session: AsyncSession):
    await _seed_events(db_session)

    asc = await client.get(BASE, params={"order": "asc"})
    assert asc.status_code == 200
    assert _slugs(asc) == ["a-passe", "b-futur", "a-proche"]

    default = await client.get(BASE)
    assert default.status_code == 200
    assert _slugs(default) == ["a-proche", "b-futur", "a-passe"]


@pytest.mark.asyncio
async def test_draft_excluded(client: AsyncClient, db_session: AsyncSession):
    services = await _seed_events(db_session)

    response = await client.get(BASE, params={"service_id": services["a"], "order": "asc"})
    assert "a-brouillon" not in _slugs(response)


@pytest.mark.asyncio
async def test_invalid_order_rejected(client: AsyncClient, db_session: AsyncSession):
    response = await client.get(BASE, params={"order": "foo"})
    assert response.status_code == 422
