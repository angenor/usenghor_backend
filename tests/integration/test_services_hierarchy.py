"""
Tests d'intégration — hiérarchie des services (pôles), lectures publiques et liens courts
=========================================================================================

Spec : specs/026-pei-org-navigation-launch/contracts/api.md
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Permission, Role, RolePermission
from app.models.organization import Sector, Service


@pytest_asyncio.fixture
async def organization_permissions(
    db_session: AsyncSession, admin_role: Role
) -> list[Permission]:
    perms = []
    for code, name in [
        ("organization.view", "Voir l'organisation"),
        ("organization.edit", "Modifier l'organisation"),
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


def _service(sector_id: str | None, name: str, sigle: str, order: int, **kwargs) -> Service:
    return Service(
        id=str(uuid4()),
        sector_id=sector_id,
        name=name,
        # Traductions renseignées : évite l'appel au traducteur réel
        name_en=f"{name} (en)",
        name_ar=f"{name} (ar)",
        sigle=sigle,
        display_order=order,
        **kwargs,
    )


@pytest_asyncio.fixture
async def org_tree(db_session: AsyncSession) -> SimpleNamespace:
    sec_a = Sector(id=str(uuid4()), code="SEC-A", name="Secteur A", display_order=1, active=True)
    sec_b = Sector(id=str(uuid4()), code="SEC-B", name="Secteur B", display_order=2, active=True)
    db_session.add_all([sec_a, sec_b])
    await db_session.flush()

    dde = _service(sec_a.id, "Direction du développement", "DDE", 2, active=True)
    dre = _service(sec_a.id, "Direction des relations", "DRE", 3, active=True)
    old = _service(sec_a.id, "Ancien service", "OLD", 1, active=False)
    other = _service(sec_b.id, "Service du secteur B", "XB", 1, active=True)
    db_session.add_all([dde, dre, old, other])
    await db_session.commit()
    return SimpleNamespace(sec_a=sec_a, sec_b=sec_b, dde=dde, dre=dre, old=old, other=other)


# =============================================================================
# Régression C1 : les lectures publiques des secteurs ne suppriment rien
# =============================================================================


@pytest.mark.asyncio
async def test_public_sector_reads_do_not_delete_inactive_services(
    client: AsyncClient, db_session: AsyncSession, org_tree
):
    resp = await client.get("/api/public/sectors/with-services")
    assert resp.status_code == 200
    sector_a = next(s for s in resp.json() if s["code"] == "SEC-A")
    assert org_tree.old.id not in [s["id"] for s in sector_a["services"]]

    resp = await client.get("/api/public/sectors/SEC-A")
    assert resp.status_code == 200
    assert org_tree.old.id not in [s["id"] for s in resp.json()["services"]]

    await db_session.commit()
    db_session.expunge_all()
    still_there = (
        await db_session.execute(select(Service).where(Service.id == org_tree.old.id))
    ).scalar_one_or_none()
    assert still_there is not None, "le service inactif a été supprimé par une lecture publique"


# =============================================================================
# US1 : imbrication publique des pôles
# =============================================================================


@pytest_asyncio.fixture
async def pole(db_session: AsyncSession, org_tree) -> Service:
    svc = _service(
        org_tree.sec_a.id,
        "Pôle Entrepreneuriat et Innovation",
        "PEI",
        0,
        active=True,
        parent_id=org_tree.dde.id,
        landing_path="/entrepreneuriat",
    )
    db_session.add(svc)
    await db_session.commit()
    return svc


@pytest.mark.asyncio
async def test_with_services_nests_poles_under_parent(
    client: AsyncClient, db_session: AsyncSession, org_tree, pole
):
    resp = await client.get("/api/public/sectors/with-services")
    assert resp.status_code == 200
    sector_a = next(s for s in resp.json() if s["code"] == "SEC-A")
    assert [s["id"] for s in sector_a["services"]] == [org_tree.dde.id, org_tree.dre.id]
    dde, dre = sector_a["services"]
    assert [c["id"] for c in dde["children"]] == [pole.id]
    assert dde["children"][0]["landing_path"] == "/entrepreneuriat"
    assert dde["children"][0]["parent_id"] == org_tree.dde.id
    assert dre["children"] == []

    resp = await client.get("/api/public/sectors/SEC-A")
    assert resp.status_code == 200
    services = resp.json()["services"]
    assert [s["id"] for s in services] == [org_tree.dde.id, org_tree.dre.id]
    assert [c["id"] for c in services[0]["children"]] == [pole.id]


@pytest.mark.asyncio
async def test_inactive_parent_hides_poles_without_deleting(
    client: AsyncClient, db_session: AsyncSession, org_tree, pole
):
    org_tree.dde.active = False
    await db_session.commit()

    resp = await client.get("/api/public/sectors/with-services")
    sector_a = next(s for s in resp.json() if s["code"] == "SEC-A")
    ids = [s["id"] for s in sector_a["services"]]
    children = [c["id"] for s in sector_a["services"] for c in s["children"]]
    assert org_tree.dde.id not in ids
    assert pole.id not in ids and pole.id not in children

    resp = await client.get(f"/api/public/services/{pole.id}")
    assert resp.status_code == 200
    assert resp.json()["parent"] is None

    await db_session.commit()
    db_session.expunge_all()
    assert (
        await db_session.execute(select(Service).where(Service.id == org_tree.dde.id))
    ).scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_public_service_list_and_detail_expose_hierarchy(
    client: AsyncClient, org_tree, pole
):
    resp = await client.get("/api/public/services")
    assert resp.status_code == 200
    listed = next(s for s in resp.json() if s["id"] == pole.id)
    assert listed["parent_id"] == org_tree.dde.id
    assert listed["landing_path"] == "/entrepreneuriat"

    resp = await client.get(f"/api/public/services/{pole.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["parent"]["id"] == org_tree.dde.id
    assert body["parent"]["sigle"] == "DDE"
    assert body["children"] == []

    resp = await client.get(f"/api/public/services/{org_tree.dde.id}")
    body = resp.json()
    assert body["parent"] is None
    assert [c["id"] for c in body["children"]] == [pole.id]
    assert body["children"][0]["landing_path"] == "/entrepreneuriat"


# =============================================================================
# US2 : règles de hiérarchie en écriture (admin)
# =============================================================================


async def _reload(db_session: AsyncSession, service_id: str) -> Service | None:
    db_session.expunge_all()
    return (
        await db_session.execute(select(Service).where(Service.id == service_id))
    ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_admin_hierarchy_refusals(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    organization_permissions,
    org_tree,
    pole,
):
    api = "/api/admin/services"
    cases = [
        ("post", api, {"name": "Nouveau", "name_en": "New", "name_ar": "جديد", "sector_id": org_tree.sec_a.id, "parent_id": str(uuid4())}, 422, "Service parent introuvable"),
        ("post", api, {"name": "Nouveau", "name_en": "New", "name_ar": "جديد", "sector_id": org_tree.sec_a.id, "parent_id": "pas-un-uuid"}, 422, "Service parent introuvable"),
        ("put", f"{api}/{org_tree.dde.id}", {"parent_id": org_tree.dde.id}, 422, "Un service ne peut pas être son propre parent"),
        ("put", f"{api}/{org_tree.dre.id}", {"parent_id": pole.id}, 409, "Le service parent est lui-même un pôle : un seul niveau est autorisé"),
        ("put", f"{api}/{org_tree.dde.id}", {"parent_id": org_tree.dre.id}, 409, "Ce service a 1 pôle(s) : il ne peut pas être rattaché"),
        ("put", f"{api}/{org_tree.other.id}", {"parent_id": org_tree.dde.id}, 409, "Le service parent doit appartenir au même secteur"),
        ("put", f"{api}/{org_tree.dde.id}", {"sector_id": org_tree.sec_b.id}, 409, "Déplacez ou détachez d'abord ses 1 pôle(s)"),
        ("put", f"{api}/{pole.id}", {"sector_id": org_tree.sec_b.id}, 409, "Le service parent doit appartenir au même secteur"),
    ]
    for method, url, payload, code, detail in cases:
        resp = await getattr(authenticated_client, method)(url, json=payload)
        assert resp.status_code == code, (url, payload, resp.text)
        assert resp.json()["detail"] == detail

    # Rien n'a été enregistré
    assert (await _reload(db_session, org_tree.dde.id)).parent_id is None
    assert (await _reload(db_session, org_tree.dde.id)).sector_id == org_tree.sec_a.id
    assert (await _reload(db_session, org_tree.dre.id)).parent_id is None
    assert (await _reload(db_session, org_tree.other.id)).parent_id is None
    assert (await _reload(db_session, pole.id)).sector_id == org_tree.sec_a.id
    count = (await db_session.execute(select(Service).where(Service.name == "Nouveau"))).all()
    assert count == []


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["en/x", "//x", "/en/x", "/ar", "/r/pei", "/a b", "/x?y", "/x#y"])
async def test_admin_invalid_landing_path(
    authenticated_client: AsyncClient, organization_permissions, org_tree, value
):
    resp = await authenticated_client.put(
        f"/api/admin/services/{org_tree.dre.id}", json={"landing_path": value}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_admin_hierarchy_accepted_cases(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    organization_permissions,
    org_tree,
    pole,
):
    api = "/api/admin/services"

    resp = await authenticated_client.put(f"{api}/{org_tree.dre.id}", json={"landing_path": "  "})
    assert resp.status_code == 200
    assert resp.json()["landing_path"] is None

    resp = await authenticated_client.put(f"{api}/{org_tree.dre.id}", json={"parent_id": org_tree.dde.id})
    assert resp.status_code == 200, resp.text
    assert resp.json()["parent_id"] == org_tree.dde.id

    resp = await authenticated_client.put(f"{api}/{org_tree.dre.id}", json={"parent_id": None})
    assert resp.status_code == 200
    assert resp.json()["parent_id"] is None

    resp = await authenticated_client.post(f"{api}/{pole.id}/duplicate", params={"new_name": "Copie"})
    assert resp.status_code == 201, resp.text
    copy = await _reload(db_session, resp.json()["id"])
    assert copy.parent_id == org_tree.dde.id
    assert copy.landing_path is None

    resp = await authenticated_client.delete(f"{api}/{org_tree.dde.id}")
    assert resp.status_code == 200, resp.text
    detached = await _reload(db_session, pole.id)
    assert detached is not None
    assert detached.parent_id is None


# =============================================================================
# Liens courts : la génération saute les codes déjà pris
# =============================================================================


@pytest.mark.asyncio
async def test_create_short_link_skips_taken_code(db_session: AsyncSession):
    from sqlalchemy import text

    from app.models.short_links import ShortLink
    from app.services.short_links_service import ShortLinkService, int_to_base36

    await db_session.execute(text(
        "CREATE SEQUENCE IF NOT EXISTS short_link_counter_seq START WITH 0 MINVALUE 0 MAXVALUE 1679615"
    ))
    # Prochain nextval = 32922 → « pei »
    await db_session.execute(text("SELECT setval('short_link_counter_seq', 32921)"))
    assert int_to_base36(32922) == "pei"
    db_session.add(ShortLink(id=str(uuid4()), code="pei", target_url="/entrepreneuriat"))
    await db_session.flush()

    link = await ShortLinkService(db_session).create_short_link("/actualites", created_by=None)

    assert link.code != "pei"
    assert link.code == int_to_base36(32923)
