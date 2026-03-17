"""
Router Public - Levées de fonds
================================

Endpoints publics pour les levées de fonds.
"""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.fundraising import Fundraiser, FundraiserStatus
from app.schemas.fundraising import FundraiserPublic, FundraiserPublicDetail
from app.services.fundraising_service import FundraisingService

router = APIRouter(prefix="/fundraisers", tags=["Fundraisers"])


@router.get("", response_model=dict)
async def list_fundraisers(
    db: DbSession,
    pagination: PaginationParams = Depends(),
    status: FundraiserStatus | None = Query(None, description="Filtrer par statut"),
) -> dict:
    """Liste les levées de fonds publiées (active/completed)."""
    service = FundraisingService(db)
    query = await service.get_public_fundraisers(status=status)

    # Paginer puis enrichir avec les totaux
    result = await paginate(db, query, pagination, Fundraiser, schema_class=None)

    enriched_items = []
    for fundraiser in result["items"]:
        total_raised, contributor_count = await service._compute_totals(fundraiser.id)
        enrichment = service._enrich_fundraiser(fundraiser, total_raised, contributor_count)
        item = FundraiserPublic(
            id=fundraiser.id,
            title=fundraiser.title,
            slug=fundraiser.slug,
            cover_image_external_id=fundraiser.cover_image_external_id,
            goal_amount=fundraiser.goal_amount,
            total_raised=enrichment["total_raised"],
            progress_percentage=enrichment["progress_percentage"],
            status=fundraiser.status,
            contributor_count=enrichment["contributor_count"],
            created_at=fundraiser.created_at,
        )
        enriched_items.append(item)

    result["items"] = enriched_items
    return result


@router.get("/{slug}", response_model=FundraiserPublicDetail)
async def get_fundraiser_by_slug(
    slug: str,
    db: DbSession,
) -> dict:
    """Récupère le détail d'une levée de fonds publiée par son slug."""
    service = FundraisingService(db)
    detail = await service.get_fundraiser_public_detail(slug)
    if not detail:
        raise NotFoundException("Levée de fonds non trouvée")
    return detail
