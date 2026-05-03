"""
Tests d'intégration — Admin FAQ Categories API
================================================

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


@pytest.mark.asyncio
async def test_categories_full_crud(
    authenticated_client: AsyncClient, faq_permissions
):
    # Create
    create_resp = await authenticated_client.post(
        "/api/admin/faq/categories",
        json={
            "code": "admissions",
            "label_fr": "Admissions",
            "label_en": "Admissions",
            "is_active": True,
        },
    )
    assert create_resp.status_code == 201
    cat = create_resp.json()
    cat_id = cat["id"]

    # Read list
    list_resp = await authenticated_client.get("/api/admin/faq/categories")
    assert list_resp.status_code == 200
    assert any(c["id"] == cat_id for c in list_resp.json()["categories"])

    # Update
    update_resp = await authenticated_client.patch(
        f"/api/admin/faq/categories/{cat_id}",
        json={"label_fr": "Admissions 2026"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["label_fr"] == "Admissions 2026"

    # Delete (vide)
    delete_resp = await authenticated_client.delete(
        f"/api/admin/faq/categories/{cat_id}"
    )
    assert delete_resp.status_code == 204


@pytest.mark.asyncio
async def test_category_code_immutable(
    authenticated_client: AsyncClient, faq_permissions
):
    create_resp = await authenticated_client.post(
        "/api/admin/faq/categories",
        json={"code": "test_immut", "label_fr": "Test"},
    )
    cat_id = create_resp.json()["id"]

    # Le PATCH avec code doit l'ignorer (FaqCategoryUpdate ne contient pas code)
    update_resp = await authenticated_client.patch(
        f"/api/admin/faq/categories/{cat_id}",
        json={"code": "nouveau_code", "label_fr": "Test 2"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["code"] == "test_immut"


@pytest.mark.asyncio
async def test_delete_non_empty_category_returns_409(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    faq_permissions,
):
    cat = FaqCategory(
        id=str(uuid4()),
        code="non_vide",
        label_fr="Non vide",
        is_active=True,
    )
    db_session.add(cat)
    await db_session.flush()
    db_session.add(
        FaqEntry(
            id=str(uuid4()),
            category_id=cat.id,
            slug="x",
            question_fr="Q ?",
            answer_fr_md="m",
            answer_fr_html="<p>h</p>",
        )
    )
    await db_session.commit()

    response = await authenticated_client.delete(
        f"/api/admin/faq/categories/{cat.id}"
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_general_category_refused(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    faq_permissions,
):
    cat = FaqCategory(
        id=str(uuid4()),
        code="general",
        label_fr="Général",
        is_active=True,
    )
    db_session.add(cat)
    await db_session.commit()

    response = await authenticated_client.delete(
        f"/api/admin/faq/categories/{cat.id}"
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_reorder_persists(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    faq_permissions,
):
    cats = []
    for i, code in enumerate(["a", "b", "c"]):
        c = FaqCategory(
            id=str(uuid4()),
            code=code,
            label_fr=code.upper(),
            is_active=True,
            display_order=i,
        )
        cats.append(c)
        db_session.add(c)
    await db_session.commit()

    response = await authenticated_client.patch(
        "/api/admin/faq/categories/reorder",
        json={
            "items": [
                {"id": cats[2].id, "display_order": 0},
                {"id": cats[0].id, "display_order": 1},
                {"id": cats[1].id, "display_order": 2},
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["updated"] == 3

    list_resp = await authenticated_client.get("/api/admin/faq/categories")
    codes = [c["code"] for c in list_resp.json()["categories"]]
    assert codes == ["c", "a", "b"]


@pytest.mark.asyncio
async def test_each_mutation_creates_audit_log(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    faq_permissions,
):
    create_resp = await authenticated_client.post(
        "/api/admin/faq/categories",
        json={"code": "audited", "label_fr": "Audit"},
    )
    cat_id = create_resp.json()["id"]

    await authenticated_client.patch(
        f"/api/admin/faq/categories/{cat_id}", json={"label_fr": "Modifié"}
    )
    await authenticated_client.delete(f"/api/admin/faq/categories/{cat_id}")

    result = await db_session.execute(
        select(AuditLog.action).where(AuditLog.table_name == "faq_categories")
    )
    actions = {row[0] for row in result.all()}
    assert "faq.category.create" in actions
    assert "faq.category.update" in actions
    assert "faq.category.delete" in actions
