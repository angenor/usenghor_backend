"""
Tests d'intégration — admin des services (refonte « Organisation »)
===================================================================

Couvre : compteurs de la liste admin, réordonnancement des objectifs et de
l'équipe, placement en fin de liste à la création, champs riches trilingues
des sous-éléments.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Permission, Role, RolePermission
from app.models.organization import (
    Sector,
    Service,
    ServiceAchievement,
    ServiceMediaLibrary,
    ServiceObjective,
    ServiceProject,
    ServiceTeam,
)
from app.services import translation_service


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


@pytest.fixture
def translator_stub(monkeypatch):
    """Remplace la traduction réseau par un stub déterministe « [lang] texte »."""

    async def fake_translate(src, lang, source=None):
        if not src or not str(src).strip():
            return None
        return f"[{lang}] {src}"

    monkeypatch.setattr(translation_service, "translate_text", fake_translate)
    monkeypatch.setattr(translation_service, "translate_html", fake_translate)


def _objective(service_id: str, title: str, order: int) -> ServiceObjective:
    return ServiceObjective(
        id=str(uuid4()),
        service_id=service_id,
        title=title,
        title_en=f"{title} (en)",
        title_ar=f"{title} (ar)",
        display_order=order,
    )


def _member(service_id: str, position: str, order: int) -> ServiceTeam:
    return ServiceTeam(
        id=str(uuid4()),
        service_id=service_id,
        user_external_id=str(uuid4()),
        position=position,
        display_order=order,
        active=True,
    )


@pytest_asyncio.fixture
async def org_data(db_session: AsyncSession) -> SimpleNamespace:
    sector = Sector(id=str(uuid4()), code="SEC-T", name="Secteur test", display_order=1, active=True)
    db_session.add(sector)
    await db_session.flush()

    full = Service(
        id=str(uuid4()), sector_id=sector.id, name="Service complet",
        name_en="Full (en)", name_ar="Full (ar)", display_order=1, active=True,
    )
    empty = Service(
        id=str(uuid4()), sector_id=sector.id, name="Service vide",
        name_en="Empty (en)", name_ar="Empty (ar)", display_order=2, active=True,
    )
    other = Service(
        id=str(uuid4()), sector_id=sector.id, name="Autre service",
        name_en="Other (en)", name_ar="Other (ar)", display_order=3, active=True,
    )
    db_session.add_all([full, empty, other])
    await db_session.flush()

    objectives = [_objective(full.id, f"Objectif {i}", i) for i in range(3)]
    members = [_member(full.id, f"Poste {i}", i) for i in range(2)]
    other_objective = _objective(other.id, "Objectif étranger", 0)
    other_member = _member(other.id, "Poste étranger", 0)
    db_session.add_all(objectives + members + [other_objective, other_member])
    db_session.add_all(
        [
            ServiceAchievement(
                id=str(uuid4()), service_id=full.id, title=f"Réalisation {i}",
                title_en="a", title_ar="a",
            )
            for i in range(4)
        ]
    )
    db_session.add(
        ServiceProject(id=str(uuid4()), service_id=full.id, title="Projet", title_en="p", title_ar="p")
    )
    db_session.add_all(
        [ServiceMediaLibrary(service_id=full.id, album_external_id=str(uuid4())) for _ in range(2)]
    )
    await db_session.commit()
    return SimpleNamespace(
        sector=sector, full=full, empty=empty, other=other,
        objectives=objectives, members=members,
        other_objective=other_objective, other_member=other_member,
    )


# =============================================================================
# Liste admin : compteurs
# =============================================================================


@pytest.mark.asyncio
async def test_list_services_includes_counts(
    authenticated_client: AsyncClient, organization_permissions, org_data
):
    resp = await authenticated_client.get("/api/admin/services", params={"limit": 500})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) >= {"items", "total", "page", "limit", "pages"}
    assert body["total"] == 3
    by_id = {item["id"]: item for item in body["items"]}

    full = by_id[org_data.full.id]
    assert full["objectives_count"] == 3
    assert full["achievements_count"] == 4
    assert full["projects_count"] == 1
    assert full["team_count"] == 2
    assert full["albums_count"] == 2
    assert full["name"] == "Service complet"
    assert "objectives" not in full  # la liste n'expose que des compteurs

    empty = by_id[org_data.empty.id]
    for key in (
        "objectives_count", "achievements_count", "projects_count",
        "team_count", "albums_count",
    ):
        assert empty[key] == 0

    assert by_id[org_data.other.id]["objectives_count"] == 1
    assert by_id[org_data.other.id]["team_count"] == 1


@pytest.mark.asyncio
async def test_list_services_filters_and_pagination_unchanged(
    authenticated_client: AsyncClient, organization_permissions, org_data
):
    resp = await authenticated_client.get(
        "/api/admin/services", params={"search": "complet", "limit": 10}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == org_data.full.id
    assert body["items"][0]["objectives_count"] == 3

    resp = await authenticated_client.get("/api/admin/services", params={"limit": 1, "page": 2})
    body = resp.json()
    assert body["total"] == 3 and body["pages"] == 3 and len(body["items"]) == 1


# =============================================================================
# Réordonnancement des objectifs
# =============================================================================


@pytest.mark.asyncio
async def test_reorder_objectives_success(
    authenticated_client: AsyncClient, organization_permissions, org_data
):
    ids = [o.id for o in reversed(org_data.objectives)]
    resp = await authenticated_client.put(
        f"/api/admin/services/{org_data.full.id}/objectives/reorder",
        json={"objective_ids": ids},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert [o["id"] for o in data] == ids
    assert [o["display_order"] for o in data] == [0, 1, 2]

    resp = await authenticated_client.get(f"/api/admin/services/{org_data.full.id}/objectives")
    assert [o["id"] for o in resp.json()] == ids


@pytest.mark.asyncio
async def test_reorder_objectives_foreign_id_is_422(
    authenticated_client: AsyncClient, organization_permissions, org_data
):
    ids = [o.id for o in org_data.objectives] + [org_data.other_objective.id]
    resp = await authenticated_client.put(
        f"/api/admin/services/{org_data.full.id}/objectives/reorder",
        json={"objective_ids": ids},
    )
    assert resp.status_code == 422
    assert "n'appartiennent pas au service" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_reorder_objectives_incomplete_list_is_422(
    authenticated_client: AsyncClient, organization_permissions, org_data
):
    resp = await authenticated_client.put(
        f"/api/admin/services/{org_data.full.id}/objectives/reorder",
        json={"objective_ids": [org_data.objectives[0].id]},
    )
    assert resp.status_code == 422
    assert "tous les objectifs" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_reorder_objectives_empty_list_is_422(
    authenticated_client: AsyncClient, organization_permissions, org_data
):
    resp = await authenticated_client.put(
        f"/api/admin/services/{org_data.full.id}/objectives/reorder",
        json={"objective_ids": []},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reorder_objectives_unknown_service_is_404(
    authenticated_client: AsyncClient, organization_permissions, org_data
):
    resp = await authenticated_client.put(
        f"/api/admin/services/{uuid4()}/objectives/reorder",
        json={"objective_ids": [org_data.objectives[0].id]},
    )
    assert resp.status_code == 404


# =============================================================================
# Réordonnancement de l'équipe
# =============================================================================


@pytest.mark.asyncio
async def test_reorder_team_success(
    authenticated_client: AsyncClient, organization_permissions, org_data
):
    ids = [m.id for m in reversed(org_data.members)]
    resp = await authenticated_client.put(
        f"/api/admin/services/{org_data.full.id}/team/reorder",
        json={"member_ids": ids},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert [m["id"] for m in data] == ids
    assert [m["display_order"] for m in data] == [0, 1]

    resp = await authenticated_client.get(f"/api/admin/services/{org_data.full.id}/team")
    assert [m["id"] for m in resp.json()] == ids


@pytest.mark.asyncio
async def test_reorder_team_foreign_id_is_422(
    authenticated_client: AsyncClient, organization_permissions, org_data
):
    ids = [m.id for m in org_data.members] + [org_data.other_member.id]
    resp = await authenticated_client.put(
        f"/api/admin/services/{org_data.full.id}/team/reorder",
        json={"member_ids": ids},
    )
    assert resp.status_code == 422
    assert "n'appartiennent pas au service" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_reorder_team_unknown_service_is_404(
    authenticated_client: AsyncClient, organization_permissions, org_data
):
    resp = await authenticated_client.put(
        f"/api/admin/services/{uuid4()}/team/reorder",
        json={"member_ids": [org_data.members[0].id]},
    )
    assert resp.status_code == 404


# =============================================================================
# Création : placement en fin de liste
# =============================================================================


@pytest.mark.asyncio
async def test_create_objective_without_order_goes_last(
    authenticated_client: AsyncClient, organization_permissions, org_data, translator_stub
):
    url = f"/api/admin/services/{org_data.full.id}/objectives"
    resp = await authenticated_client.post(url, json={"title": "Nouvel objectif"})
    assert resp.status_code == 201, resp.text
    assert resp.json()["display_order"] == 3  # 0, 1, 2 existants

    resp = await authenticated_client.post(url, json={"title": "Placé", "display_order": 0})
    assert resp.status_code == 201
    assert resp.json()["display_order"] == 0

    # Service sans objectif : premier élément à 0
    resp = await authenticated_client.post(
        f"/api/admin/services/{org_data.empty.id}/objectives", json={"title": "Premier"}
    )
    assert resp.json()["display_order"] == 0


@pytest.mark.asyncio
async def test_create_team_member_without_order_goes_last(
    authenticated_client: AsyncClient, organization_permissions, org_data
):
    url = f"/api/admin/services/{org_data.full.id}/team"
    resp = await authenticated_client.post(
        url, json={"user_external_id": str(uuid4()), "position": "Chargé de mission"}
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["display_order"] == 2  # 0, 1 existants
    assert resp.json()["active"] is True

    resp = await authenticated_client.post(
        url,
        json={"user_external_id": str(uuid4()), "position": "Placé", "display_order": 0},
    )
    assert resp.status_code == 201
    assert resp.json()["display_order"] == 0


# =============================================================================
# Champs riches trilingues des sous-éléments
# =============================================================================


_RICH = {
    "description_html": "<p>Description</p>",
    "description_md": "Description",
    "title_en": "Title",
    "title_ar": "العنوان",
    "description_en_html": "<p>Description EN</p>",
    "description_en_md": "Description EN",
    "description_ar_html": "<p>الوصف</p>",
    "description_ar_md": "الوصف",
}


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["objectives", "achievements", "projects"])
async def test_subitems_persist_rich_trilingual_fields(
    authenticated_client: AsyncClient, organization_permissions, org_data, translator_stub, kind
):
    url = f"/api/admin/services/{org_data.empty.id}/{kind}"
    payload = {"title": "Titre", **_RICH}
    if kind == "achievements":
        payload["achievement_date"] = "2026-03-15"
    resp = await authenticated_client.post(url, json=payload)
    assert resp.status_code == 201, resp.text
    created = resp.json()
    for key, value in _RICH.items():
        assert created[key] == value, key
    if kind == "achievements":
        assert created["achievement_date"] == "2026-03-15"

    update = {
        "description_html": "<p>Modifiée</p>",
        "description_md": "Modifiée",
        "title_en": "Title 2",
        "description_ar_md": "الوصف 2",
    }
    if kind == "achievements":
        update["achievement_date"] = "2025-12-01"
    resp = await authenticated_client.put(f"{url}/{created['id']}", json=update)
    assert resp.status_code == 200, resp.text
    updated = resp.json()
    for key, value in update.items():
        assert updated[key] == value, key
    assert updated["description_en_html"] == _RICH["description_en_html"]

    resp = await authenticated_client.get(url)
    stored = next(i for i in resp.json() if i["id"] == created["id"])
    for key, value in update.items():
        assert stored[key] == value, key


# =============================================================================
# Secteurs : route statique /reorder, suppression gardée, ordre à la création
# =============================================================================


@pytest.mark.asyncio
async def test_reorder_sectors_route_not_captured_by_sector_id(
    authenticated_client: AsyncClient, organization_permissions, org_data, db_session: AsyncSession
):
    second = Sector(id=str(uuid4()), code="SEC-2", name="Second secteur", display_order=5, active=True)
    db_session.add(second)
    await db_session.commit()

    resp = await authenticated_client.put(
        "/api/admin/sectors/reorder",
        json={"sector_ids": [second.id, org_data.sector.id]},
    )
    assert resp.status_code == 200, resp.text
    assert [s["id"] for s in resp.json()][:2] == [second.id, org_data.sector.id]


@pytest.mark.asyncio
async def test_delete_service_with_content_is_409(
    authenticated_client: AsyncClient, organization_permissions, org_data
):
    resp = await authenticated_client.delete(f"/api/admin/services/{org_data.full.id}")
    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert "3 objectif(s)" in detail and "4 réalisation(s)" in detail and "1 projet(s)" in detail


@pytest.mark.asyncio
async def test_delete_empty_service_succeeds(
    authenticated_client: AsyncClient, organization_permissions, org_data
):
    resp = await authenticated_client.delete(f"/api/admin/services/{org_data.empty.id}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_service_without_order_goes_last_among_siblings(
    authenticated_client: AsyncClient, organization_permissions, org_data, translator_stub
):
    resp = await authenticated_client.post(
        "/api/admin/services",
        json={"name": "Nouveau service", "sector_id": org_data.sector.id},
    )
    assert resp.status_code == 201, resp.text
    new_id = resp.json()["id"]
    detail = (await authenticated_client.get(f"/api/admin/services/{new_id}")).json()
    assert detail["display_order"] == 4  # après 1, 2, 3

    # Un pôle démarre sa propre numérotation sous son parent.
    resp = await authenticated_client.post(
        "/api/admin/services",
        json={"name": "Pôle", "sector_id": org_data.sector.id, "parent_id": org_data.empty.id},
    )
    assert resp.status_code == 201, resp.text
    pole = (await authenticated_client.get(f"/api/admin/services/{resp.json()['id']}")).json()
    assert pole["display_order"] == 0
