"""
Router Admin - Liens courts
=============================

Endpoints CRUD pour la gestion des liens courts et domaines autorisés.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.identity import User
from app.models.short_links import ShortLink
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.short_links import (
    AllowedDomainCreate,
    AllowedDomainRead,
    ShortLinkCreate,
    ShortLinkRead,
)
from app.services.short_links_service import ShortLinkService

router = APIRouter(prefix="/short-links", tags=["Short Links"])

PRODUCTION_DOMAIN = "https://usenghor-francophonie.org"


# ===== Domaines autorisés (routes statiques AVANT routes dynamiques) =====


@router.get("/allowed-domains", response_model=dict)
async def list_allowed_domains(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("short_links.view")),
) -> dict:
    """Liste les domaines autorisés."""
    service = ShortLinkService(db)
    domains = await service.list_allowed_domains()
    return {
        "items": [AllowedDomainRead.model_validate(d) for d in domains],
    }


@router.post(
    "/allowed-domains",
    response_model=IdResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_allowed_domain(
    data: AllowedDomainCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("short_links.create")),
) -> IdResponse:
    """Ajoute un domaine à la liste blanche."""
    service = ShortLinkService(db)
    domain = await service.add_allowed_domain(data.domain)
    return IdResponse(id=domain.id, message="Domaine ajouté avec succès")


@router.delete("/allowed-domains/{domain_id}", response_model=MessageResponse)
async def remove_allowed_domain(
    domain_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("short_links.delete")),
) -> MessageResponse:
    """Supprime un domaine de la liste blanche."""
    service = ShortLinkService(db)
    await service.remove_allowed_domain(domain_id)
    return MessageResponse(message="Domaine supprimé avec succès")


# ===== Liens courts =====


@router.get("", response_model=dict)
async def list_short_links(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur code ou URL"),
    _: bool = Depends(PermissionChecker("short_links.view")),
) -> dict:
    """Liste les liens courts avec pagination."""
    service = ShortLinkService(db)
    query = await service.list_short_links(search=search)
    result = await paginate(db, query, pagination, ShortLink, ShortLinkRead)

    # Enrichir chaque item avec full_short_url et created_by_name
    for item in result["items"]:
        if isinstance(item, dict):
            item["full_short_url"] = f"{PRODUCTION_DOMAIN}/r/{item['code']}"
        else:
            item.full_short_url = f"{PRODUCTION_DOMAIN}/r/{item.code}"

    # Résoudre created_by_name via une requête séparée
    from sqlalchemy import select as sa_select

    items_list = result["items"]
    if items_list:
        # Collecter les IDs des créateurs
        creator_ids = set()
        for item in items_list:
            cb = item["created_by"] if isinstance(item, dict) else getattr(item, "created_by", None)
            if cb:
                creator_ids.add(cb)

        if creator_ids:
            users_result = await db.execute(
                sa_select(User.id, User.first_name, User.last_name).where(
                    User.id.in_(creator_ids)
                )
            )
            users_map = {
                row.id: f"{row.first_name or ''} {row.last_name or ''}".strip()
                for row in users_result.all()
            }

            for item in items_list:
                if isinstance(item, dict):
                    cb = item.get("created_by")
                    item["created_by_name"] = users_map.get(cb, None)
                else:
                    cb = getattr(item, "created_by", None)
                    item.created_by_name = users_map.get(cb, None)

    return result


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_short_link(
    data: ShortLinkCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("short_links.create")),
) -> IdResponse:
    """Crée un nouveau lien court."""
    service = ShortLinkService(db)
    link = await service.create_short_link(
        target_url=data.target_url,
        created_by=current_user.id,
    )
    return IdResponse(id=link.id, message="Lien court créé avec succès")


@router.delete("/{link_id}", response_model=MessageResponse)
async def delete_short_link(
    link_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("short_links.delete")),
) -> MessageResponse:
    """Supprime un lien court."""
    service = ShortLinkService(db)
    await service.delete_short_link(link_id)
    return MessageResponse(message="Lien court supprimé avec succès")
