"""
Tests unitaires — Génération de slug FAQ
==========================================
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import FaqCategory, FaqEntry
from app.services.faq_slug import _slugify, generate_slug


@pytest.mark.unit
def test_slugify_basic():
    assert _slugify("Comment postuler ?") == "comment-postuler"


@pytest.mark.unit
def test_slugify_handles_accents():
    assert _slugify("Café & thé") == "cafe-the"


@pytest.mark.unit
def test_slugify_arabic_returns_empty_string():
    # Translit ASCII pure : l'arabe se réduit à une chaîne vide
    assert _slugify("ما هي الجامعة") == ""


@pytest.mark.asyncio
async def test_generate_slug_uses_fallback_when_empty(db_session: AsyncSession):
    slug = await generate_slug("ما هي", db_session)
    assert slug == "question"


@pytest.mark.asyncio
async def test_generate_slug_increments_on_collision(db_session: AsyncSession):
    cat = FaqCategory(
        id=str(uuid4()),
        code="general",
        label_fr="Général",
        is_active=True,
    )
    db_session.add(cat)
    await db_session.flush()

    existing = FaqEntry(
        id=str(uuid4()),
        category_id=cat.id,
        slug="comment-postuler",
        question_fr="Comment postuler ?",
        answer_fr_md="m",
        answer_fr_html="<p>h</p>",
    )
    db_session.add(existing)
    await db_session.commit()

    new_slug = await generate_slug("Comment postuler ?", db_session)
    assert new_slug == "comment-postuler-2"
