"""
Routes admin Fundraising (Levées de fonds)
==========================================

CRUD campagnes, contributeurs, manifestations d'intérêt,
sections éditoriales, médiathèque et export CSV.
"""

import io

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.fundraising import (
    Fundraiser,
    FundraiserContributor,
    FundraiserEditorialItem,
    FundraiserEditorialSection,
    FundraiserInterestExpression,
    FundraiserMedia,
)
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.fundraising import (
    ContributorCreate,
    ContributorRead,
    ContributorUpdate,
    EditorialItemCreate,
    EditorialItemRead,
    EditorialItemUpdate,
    EditorialSectionRead,
    EditorialSectionUpdate,
    FundraiserCreate,
    FundraiserMediaCreate,
    FundraiserMediaRead,
    FundraiserMediaUpdate,
    FundraiserRead,
    FundraiserStatistics,
    FundraiserUpdate,
    InterestExpressionRead,
    InterestExpressionStatusUpdate,
)
from app.services.fundraising_service import FundraisingService

router = APIRouter(prefix="/fundraisers", tags=["Fundraisers"])


# ── Statistics (AVANT les routes dynamiques) ─────────────────────────

@router.get("/statistics", response_model=FundraiserStatistics)
async def get_statistics(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.view")),
) -> dict:
    """Statistiques du dashboard admin."""
    service = FundraisingService(db)
    return await service.get_statistics()


# ── Interest Expressions (routes statiques AVANT /{id}) ──────────────

@router.get("/interest-expressions", response_model=dict)
async def list_interest_expressions(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    fundraiser_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    _: bool = Depends(PermissionChecker("fundraisers.view")),
) -> dict:
    """Liste paginée des manifestations d'intérêt."""
    service = FundraisingService(db)
    query = await service.get_interest_expressions(
        fundraiser_id=fundraiser_id,
        status=status_filter,
        search=search,
    )

    result = await paginate(db, query, pagination, FundraiserInterestExpression)
    # Enrichir avec le titre de la campagne
    enriched_items = []
    for expr in result["items"]:
        fundraiser = await service.get_fundraiser_by_id(expr.fundraiser_id)
        enriched_items.append(
            InterestExpressionRead(
                id=expr.id,
                fundraiser_id=expr.fundraiser_id,
                fundraiser_title=fundraiser.title if fundraiser else None,
                full_name=expr.full_name,
                email=expr.email,
                message=expr.message,
                status=expr.status,
                created_at=expr.created_at,
                updated_at=expr.updated_at,
            )
        )
    result["items"] = enriched_items
    return result


@router.put("/interest-expressions/{expression_id}/status", response_model=InterestExpressionRead)
async def update_interest_status(
    expression_id: str,
    data: InterestExpressionStatusUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.edit")),
) -> InterestExpressionRead:
    """Mettre à jour le statut d'une manifestation d'intérêt."""
    service = FundraisingService(db)
    expr = await service.update_interest_status(expression_id, data.status)
    fundraiser = await service.get_fundraiser_by_id(expr.fundraiser_id)
    return InterestExpressionRead(
        id=expr.id,
        fundraiser_id=expr.fundraiser_id,
        fundraiser_title=fundraiser.title if fundraiser else None,
        full_name=expr.full_name,
        email=expr.email,
        message=expr.message,
        status=expr.status,
        created_at=expr.created_at,
        updated_at=expr.updated_at,
    )


@router.get("/interest-expressions/export")
async def export_interest_expressions(
    db: DbSession,
    current_user: CurrentUser,
    fundraiser_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    _: bool = Depends(PermissionChecker("fundraisers.view")),
):
    """Export CSV des manifestations d'intérêt."""
    service = FundraisingService(db)
    csv_content = await service.export_interest_expressions_csv(
        fundraiser_id=fundraiser_id,
        status=status_filter,
    )
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=manifestations_interet.csv"},
    )


# ── Editorial Sections (routes statiques AVANT /{id}) ────────────────

@router.get("/editorial-sections", response_model=list[EditorialSectionRead])
async def list_editorial_sections(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.view")),
) -> list:
    """Liste des sections éditoriales avec items."""
    service = FundraisingService(db)
    return await service.get_all_sections_with_items()


@router.put("/editorial-sections/{section_id}", response_model=EditorialSectionRead)
async def update_editorial_section(
    section_id: str,
    data: EditorialSectionUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.edit")),
):
    """Modifier une section éditoriale."""
    service = FundraisingService(db)
    update_dict = data.model_dump(exclude_unset=True)
    return await service.update_section(section_id, **update_dict)


@router.post(
    "/editorial-sections/{section_id}/items",
    response_model=IdResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_editorial_item(
    section_id: str,
    data: EditorialItemCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.create")),
) -> IdResponse:
    """Ajouter un item à une section éditoriale."""
    service = FundraisingService(db)
    item = await service.create_item(section_id, **data.model_dump())
    return IdResponse(id=item.id, message="Item créé avec succès")


@router.put("/editorial-sections/items/{item_id}", response_model=EditorialItemRead)
async def update_editorial_item(
    item_id: str,
    data: EditorialItemUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.edit")),
):
    """Modifier un item éditorial."""
    service = FundraisingService(db)
    update_dict = data.model_dump(exclude_unset=True)
    return await service.update_item(item_id, **update_dict)


@router.delete("/editorial-sections/items/{item_id}", response_model=MessageResponse)
async def delete_editorial_item(
    item_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.delete")),
) -> MessageResponse:
    """Supprimer un item éditorial."""
    service = FundraisingService(db)
    await service.delete_item(item_id)
    return MessageResponse(message="Item supprimé avec succès")


# ── CRUD Fundraisers ─────────────────────────────────────────────────

@router.get("", response_model=dict)
async def list_fundraisers(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    _: bool = Depends(PermissionChecker("fundraisers.view")),
) -> dict:
    """Liste paginée des campagnes."""
    service = FundraisingService(db)
    query = await service.get_fundraisers(search=search, status=status_filter)
    return await paginate(db, query, pagination, Fundraiser, FundraiserRead)


@router.get("/{fundraiser_id}", response_model=FundraiserRead)
async def get_fundraiser(
    fundraiser_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.view")),
):
    """Détail d'une campagne."""
    service = FundraisingService(db)
    fundraiser = await service.get_fundraiser_by_id(fundraiser_id)
    if not fundraiser:
        raise NotFoundException("Campagne non trouvée")
    return fundraiser


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_fundraiser(
    data: FundraiserCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.create")),
) -> IdResponse:
    """Créer une campagne."""
    service = FundraisingService(db)
    fundraiser = await service.create_fundraiser(**data.model_dump())
    return IdResponse(id=fundraiser.id, message="Campagne créée avec succès")


@router.put("/{fundraiser_id}", response_model=FundraiserRead)
async def update_fundraiser(
    fundraiser_id: str,
    data: FundraiserUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.edit")),
):
    """Modifier une campagne."""
    service = FundraisingService(db)
    update_dict = data.model_dump(exclude_unset=True)
    return await service.update_fundraiser(fundraiser_id, **update_dict)


@router.delete("/{fundraiser_id}", response_model=MessageResponse)
async def delete_fundraiser(
    fundraiser_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.delete")),
) -> MessageResponse:
    """Supprimer une campagne."""
    service = FundraisingService(db)
    await service.delete_fundraiser(fundraiser_id)
    return MessageResponse(message="Campagne supprimée avec succès")


# ── Contributors ─────────────────────────────────────────────────────

@router.get("/{fundraiser_id}/contributors", response_model=list[ContributorRead])
async def list_contributors(
    fundraiser_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.view")),
) -> list:
    """Liste des contributeurs d'une campagne."""
    service = FundraisingService(db)
    return await service.get_contributors(fundraiser_id)


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
    _: bool = Depends(PermissionChecker("fundraisers.create")),
) -> IdResponse:
    """Ajouter un contributeur à une campagne."""
    service = FundraisingService(db)
    contributor = await service.add_contributor(fundraiser_id, **data.model_dump())
    return IdResponse(id=contributor.id, message="Contributeur ajouté avec succès")


@router.put("/{fundraiser_id}/contributors/{contributor_id}", response_model=ContributorRead)
async def update_contributor(
    fundraiser_id: str,
    contributor_id: str,
    data: ContributorUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.edit")),
):
    """Modifier un contributeur."""
    service = FundraisingService(db)
    update_dict = data.model_dump(exclude_unset=True)
    return await service.update_contributor(contributor_id, **update_dict)


@router.delete("/{fundraiser_id}/contributors/{contributor_id}", response_model=MessageResponse)
async def delete_contributor(
    fundraiser_id: str,
    contributor_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.delete")),
) -> MessageResponse:
    """Supprimer un contributeur."""
    service = FundraisingService(db)
    await service.delete_contributor(contributor_id)
    return MessageResponse(message="Contributeur supprimé avec succès")


# ── News Associations ────────────────────────────────────────────────

@router.get("/{fundraiser_id}/news", response_model=list)
async def list_fundraiser_news(
    fundraiser_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.view")),
) -> list:
    """Liste des actualités associées à une campagne."""
    service = FundraisingService(db)
    fundraiser = await service.get_fundraiser_by_id(fundraiser_id)
    if not fundraiser:
        raise NotFoundException("Campagne non trouvée")
    return await service.get_fundraiser_news(fundraiser_id)


@router.post("/{fundraiser_id}/news/{news_id}", response_model=MessageResponse)
async def associate_news(
    fundraiser_id: str,
    news_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.edit")),
) -> MessageResponse:
    """Associer une actualité à une campagne."""
    service = FundraisingService(db)
    await service.associate_news(fundraiser_id, news_id)
    return MessageResponse(message="Actualité associée avec succès")


@router.delete("/{fundraiser_id}/news/{news_id}", response_model=MessageResponse)
async def dissociate_news(
    fundraiser_id: str,
    news_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.edit")),
) -> MessageResponse:
    """Dissocier une actualité d'une campagne."""
    service = FundraisingService(db)
    await service.dissociate_news(fundraiser_id, news_id)
    return MessageResponse(message="Actualité dissociée avec succès")


# ── Media ────────────────────────────────────────────────────────────

@router.get("/{fundraiser_id}/media", response_model=list[FundraiserMediaRead])
async def list_media(
    fundraiser_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.view")),
) -> list:
    """Liste des médias d'une campagne."""
    service = FundraisingService(db)
    media_list = await service.list_media(fundraiser_id)
    return [
        FundraiserMediaRead(
            id=m.id,
            fundraiser_id=m.fundraiser_id,
            media_external_id=m.media_external_id,
            media_url=service._resolve_media_url(m.media_external_id),
            caption_fr=m.caption_fr,
            caption_en=m.caption_en,
            caption_ar=m.caption_ar,
            display_order=m.display_order,
            created_at=m.created_at,
        )
        for m in media_list
    ]


@router.post(
    "/{fundraiser_id}/media",
    response_model=IdResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_media(
    fundraiser_id: str,
    data: FundraiserMediaCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.create")),
) -> IdResponse:
    """Associer un média à une campagne."""
    service = FundraisingService(db)
    media = await service.add_media(fundraiser_id, **data.model_dump())
    return IdResponse(id=media.id, message="Média ajouté avec succès")


@router.put("/{fundraiser_id}/media/{media_id}", response_model=FundraiserMediaRead)
async def update_media(
    fundraiser_id: str,
    media_id: str,
    data: FundraiserMediaUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.edit")),
):
    """Modifier les légendes/ordre d'un média."""
    service = FundraisingService(db)
    update_dict = data.model_dump(exclude_unset=True)
    m = await service.update_media(media_id, **update_dict)
    return FundraiserMediaRead(
        id=m.id,
        fundraiser_id=m.fundraiser_id,
        media_external_id=m.media_external_id,
        media_url=service._resolve_media_url(m.media_external_id),
        caption_fr=m.caption_fr,
        caption_en=m.caption_en,
        caption_ar=m.caption_ar,
        display_order=m.display_order,
        created_at=m.created_at,
    )


@router.delete("/{fundraiser_id}/media/{media_id}", response_model=MessageResponse)
async def remove_media(
    fundraiser_id: str,
    media_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("fundraisers.delete")),
) -> MessageResponse:
    """Dissocier un média d'une campagne."""
    service = FundraisingService(db)
    await service.remove_media(media_id)
    return MessageResponse(message="Média supprimé avec succès")
