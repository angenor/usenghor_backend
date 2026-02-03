"""
Router Public - Partenaires
===========================

Endpoints publics pour les partenaires.
"""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession
from app.core.pagination import PaginationParams, paginate
from app.models.partner import Partner, PartnerType
from app.schemas.partner import PartnerPublic
from app.services.partner_service import PartnerService

router = APIRouter(prefix="/partners", tags=["Partners"])


@router.get("", response_model=dict)
async def list_partners(
    db: DbSession,
    pagination: PaginationParams = Depends(),
    partner_type: PartnerType | None = Query(None, description="Filtrer par type"),
    country_id: str | None = Query(None, description="Filtrer par pays"),
) -> dict:
    """Liste les partenaires actifs."""
    service = PartnerService(db)
    query = await service.get_partners(
        partner_type=partner_type,
        country_id=country_id,
        active=True,  # Seulement les partenaires actifs
    )
    return await paginate(db, query, pagination, Partner, PartnerPublic)


@router.get("/by-type/{partner_type}", response_model=list[PartnerPublic])
async def list_partners_by_type(
    partner_type: PartnerType,
    db: DbSession,
) -> list[PartnerPublic]:
    """Liste les partenaires actifs d'un type donné."""
    service = PartnerService(db)
    partners = await service.get_partners_by_type(partner_type)
    return [PartnerPublic.model_validate(p) for p in partners]
