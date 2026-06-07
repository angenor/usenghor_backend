"""
Router Admin - Tags
===================

Endpoints CRUD pour la gestion des tags/étiquettes.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.exceptions import NotFoundException
from app.core.pagination import PaginationParams, paginate
from app.models.content import Tag
from app.schemas.common import IdResponse, MessageResponse
from app.schemas.content import (
    TagCreate,
    TagMerge,
    TagRead,
    TagTranslateRequest,
    TagTranslateResponse,
    TagUpdate,
)
from app.services.content_service import ContentService

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("", response_model=dict)
async def list_tags(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Recherche sur nom ou slug"),
    _: bool = Depends(PermissionChecker("news.view")),
) -> dict:
    """Liste les tags avec pagination et filtres."""
    service = ContentService(db)
    query = await service.get_tags(search=search)
    return await paginate(db, query, pagination, Tag, TagRead)


# Route STATIQUE déclarée avant la route dynamique /{tag_id}.
@router.post("/translate", response_model=TagTranslateResponse)
async def translate_tag_fields(
    data: TagTranslateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("news.view")),
) -> TagTranslateResponse:
    """Traduit les champs FR → EN/AR sans persistance (pré-remplissage du formulaire)."""
    return await ContentService(db).translate_tag_fields(data)


@router.get("/{tag_id}", response_model=TagRead)
async def get_tag(
    tag_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("news.view")),
) -> Tag:
    """Récupère un tag par son ID."""
    service = ContentService(db)
    tag = await service.get_tag_by_id(tag_id)
    if not tag:
        raise NotFoundException("Tag non trouvé")
    return tag


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("news.create")),
) -> IdResponse:
    """Crée un nouveau tag."""
    service = ContentService(db)
    tag = await service.create_tag(
        name=tag_data.name,
        slug=tag_data.slug,
        icon=tag_data.icon,
        description=tag_data.description,
        name_en=tag_data.name_en,
        name_ar=tag_data.name_ar,
        description_en=tag_data.description_en,
        description_ar=tag_data.description_ar,
    )
    return IdResponse(id=tag.id, message="Tag créé avec succès")


@router.put("/{tag_id}", response_model=TagRead)
async def update_tag(
    tag_id: str,
    tag_data: TagUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("news.edit")),
) -> Tag:
    """Met à jour un tag."""
    service = ContentService(db)
    update_dict = tag_data.model_dump(exclude_unset=True)
    return await service.update_tag(tag_id, **update_dict)


@router.delete("/{tag_id}", response_model=MessageResponse)
async def delete_tag(
    tag_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("news.delete")),
) -> MessageResponse:
    """Supprime un tag."""
    service = ContentService(db)
    await service.delete_tag(tag_id)
    return MessageResponse(message="Tag supprimé avec succès")


@router.post("/merge", response_model=TagRead)
async def merge_tags(
    merge_data: TagMerge,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("news.edit")),
) -> Tag:
    """Fusionne plusieurs tags vers un tag cible."""
    service = ContentService(db)
    return await service.merge_tags(merge_data.source_tag_ids, merge_data.target_tag_id)


@router.get("/{tag_id}/usage", response_model=dict)
async def get_tag_usage(
    tag_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("news.view")),
) -> dict:
    """Récupère les statistiques d'utilisation d'un tag."""
    service = ContentService(db)
    return await service.get_tag_usage(tag_id)
