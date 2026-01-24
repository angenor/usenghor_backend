"""
Router Admin - Pays
===================

Endpoints CRUD pour la gestion des pays.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.pagination import PaginationParams, paginate
from app.models.core import Country
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.core import (
    CountryBulkToggle,
    CountryCreate,
    CountryImportISO,
    CountryRead,
    CountryUpdate,
)
from app.services.core_service import CoreService

router = APIRouter(prefix="/countries", tags=["Countries"])


@router.get("", response_model=dict)
async def list_countries(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur code ou nom"),
    active: bool | None = Query(None, description="Filtrer par statut actif"),
    _: bool = Depends(PermissionChecker("admin.settings")),
) -> dict:
    """Liste les pays avec pagination et filtres."""
    service = CoreService(db)
    query = await service.get_countries(search=search, active=active)
    return await paginate(db, query, pagination, Country)


@router.get("/{country_id}", response_model=CountryRead)
async def get_country(
    country_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("admin.settings")),
) -> Country:
    """Récupère un pays par son ID."""
    service = CoreService(db)
    country = await service.get_country_by_id(country_id)
    if not country:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Pays non trouvé")
    return country


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_country(
    country_data: CountryCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("admin.settings")),
) -> IdResponse:
    """Crée un nouveau pays."""
    service = CoreService(db)
    country = await service.create_country(
        iso_code=country_data.iso_code,
        iso_code3=country_data.iso_code3,
        name_fr=country_data.name_fr,
        name_en=country_data.name_en,
        name_ar=country_data.name_ar,
        phone_code=country_data.phone_code,
        active=country_data.active,
    )
    return IdResponse(id=country.id, message="Pays créé avec succès")


@router.put("/{country_id}", response_model=CountryRead)
async def update_country(
    country_id: str,
    country_data: CountryUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("admin.settings")),
) -> Country:
    """Met à jour un pays."""
    service = CoreService(db)
    update_dict = country_data.model_dump(exclude_unset=True)
    return await service.update_country(country_id, **update_dict)


@router.post("/{country_id}/toggle-active", response_model=CountryRead)
async def toggle_country_active(
    country_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("admin.settings")),
) -> Country:
    """Bascule le statut actif d'un pays."""
    service = CoreService(db)
    return await service.toggle_country_active(country_id)


@router.post("/bulk-toggle", response_model=MessageResponse)
async def bulk_toggle_countries(
    toggle_data: CountryBulkToggle,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("admin.settings")),
) -> MessageResponse:
    """Bascule le statut actif de plusieurs pays."""
    service = CoreService(db)
    count = await service.bulk_toggle_countries(
        toggle_data.country_ids, toggle_data.active
    )
    return MessageResponse(message=f"{count} pays modifié(s)")


@router.post("/import-iso", response_model=dict)
async def import_iso_countries(
    import_data: CountryImportISO,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("admin.settings")),
) -> dict:
    """Importe les pays depuis les données ISO."""
    service = CoreService(db)
    result = await service.import_iso_countries(import_data.overwrite_existing)
    return {
        "message": "Import terminé",
        **result,
    }
