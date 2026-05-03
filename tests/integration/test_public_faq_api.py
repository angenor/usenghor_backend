"""
Tests d'intégration — Endpoint public FAQ
==========================================

Spec: specs/019-faq-backoffice/contracts/public-faq-api.md
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import FaqCategory, FaqEntry


@pytest.mark.asyncio
async def test_get_public_faq_excludes_inactive_categories(
    client: AsyncClient, db_session: AsyncSession
):
    """Une catégorie avec is_active = False ne doit pas apparaître."""
    active = FaqCategory(
        id=str(uuid4()),
        code="active",
        label_fr="Active",
        display_order=0,
        is_active=True,
    )
    inactive = FaqCategory(
        id=str(uuid4()),
        code="inactive",
        label_fr="Inactive",
        display_order=1,
        is_active=False,
    )
    db_session.add_all([active, inactive])
    await db_session.commit()

    response = await client.get("/api/public/faq")
    assert response.status_code == 200
    codes = [c["code"] for c in response.json()["categories"]]
    assert "active" in codes
    assert "inactive" not in codes


@pytest.mark.asyncio
async def test_get_public_faq_excludes_unpublished_entries(
    client: AsyncClient, db_session: AsyncSession
):
    """Une entrée non publiée ne doit pas apparaître."""
    cat = FaqCategory(
        id=str(uuid4()), code="cat1", label_fr="Cat 1", is_active=True
    )
    db_session.add(cat)
    await db_session.flush()

    published = FaqEntry(
        id=str(uuid4()),
        category_id=cat.id,
        slug="published-q",
        question_fr="Question publiée ?",
        answer_fr_md="md",
        answer_fr_html="<p>html</p>",
        is_published=True,
        published_at=datetime.now(timezone.utc),
    )
    draft = FaqEntry(
        id=str(uuid4()),
        category_id=cat.id,
        slug="draft-q",
        question_fr="Question brouillon ?",
        answer_fr_md="md",
        answer_fr_html="<p>html</p>",
        is_published=False,
    )
    db_session.add_all([published, draft])
    await db_session.commit()

    response = await client.get("/api/public/faq")
    assert response.status_code == 200
    entries = response.json()["categories"][0]["entries"]
    slugs = [e["slug"] for e in entries]
    assert "published-q" in slugs
    assert "draft-q" not in slugs


@pytest.mark.asyncio
async def test_get_public_faq_french_fallback(
    client: AsyncClient, db_session: AsyncSession
):
    """Si question_en/ar est NULL, l'API retourne la valeur FR."""
    cat = FaqCategory(
        id=str(uuid4()), code="fb", label_fr="FB", is_active=True
    )
    db_session.add(cat)
    await db_session.flush()

    entry = FaqEntry(
        id=str(uuid4()),
        category_id=cat.id,
        slug="fallback",
        question_fr="Question FR",
        question_en=None,
        question_ar=None,
        answer_fr_md="md",
        answer_fr_html="<p>FR html</p>",
        answer_en_html=None,
        answer_ar_html=None,
        is_published=True,
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(entry)
    await db_session.commit()

    response = await client.get("/api/public/faq")
    assert response.status_code == 200
    e = response.json()["categories"][0]["entries"][0]
    assert e["question_fr"] == "Question FR"
    assert e["question_en"] == "Question FR"
    assert e["question_ar"] == "Question FR"
    assert e["answer_en_html"] == "<p>FR html</p>"
    assert e["answer_ar_html"] == "<p>FR html</p>"


@pytest.mark.asyncio
async def test_get_public_faq_sorting(
    client: AsyncClient, db_session: AsyncSession
):
    """Catégories triées par display_order ; entrées triées par display_order."""
    cat_b = FaqCategory(
        id=str(uuid4()), code="b", label_fr="B", display_order=1, is_active=True
    )
    cat_a = FaqCategory(
        id=str(uuid4()), code="a", label_fr="A", display_order=0, is_active=True
    )
    db_session.add_all([cat_b, cat_a])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    e2 = FaqEntry(
        id=str(uuid4()),
        category_id=cat_a.id,
        slug="e2",
        question_fr="E2 ?",
        answer_fr_md="m",
        answer_fr_html="h",
        is_published=True,
        published_at=now + timedelta(seconds=10),
        display_order=1,
    )
    e1 = FaqEntry(
        id=str(uuid4()),
        category_id=cat_a.id,
        slug="e1",
        question_fr="E1 ?",
        answer_fr_md="m",
        answer_fr_html="h",
        is_published=True,
        published_at=now,
        display_order=0,
    )
    db_session.add_all([e2, e1])
    await db_session.commit()

    response = await client.get("/api/public/faq")
    cats = response.json()["categories"]
    assert [c["code"] for c in cats] == ["a", "b"]
    entries = cats[0]["entries"]
    assert [e["slug"] for e in entries] == ["e1", "e2"]


@pytest.mark.asyncio
async def test_get_public_faq_no_markdown_in_response(
    client: AsyncClient, db_session: AsyncSession
):
    """Les colonnes answer_*_md ne doivent jamais figurer dans la réponse."""
    cat = FaqCategory(
        id=str(uuid4()), code="c", label_fr="C", is_active=True
    )
    db_session.add(cat)
    await db_session.flush()

    entry = FaqEntry(
        id=str(uuid4()),
        category_id=cat.id,
        slug="q",
        question_fr="Q ?",
        answer_fr_md="**source markdown**",
        answer_fr_html="<p>html</p>",
        is_published=True,
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(entry)
    await db_session.commit()

    response = await client.get("/api/public/faq")
    e = response.json()["categories"][0]["entries"][0]
    assert "answer_fr_md" not in e
    assert "answer_en_md" not in e
    assert "answer_ar_md" not in e
    assert "**source markdown**" not in str(e)
