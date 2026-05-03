"""
Tests d'intégration — Admin FAQ Entries API
=============================================

Spec : specs/019-faq-backoffice/contracts/admin-faq-api.md
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import FaqCategory, FaqEntry
from app.models.identity import AuditLog, Permission, Role, RolePermission


@pytest_asyncio.fixture
async def faq_permissions(
    db_session: AsyncSession, admin_role: Role
) -> list[Permission]:
    """Ajoute les permissions FAQ au rôle admin existant."""
    perms = []
    for code, name in [
        ("faq.view", "Voir la FAQ"),
        ("faq.create", "Créer une FAQ"),
        ("faq.edit", "Modifier la FAQ"),
        ("faq.delete", "Supprimer une FAQ"),
    ]:
        p = Permission(
            id=str(uuid4()),
            code=code,
            name_fr=name,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(p)
        perms.append(p)
    await db_session.flush()

    for p in perms:
        db_session.add(RolePermission(role_id=admin_role.id, permission_id=p.id))
    await db_session.commit()
    return perms


@pytest_asyncio.fixture
async def general_category(db_session: AsyncSession) -> FaqCategory:
    cat = FaqCategory(
        id=str(uuid4()),
        code="general",
        label_fr="Général",
        is_active=True,
        display_order=0,
    )
    db_session.add(cat)
    await db_session.commit()
    return cat


@pytest.mark.asyncio
async def test_post_entries_requires_auth(client: AsyncClient):
    response = await client.post(
        "/api/admin/faq/entries",
        json={
            "category_id": str(uuid4()),
            "question_fr": "Test ?",
            "answer_fr_md": "md",
            "answer_fr_html": "<p>html</p>",
        },
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_post_entries_generates_slug_when_omitted(
    authenticated_client: AsyncClient,
    faq_permissions,
    general_category: FaqCategory,
):
    response = await authenticated_client.post(
        "/api/admin/faq/entries",
        json={
            "category_id": general_category.id,
            "question_fr": "Comment postuler ?",
            "answer_fr_md": "md",
            "answer_fr_html": "<p>html</p>",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["slug"] == "comment-postuler"
    assert body["is_published"] is False


@pytest.mark.asyncio
async def test_post_entries_invalid_category_returns_400(
    authenticated_client: AsyncClient,
    faq_permissions,
):
    response = await authenticated_client.post(
        "/api/admin/faq/entries",
        json={
            "category_id": str(uuid4()),
            "question_fr": "Sans catégorie ?",
            "answer_fr_md": "md",
            "answer_fr_html": "<p>html</p>",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_publish_sets_published_at_first_time_only(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    faq_permissions,
    general_category: FaqCategory,
):
    create_resp = await authenticated_client.post(
        "/api/admin/faq/entries",
        json={
            "category_id": general_category.id,
            "question_fr": "Première publication ?",
            "answer_fr_md": "md",
            "answer_fr_html": "<p>html</p>",
        },
    )
    entry_id = create_resp.json()["id"]

    pub1 = await authenticated_client.patch(
        f"/api/admin/faq/entries/{entry_id}/publish",
        json={"is_published": True},
    )
    assert pub1.status_code == 200
    first_at = pub1.json()["published_at"]
    assert first_at is not None

    unpub = await authenticated_client.patch(
        f"/api/admin/faq/entries/{entry_id}/publish",
        json={"is_published": False},
    )
    assert unpub.status_code == 200
    assert unpub.json()["published_at"] == first_at  # conservé

    pub2 = await authenticated_client.patch(
        f"/api/admin/faq/entries/{entry_id}/publish",
        json={"is_published": True},
    )
    assert pub2.json()["published_at"] == first_at  # toujours conservé


@pytest.mark.asyncio
async def test_publish_refuses_when_answer_fr_html_empty(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    faq_permissions,
    general_category: FaqCategory,
):
    entry = FaqEntry(
        id=str(uuid4()),
        category_id=general_category.id,
        slug="empty-html",
        question_fr="Vide ?",
        answer_fr_md="md",
        answer_fr_html="x",  # On créé valide puis on vide en DB
    )
    db_session.add(entry)
    await db_session.commit()
    entry.answer_fr_html = ""
    await db_session.commit()

    response = await authenticated_client.patch(
        f"/api/admin/faq/entries/{entry.id}/publish",
        json={"is_published": True},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_entry_slug_collision_returns_409(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    faq_permissions,
    general_category: FaqCategory,
):
    e1 = FaqEntry(
        id=str(uuid4()),
        category_id=general_category.id,
        slug="taken-slug",
        question_fr="Q1 ?",
        answer_fr_md="m",
        answer_fr_html="<p>h</p>",
    )
    e2 = FaqEntry(
        id=str(uuid4()),
        category_id=general_category.id,
        slug="other",
        question_fr="Q2 ?",
        answer_fr_md="m",
        answer_fr_html="<p>h</p>",
    )
    db_session.add_all([e1, e2])
    await db_session.commit()

    response = await authenticated_client.patch(
        f"/api/admin/faq/entries/{e2.id}",
        json={"slug": "taken-slug"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_each_mutation_creates_audit_log(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    faq_permissions,
    general_category: FaqCategory,
):
    create_resp = await authenticated_client.post(
        "/api/admin/faq/entries",
        json={
            "category_id": general_category.id,
            "question_fr": "Audit ?",
            "answer_fr_md": "md",
            "answer_fr_html": "<p>html</p>",
        },
    )
    entry_id = create_resp.json()["id"]

    await authenticated_client.patch(
        f"/api/admin/faq/entries/{entry_id}",
        json={"question_fr": "Audit modifiée ?"},
    )
    await authenticated_client.patch(
        f"/api/admin/faq/entries/{entry_id}/publish",
        json={"is_published": True},
    )
    await authenticated_client.delete(f"/api/admin/faq/entries/{entry_id}")

    result = await db_session.execute(
        select(AuditLog.action).where(AuditLog.table_name == "faq_entries")
    )
    actions = {row[0] for row in result.all()}
    assert "faq.entry.create" in actions
    assert "faq.entry.update" in actions
    assert "faq.entry.publish" in actions
    assert "faq.entry.delete" in actions
