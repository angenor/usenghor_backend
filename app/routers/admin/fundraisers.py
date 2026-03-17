"""
Router Admin - Levées de fonds
===============================

Endpoints admin pour la gestion des levées de fonds.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.pagination import PaginationParams, paginate
from app.models.fundraising import Fundraiser, FundraiserStatus
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.fundraising import (
    ContributorCreate,
    ContributorRead,
    ContributorUpdate,
    FundraiserCreate,
    FundraiserNewsCreate,
    FundraiserRead,
    FundraiserStatistics,
    FundraiserUpdate,
)
from app.services.fundraising_service import FundraisingService

router = APIRouter(prefix="/fundraisers", tags=["Fundraisers"])


# =============================================================================
# STATISTIQUES
# =============================================================================


@router.get("/statistics", response_model=FundraiserStatistics)
async def get_statistics(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.view")),
) -> dict:
    """Statistiques des levées de fonds."""
    service = FundraisingService(db)
    return await service.get_statistics()


# =============================================================================
# FUNDRAISERS CRUD
# =============================================================================


@router.get("", response_model=dict)
async def list_fundraisers(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Rechercher par titre"),
    status: FundraiserStatus | None = Query(None, description="Filtrer par statut"),
    _: bool = Depends(PermissionChecker("fundraisers.view")),
) -> dict:
    """Liste les levées de fonds (tous statuts)."""
    service = FundraisingService(db)
    query = await service.get_fundraisers(search=search, status=status)

    # Paginer puis enrichir avec les totaux
    result = await paginate(db, query, pagination, Fundraiser, schema_class=None)

    enriched_items = []
    for fundraiser in result["items"]:
        total_raised, contributor_count = await service._compute_totals(fundraiser.id)
        enrichment = service._enrich_fundraiser(fundraiser, total_raised, contributor_count)
        item = FundraiserRead.model_validate(fundraiser)
        item.total_raised = enrichment["total_raised"]
        item.progress_percentage = enrichment["progress_percentage"]
        item.contributor_count = enrichment["contributor_count"]
        enriched_items.append(item)

    result["items"] = enriched_items
    return result


@router.get("/{fundraiser_id}", response_model=FundraiserRead)
async def get_fundraiser(
    fundraiser_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.view")),
) -> Fundraiser:
    """Récupère une levée de fonds par son ID."""
    service = FundraisingService(db)
    fundraiser = await service.get_fundraiser_by_id(fundraiser_id)
    if not fundraiser:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Levée de fonds non trouvée")

    total_raised, contributor_count = await service._compute_totals(fundraiser_id)
    enrichment = service._enrich_fundraiser(fundraiser, total_raised, contributor_count)
    result = FundraiserRead.model_validate(fundraiser)
    result.total_raised = enrichment["total_raised"]
    result.progress_percentage = enrichment["progress_percentage"]
    result.contributor_count = enrichment["contributor_count"]
    return result


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_fundraiser(
    data: FundraiserCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.create")),
) -> IdResponse:
    """Crée une levée de fonds."""
    service = FundraisingService(db)
    fundraiser = await service.create_fundraiser(**data.model_dump())
    return IdResponse(id=fundraiser.id, message="Levée de fonds créée avec succès")


@router.put("/{fundraiser_id}", response_model=FundraiserRead)
async def update_fundraiser(
    fundraiser_id: str,
    data: FundraiserUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.edit")),
) -> Fundraiser:
    """Met à jour une levée de fonds."""
    service = FundraisingService(db)
    update_dict = data.model_dump(exclude_unset=True)
    fundraiser = await service.update_fundraiser(fundraiser_id, **update_dict)

    total_raised, contributor_count = await service._compute_totals(fundraiser_id)
    enrichment = service._enrich_fundraiser(fundraiser, total_raised, contributor_count)
    result = FundraiserRead.model_validate(fundraiser)
    result.total_raised = enrichment["total_raised"]
    result.progress_percentage = enrichment["progress_percentage"]
    result.contributor_count = enrichment["contributor_count"]
    return result


@router.delete("/{fundraiser_id}", response_model=MessageResponse)
async def delete_fundraiser(
    fundraiser_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.delete")),
) -> MessageResponse:
    """Supprime une levée de fonds."""
    service = FundraisingService(db)
    await service.delete_fundraiser(fundraiser_id)
    return MessageResponse(message="Levée de fonds supprimée avec succès")


# =============================================================================
# CONTRIBUTORS
# =============================================================================


@router.get("/{fundraiser_id}/contributors", response_model=list[ContributorRead])
async def list_contributors(
    fundraiser_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.view")),
) -> list:
    """Liste les contributeurs d'une levée de fonds."""
    service = FundraisingService(db)
    fundraiser = await service.get_fundraiser_by_id(fundraiser_id)
    if not fundraiser:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Levée de fonds non trouvée")
    return fundraiser.contributors


@router.post(
    "/{fundraiser_id}/contributors",
    response_model=IdResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_contributor(
    fundraiser_id: str,
    data: ContributorCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.edit")),
) -> IdResponse:
    """Ajoute un contributeur à une levée de fonds."""
    service = FundraisingService(db)
    contributor = await service.add_contributor(fundraiser_id, **data.model_dump())
    return IdResponse(id=contributor.id, message="Contributeur ajouté avec succès")


@router.put(
    "/{fundraiser_id}/contributors/{contributor_id}",
    response_model=ContributorRead,
)
async def update_contributor(
    fundraiser_id: str,
    contributor_id: str,
    data: ContributorUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.edit")),
) -> ContributorRead:
    """Met à jour un contributeur."""
    service = FundraisingService(db)
    update_dict = data.model_dump(exclude_unset=True)
    contributor = await service.update_contributor(contributor_id, **update_dict)
    return contributor


@router.delete(
    "/{fundraiser_id}/contributors/{contributor_id}",
    response_model=MessageResponse,
)
async def delete_contributor(
    fundraiser_id: str,
    contributor_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.delete")),
) -> MessageResponse:
    """Supprime un contributeur."""
    service = FundraisingService(db)
    await service.delete_contributor(contributor_id)
    return MessageResponse(message="Contributeur supprimé avec succès")


# =============================================================================
# NEWS ASSOCIATIONS
# =============================================================================


@router.post(
    "/{fundraiser_id}/news",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def associate_news(
    fundraiser_id: str,
    data: FundraiserNewsCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.edit")),
) -> MessageResponse:
    """Associe une actualité à une levée de fonds."""
    service = FundraisingService(db)
    await service.associate_news(fundraiser_id, data.news_id)
    return MessageResponse(message="Actualité associée avec succès")


@router.delete(
    "/{fundraiser_id}/news/{news_id}",
    response_model=MessageResponse,
)
async def dissociate_news(
    fundraiser_id: str,
    news_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.edit")),
) -> MessageResponse:
    """Dissocie une actualité d'une levée de fonds."""
    service = FundraisingService(db)
    await service.dissociate_news(fundraiser_id, news_id)
    return MessageResponse(message="Actualité dissociée avec succès")
