"""
Routes publiques Fundraising (Levées de fonds)
===============================================

Liste, détail, statistiques globales, contributeurs agrégés,
sections éditoriales et manifestation d'intérêt.
"""

import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.dependencies import DbSession
from app.core.pagination import PaginationParams, paginate
from app.models.fundraising import Fundraiser
from app.schemas.fundraising import (
    AllContributorsItem,
    EditorialItemPublic,
    EditorialSectionPublic,
    FundraiserPublic,
    FundraiserPublicDetail,
    GlobalStats,
    InterestExpressionCreate,
)
from app.services.fundraising_service import FundraisingService

router = APIRouter(prefix="/fundraisers", tags=["Fundraisers"])


def _get_lang(request: Request) -> str:
    """Extrait la langue depuis le query param lang (prioritaire) ou Accept-Language."""
    lang = request.query_params.get("lang")
    if lang and lang in ("fr", "en", "ar"):
        return lang
    # Français par défaut (langue principale du site)
    return "fr"


# ── Routes statiques (AVANT /{slug}) ────────────────────────────────

@router.get("/global-stats", response_model=GlobalStats)
async def get_global_stats(db: DbSession) -> dict:
    """Statistiques agrégées pour la page principale."""
    service = FundraisingService(db)
    return await service.get_global_stats()


@router.get("/all-contributors", response_model=dict)
async def get_all_contributors(
    db: DbSession,
    pagination: PaginationParams = Depends(),
) -> dict:
    """Liste de tous les contributeurs uniques toutes campagnes."""
    service = FundraisingService(db)
    query = await service.get_all_contributors()

    # Pagination manuelle car c'est une requête agrégée
    from sqlalchemy import func, select
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    from math import ceil
    pages = ceil(total / pagination.limit) if pagination.limit > 0 else 0

    result = await db.execute(
        query.offset(pagination.offset).limit(pagination.limit)
    )
    rows = result.all()

    items = []
    for row in rows:
        show = bool(row.show_amount_publicly)
        items.append(
            AllContributorsItem(
                name=row.name,
                category=row.category,
                total_amount=float(row.total_amount) if show else None,
                show_amount_publicly=show,
                logo_url=f"/api/public/media/{row.logo_external_id}/download" if row.logo_external_id else None,
                campaigns_count=row.campaigns_count,
            )
        )

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit,
        "pages": pages,
    }


@router.get("/editorial-sections", response_model=dict)
async def get_editorial_sections(
    request: Request,
    db: DbSession,
) -> dict:
    """Sections éditoriales actives avec items dans la langue demandée."""
    service = FundraisingService(db)
    lang = _get_lang(request)

    sections = await service.get_active_sections_with_items()

    result = []
    for section in sections:
        title = getattr(section, f"title_{lang}", None) or section.title_fr
        items = []
        for item in section.items:
            item_title = getattr(item, f"title_{lang}", None) or item.title_fr
            item_desc = getattr(item, f"description_{lang}", None) or item.description_fr
            items.append(EditorialItemPublic(
                icon=item.icon,
                title=item_title,
                description=item_desc,
            ))
        result.append(EditorialSectionPublic(
            slug=section.slug,
            title=title,
            items=items,
        ))

    return {"sections": result}


# ── Liste paginée ───────────────────────────────────────────────────

@router.get("", response_model=dict)
async def list_fundraisers(
    db: DbSession,
    pagination: PaginationParams = Depends(),
    status_filter: str | None = Query(None, alias="status"),
) -> dict:
    """Liste des campagnes publiées (active + completed)."""
    service = FundraisingService(db)
    query = await service.get_published_fundraisers(status=status_filter)

    # Paginer et enrichir avec les totaux
    result = await paginate(db, query, pagination, Fundraiser)
    enriched = [service._enrich_fundraiser_public(f) for f in result["items"]]
    result["items"] = enriched
    return result


# ── Manifestation d'intérêt ─────────────────────────────────────────

@router.post("/{slug}/interest", status_code=status.HTTP_201_CREATED)
async def submit_interest(
    slug: str,
    data: InterestExpressionCreate,
    db: DbSession,
):
    """Manifester son intérêt pour contribuer à une campagne."""
    service = FundraisingService(db)

    # Validation anti-spam
    if data.honeypot:
        raise HTTPException(status_code=400, detail="Vérification de sécurité échouée.")

    # Vérifier le délai minimum (3 secondes)
    if data.form_opened_at > 0:
        elapsed = time.time() - data.form_opened_at
        if elapsed < 3:
            raise HTTPException(status_code=400, detail="Vérification de sécurité échouée.")

    # Vérifier le challenge token
    if not data.challenge_token:
        raise HTTPException(status_code=400, detail="Vérification de sécurité échouée.")

    # Vérifier que la campagne existe et est active
    fundraiser = await service.get_fundraiser_by_slug(slug)
    if not fundraiser or fundraiser.status != "active":
        raise HTTPException(status_code=404, detail="Campagne non trouvée ou clôturée.")

    # Créer ou mettre à jour la manifestation d'intérêt
    expression, is_new = await service.create_or_update_interest_expression(
        fundraiser_id=fundraiser.id,
        full_name=data.full_name,
        email=data.email,
        message=data.message,
    )

    # Envoyer les emails (confirmation + notification admin)
    try:
        from app.services.email_service import EmailService
        email_service = EmailService()

        # Email de confirmation au visiteur
        await email_service.send_template_email(
            to_email=data.email,
            subject=f"Confirmation - Intérêt pour {fundraiser.title}",
            template_name="interest_expression_confirmation",
            context={
                "full_name": data.full_name,
                "fundraiser_title": fundraiser.title,
                "message": data.message or "",
            },
        )

        # Email de notification admin
        from app.core.config import settings
        if hasattr(settings, "admin_email") and settings.admin_email:
            await email_service.send_template_email(
                to_email=settings.admin_email,
                subject=f"Nouvelle manifestation d'intérêt - {fundraiser.title}",
                template_name="interest_expression_notification",
                context={
                    "full_name": data.full_name,
                    "email": data.email,
                    "fundraiser_title": fundraiser.title,
                    "message": data.message or "",
                },
            )
    except Exception:
        pass  # Ne pas bloquer la soumission si l'email échoue

    if is_new:
        return {"message": "Votre intérêt a bien été enregistré. Un email de confirmation vous a été envoyé."}
    else:
        return {"message": "Votre intérêt a été mis à jour."}


# ── Détail par slug (APRÈS les routes statiques) ────────────────────

@router.get("/{slug}", response_model=FundraiserPublicDetail)
async def get_fundraiser_by_slug(
    slug: str,
    db: DbSession,
) -> dict:
    """Détail complet d'une campagne."""
    service = FundraisingService(db)
    fundraiser = await service.get_fundraiser_by_slug(slug)

    if not fundraiser or fundraiser.status not in ("active", "completed"):
        raise HTTPException(status_code=404, detail="Campagne non trouvée")

    detail = service._enrich_fundraiser_public_detail(fundraiser)

    # Ajouter les news associées
    detail["news"] = await service.get_fundraiser_news(fundraiser.id)

    return detail
