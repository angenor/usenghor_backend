"""
Tests d'intégration — API admin PEI : partenaires du pôle
=========================================================

Spec : specs/022-pei-laureates-partners/contracts/admin-api.md
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import MediaType
from app.models.entrepreneurship import PeiPartner
from app.models.identity import AuditLog, Permission, Role, RolePermission
from app.models.media import Media
from app.models.partner import Partner, PartnerType

BASE = "/api/admin/entrepreneurship"
PERMISSION_CODES = [
    ("entrepreneurship.view", "Voir le pôle Entrepreneuriat"),
    ("entrepreneurship.create", "Créer des contenus du pôle Entrepreneuriat"),
    ("entrepreneurship.edit", "Modifier des contenus du pôle Entrepreneuriat"),
    ("entrepreneurship.delete", "Supprimer des contenus du pôle Entrepreneuriat"),
]


@pytest_asyncio.fixture
async def entrepreneurship_permissions(
    db_session: AsyncSession, admin_role: Role
) -> list[Permission]:
    """Greffe les 4 permissions entrepreneurship.* sur le rôle admin."""
    perms = []
    for code, name in PERMISSION_CODES:
        p = Permission(
            id=str(uuid4()),
            code=code,
            name_fr=name,
            category="entrepreneurship",
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
async def partners(db_session: AsyncSession) -> dict[str, Partner]:
    logo = Media(id=str(uuid4()), name="auf.png", type=MediaType.IMAGE, url="uploads/auf.png")
    db_session.add(logo)
    await db_session.flush()
    items = {
        "campus": Partner(name="Campus France", description="Agence française", type=PartnerType.OTHER, active=True),
        "auf": Partner(name="AUF", type=PartnerType.CHARTER_OPERATOR, active=True, logo_external_id=logo.id),
        "oif": Partner(name="OIF", type=PartnerType.CHARTER_OPERATOR, active=False),
        "cci": Partner(name="CCI Côte d'Ivoire", type=PartnerType.OTHER, active=True),
    }
    db_session.add_all(items.values())
    await db_session.commit()
    return items


async def _audits(db: AsyncSession, action: str):
    return (
        (await db.execute(select(AuditLog).where(AuditLog.action == action))).scalars().all()
    )


async def _link(client: AsyncClient, partner_id: str, family: str) -> dict:
    response = await client.post(f"{BASE}/partners", json={"partner_id": partner_id, "family": family})
    assert response.status_code == 201, response.text
    return response.json()


async def _family_orders(client: AsyncClient, family: str) -> list[tuple[str, int]]:
    body = (await client.get(f"{BASE}/partners", params={"family": family})).json()
    return [(i["partner_id"], i["display_order"]) for i in body]


@pytest.mark.asyncio
async def test_partner_routes_require_permission(authenticated_client: AsyncClient, partners):
    assert (await authenticated_client.get(f"{BASE}/partners")).status_code == 403
    response = await authenticated_client.post(
        f"{BASE}/partners", json={"partner_id": partners["auf"].id, "family": "academic"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_available_excludes_linked_partners(
    authenticated_client: AsyncClient, entrepreneurship_permissions, partners
):
    body = (await authenticated_client.get(f"{BASE}/partners/available")).json()
    names = [p["name"] for p in body]
    # Actifs d'abord (l'ordre alphabétique fin dépend de la collation de la base)
    assert names[0] == "AUF"
    assert set(names[:3]) == {"AUF", "Campus France", "CCI Côte d'Ivoire"}
    assert names[3] == "OIF"
    auf = next(p for p in body if p["name"] == "AUF")
    assert auf["logo_url"] == f"/api/public/media/{partners['auf'].logo_external_id}/download"
    assert set(auf) == {"id", "name", "type", "active", "logo_url"}

    await _link(authenticated_client, partners["auf"].id, "international")
    body = (await authenticated_client.get(f"{BASE}/partners/available")).json()
    assert "AUF" not in [p["name"] for p in body]

    searched = (
        await authenticated_client.get(f"{BASE}/partners/available", params={"q": "française"})
    ).json()
    assert [p["name"] for p in searched] == ["Campus France"]


@pytest.mark.asyncio
async def test_link_partner_conflict_and_errors(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    partners,
):
    created = await _link(authenticated_client, partners["campus"].id, "academic")
    assert created["display_order"] == 0
    assert created["family"] == "academic"
    assert created["partner"]["name"] == "Campus France"
    assert created["partner"]["active"] is True

    dup = await authenticated_client.post(
        f"{BASE}/partners", json={"partner_id": partners["campus"].id, "family": "support"}
    )
    assert dup.status_code == 409
    assert dup.json()["detail"] == "Ce partenaire est déjà rattaché au pôle"

    unknown = await authenticated_client.post(
        f"{BASE}/partners", json={"partner_id": str(uuid4()), "family": "support"}
    )
    assert unknown.status_code == 404

    bad_family = await authenticated_client.post(
        f"{BASE}/partners", json={"partner_id": partners["auf"].id, "family": "sponsors"}
    )
    assert bad_family.status_code == 422

    logs = await _audits(db_session, "entrepreneurship.partner.link")
    assert len(logs) == 1
    assert logs[0].record_id == partners["campus"].id
    assert logs[0].table_name == "pei_partners"


@pytest.mark.asyncio
async def test_change_family_reorder_and_unlink(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    partners,
):
    auf, oif, cci = partners["auf"].id, partners["oif"].id, partners["cci"].id
    await _link(authenticated_client, auf, "international")
    await _link(authenticated_client, oif, "international")
    await _link(authenticated_client, cci, "international")
    await _link(authenticated_client, partners["campus"].id, "support")

    # Inactif rattaché : visible en admin avec active = False
    listing = (await authenticated_client.get(f"{BASE}/partners")).json()
    assert [i["family"] for i in listing] == ["support", "international", "international", "international"]
    assert next(i for i in listing if i["partner_id"] == oif)["partner"]["active"] is False

    incomplete = await authenticated_client.patch(
        f"{BASE}/partners/reorder", json={"family": "international", "ids": [auf, oif]}
    )
    assert incomplete.status_code == 422

    reordered = await authenticated_client.patch(
        f"{BASE}/partners/reorder", json={"family": "international", "ids": [cci, auf, oif]}
    )
    assert reordered.status_code == 200, reordered.text
    assert await _family_orders(authenticated_client, "international") == [(cci, 0), (auf, 1), (oif, 2)]
    assert await _family_orders(authenticated_client, "support") == [(partners["campus"].id, 0)]

    moved = await authenticated_client.patch(f"{BASE}/partners/{cci}", json={"family": "support"})
    assert moved.status_code == 200, moved.text
    assert moved.json()["family"] == "support"
    assert moved.json()["display_order"] == 1
    assert await _family_orders(authenticated_client, "international") == [(auf, 0), (oif, 1)]

    removed = await authenticated_client.delete(f"{BASE}/partners/{auf}")
    assert removed.status_code == 204
    assert await _family_orders(authenticated_client, "international") == [(oif, 0)]
    still_there = await db_session.execute(select(func.count(Partner.id)).where(Partner.id == auf))
    assert still_there.scalar() == 1

    assert (await authenticated_client.delete(f"{BASE}/partners/{auf}")).status_code == 404

    for action in ("link", "reorder", "update", "unlink"):
        assert await _audits(db_session, f"entrepreneurship.partner.{action}"), action
    reorder_log = (await _audits(db_session, "entrepreneurship.partner.reorder"))[0]
    assert reorder_log.new_values == {"family": "international", "ids": [cci, auf, oif]}


@pytest.mark.asyncio
async def test_deleting_partner_cascades_link(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    entrepreneurship_permissions,
    partners,
):
    await _link(authenticated_client, partners["campus"].id, "academic")
    await db_session.execute(delete(Partner).where(Partner.id == partners["campus"].id))
    await db_session.commit()

    count = (await db_session.execute(select(func.count()).select_from(PeiPartner))).scalar()
    assert count == 0
    listing = await authenticated_client.get(f"{BASE}/partners")
    assert listing.status_code == 200
    assert listing.json() == []
