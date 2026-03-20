"""
Service Survey
===============

Logique métier pour les campagnes de sondage.
"""

import csv
import io
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.base import SurveyCampaignStatus
from app.models.survey import SurveyAssociation, SurveyCampaign, SurveyResponse

logger = logging.getLogger(__name__)


class SurveyService:
    """Service pour la gestion des campagnes de sondage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # CAMPAIGNS - CRUD
    # =========================================================================

    async def get_campaigns(
        self,
        user_id: str,
        is_super_admin: bool = False,
        search: str | None = None,
        status: SurveyCampaignStatus | None = None,
    ):
        """Requête de base pour lister les campagnes (filtrée par créateur sauf super_admin)."""
        query = select(SurveyCampaign)

        if not is_super_admin:
            query = query.where(SurveyCampaign.created_by == user_id)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    SurveyCampaign.title_fr.ilike(search_filter),
                    SurveyCampaign.title_en.ilike(search_filter),
                    SurveyCampaign.slug.ilike(search_filter),
                )
            )

        if status:
            query = query.where(SurveyCampaign.status == status)

        return query

    async def get_campaign_by_id(
        self,
        campaign_id: str,
        user_id: str,
        is_super_admin: bool = False,
    ) -> SurveyCampaign:
        """Récupérer une campagne par ID (avec contrôle d'accès)."""
        query = select(SurveyCampaign).where(SurveyCampaign.id == campaign_id)

        if not is_super_admin:
            query = query.where(SurveyCampaign.created_by == user_id)

        result = await self.db.execute(query)
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise NotFoundException("Campagne non trouvée")

        return campaign

    async def get_campaign_by_slug(self, slug: str) -> SurveyCampaign:
        """Récupérer une campagne par slug (accès public)."""
        result = await self.db.execute(
            select(SurveyCampaign).where(SurveyCampaign.slug == slug)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise NotFoundException("Formulaire introuvable")

        return campaign

    async def create_campaign(self, data: dict, user_id: str) -> SurveyCampaign:
        """Créer une nouvelle campagne."""
        # Vérifier l'unicité du slug
        existing = await self.db.execute(
            select(SurveyCampaign).where(SurveyCampaign.slug == data["slug"])
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Ce slug est déjà utilisé")

        campaign = SurveyCampaign(
            **data,
            created_by=user_id,
            status=SurveyCampaignStatus.DRAFT,
        )
        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def update_campaign(
        self,
        campaign_id: str,
        user_id: str,
        is_super_admin: bool = False,
        **kwargs,
    ) -> SurveyCampaign:
        """Mettre à jour une campagne."""
        campaign = await self.get_campaign_by_id(campaign_id, user_id, is_super_admin)

        # Vérifier l'unicité du slug si modifié
        if "slug" in kwargs and kwargs["slug"] != campaign.slug:
            existing = await self.db.execute(
                select(SurveyCampaign).where(
                    SurveyCampaign.slug == kwargs["slug"],
                    SurveyCampaign.id != campaign_id,
                )
            )
            if existing.scalar_one_or_none():
                raise ConflictException("Ce slug est déjà utilisé")

        for key, value in kwargs.items():
            setattr(campaign, key, value)

        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def delete_campaign(
        self,
        campaign_id: str,
        user_id: str,
        is_super_admin: bool = False,
    ) -> None:
        """Supprimer une campagne et ses réponses (CASCADE)."""
        campaign = await self.get_campaign_by_id(campaign_id, user_id, is_super_admin)
        await self.db.delete(campaign)
        await self.db.commit()

    # =========================================================================
    # CAMPAIGNS - LIFECYCLE
    # =========================================================================

    async def publish_campaign(
        self, campaign_id: str, user_id: str, is_super_admin: bool = False
    ) -> SurveyCampaign:
        """Publier une campagne (draft/paused → active)."""
        campaign = await self.get_campaign_by_id(campaign_id, user_id, is_super_admin)

        if campaign.status not in (SurveyCampaignStatus.DRAFT, SurveyCampaignStatus.PAUSED):
            raise ValidationException("Seules les campagnes en brouillon ou en pause peuvent être publiées")

        campaign.status = SurveyCampaignStatus.ACTIVE
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def pause_campaign(
        self, campaign_id: str, user_id: str, is_super_admin: bool = False
    ) -> SurveyCampaign:
        """Mettre en pause une campagne (active → paused)."""
        campaign = await self.get_campaign_by_id(campaign_id, user_id, is_super_admin)

        if campaign.status != SurveyCampaignStatus.ACTIVE:
            raise ValidationException("Seules les campagnes actives peuvent être mises en pause")

        campaign.status = SurveyCampaignStatus.PAUSED
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def close_campaign(
        self, campaign_id: str, user_id: str, is_super_admin: bool = False
    ) -> SurveyCampaign:
        """Clôturer une campagne (active/paused → closed)."""
        campaign = await self.get_campaign_by_id(campaign_id, user_id, is_super_admin)

        if campaign.status not in (SurveyCampaignStatus.ACTIVE, SurveyCampaignStatus.PAUSED):
            raise ValidationException("Seules les campagnes actives ou en pause peuvent être clôturées")

        campaign.status = SurveyCampaignStatus.CLOSED
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def duplicate_campaign(
        self,
        campaign_id: str,
        new_slug: str,
        user_id: str,
        is_super_admin: bool = False,
    ) -> SurveyCampaign:
        """Dupliquer une campagne (structure uniquement, sans réponses)."""
        source = await self.get_campaign_by_id(campaign_id, user_id, is_super_admin)

        # Vérifier l'unicité du slug
        existing = await self.db.execute(
            select(SurveyCampaign).where(SurveyCampaign.slug == new_slug)
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Ce slug est déjà utilisé")

        new_campaign = SurveyCampaign(
            slug=new_slug,
            title_fr=f"{source.title_fr} (copie)",
            title_en=f"{source.title_en} (copy)" if source.title_en else None,
            title_ar=source.title_ar,
            description_fr=source.description_fr,
            description_en=source.description_en,
            description_ar=source.description_ar,
            survey_json=source.survey_json,
            confirmation_email_enabled=source.confirmation_email_enabled,
            closes_at=None,
            created_by=user_id,
            status=SurveyCampaignStatus.DRAFT,
        )
        self.db.add(new_campaign)
        await self.db.commit()
        await self.db.refresh(new_campaign)
        return new_campaign

    # =========================================================================
    # RESPONSES
    # =========================================================================

    async def check_rate_limit(self, ip_address: str, max_per_hour: int = 5) -> bool:
        """Vérifier le rate limiting par IP (retourne True si autorisé)."""
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

        result = await self.db.execute(
            select(func.count(SurveyResponse.id)).where(
                SurveyResponse.ip_address == ip_address,
                SurveyResponse.submitted_at >= one_hour_ago,
            )
        )
        count = result.scalar() or 0
        return count < max_per_hour

    async def submit_response(
        self,
        slug: str,
        response_data: dict,
        ip_address: str | None = None,
        session_id: str | None = None,
    ) -> SurveyResponse:
        """Enregistrer une réponse publique."""
        campaign = await self.get_campaign_by_slug(slug)

        # Auto-clôture si closes_at dépassé
        if campaign.closes_at and campaign.closes_at < datetime.now(timezone.utc):
            if campaign.status == SurveyCampaignStatus.ACTIVE:
                campaign.status = SurveyCampaignStatus.CLOSED
                await self.db.commit()

        if campaign.status != SurveyCampaignStatus.ACTIVE:
            raise ValidationException("Ce formulaire n'accepte plus de réponses")

        # Rate limiting
        if ip_address:
            if not await self.check_rate_limit(ip_address):
                raise ValidationException("Trop de soumissions. Veuillez réessayer plus tard.")

        # Dédoublonnage par session
        if session_id:
            existing = await self.db.execute(
                select(SurveyResponse).where(
                    SurveyResponse.campaign_id == campaign.id,
                    SurveyResponse.session_id == session_id,
                )
            )
            if existing.scalar_one_or_none():
                raise ConflictException("Vous avez déjà répondu à ce formulaire")

        response = SurveyResponse(
            campaign_id=campaign.id,
            response_data=response_data,
            ip_address=ip_address,
            session_id=session_id,
        )
        self.db.add(response)
        await self.db.commit()
        await self.db.refresh(response)

        # Email de confirmation si activé
        if campaign.confirmation_email_enabled:
            await self._send_confirmation_email(campaign, response_data)

        return response

    async def _send_confirmation_email(
        self, campaign: SurveyCampaign, response_data: dict
    ) -> None:
        """Envoyer un email de confirmation au répondant."""
        # Utiliser le champ configuré par l'admin
        if not campaign.confirmation_email_field:
            return

        email = response_data.get(campaign.confirmation_email_field)

        if not email or not isinstance(email, str) or "@" not in email:
            return

        try:
            from app.services.email_service import EmailService
            await EmailService.send_email(
                to=email,
                subject=f"Confirmation - {campaign.title_fr}",
                template_name="survey_confirmation",
                context={
                    "campaign_title": campaign.title_fr,
                    "submitted_at": datetime.now(timezone.utc).strftime("%d/%m/%Y à %H:%M"),
                    "site_url": "https://usenghor-francophonie.org",
                },
            )
        except Exception as e:
            logger.error(f"Erreur envoi email confirmation survey: {e}")

    async def get_responses(self, campaign_id: str):
        """Requête de base pour lister les réponses d'une campagne."""
        return select(SurveyResponse).where(SurveyResponse.campaign_id == campaign_id)

    async def get_stats(self, campaign_id: str) -> dict:
        """Calculer les statistiques agrégées d'une campagne."""
        campaign = await self.db.execute(
            select(SurveyCampaign).where(SurveyCampaign.id == campaign_id)
        )
        campaign_obj = campaign.scalar_one_or_none()
        if not campaign_obj:
            raise NotFoundException("Campagne non trouvée")

        # Récupérer toutes les réponses
        result = await self.db.execute(
            select(SurveyResponse).where(SurveyResponse.campaign_id == campaign_id)
        )
        responses = list(result.scalars().all())

        total = len(responses)
        first_at = min((r.submitted_at for r in responses), default=None)
        last_at = max((r.submitted_at for r in responses), default=None)

        # Analyser les questions du formulaire
        survey_def = campaign_obj.survey_json or {}
        elements = survey_def.get("elements", survey_def.get("pages", [{}]))

        # Aplatir les pages si nécessaire
        questions = []
        if isinstance(elements, list):
            for item in elements:
                if isinstance(item, dict) and "elements" in item:
                    questions.extend(item["elements"])
                elif isinstance(item, dict) and "type" in item:
                    questions.append(item)

        question_stats = []
        choice_types = {"radiogroup", "checkbox", "dropdown", "tagbox", "boolean"}
        rating_types = {"rating"}

        for q in questions:
            q_name = q.get("name", "")
            q_type = q.get("type", "")
            q_title = q.get("title", q_name)
            if isinstance(q_title, dict):
                q_title = q_title.get("fr", q_title.get("default", q_name))

            if q_type in choice_types:
                counter = Counter()
                for r in responses:
                    val = r.response_data.get(q_name)
                    if isinstance(val, list):
                        for v in val:
                            counter[str(v)] += 1
                    elif val is not None:
                        counter[str(val)] += 1

                question_stats.append({
                    "name": q_name,
                    "type": q_type,
                    "title": q_title,
                    "stats": {"distribution": dict(counter)},
                })

            elif q_type in rating_types:
                values = []
                for r in responses:
                    val = r.response_data.get(q_name)
                    if val is not None:
                        try:
                            values.append(float(val))
                        except (ValueError, TypeError):
                            pass

                avg = round(sum(values) / len(values), 2) if values else 0
                counter = Counter(str(int(v)) for v in values)
                question_stats.append({
                    "name": q_name,
                    "type": q_type,
                    "title": q_title,
                    "stats": {"average": avg, "distribution": dict(counter)},
                })

        return {
            "total_responses": total,
            "first_response_at": first_at,
            "last_response_at": last_at,
            "questions": question_stats,
        }

    async def export_csv(self, campaign_id: str) -> str:
        """Exporter les réponses au format CSV."""
        campaign = await self.db.execute(
            select(SurveyCampaign).where(SurveyCampaign.id == campaign_id)
        )
        campaign_obj = campaign.scalar_one_or_none()
        if not campaign_obj:
            raise NotFoundException("Campagne non trouvée")

        result = await self.db.execute(
            select(SurveyResponse)
            .where(SurveyResponse.campaign_id == campaign_id)
            .order_by(SurveyResponse.submitted_at.asc())
        )
        responses = list(result.scalars().all())

        # Collecter toutes les clés de réponse
        all_keys: list[str] = []
        seen_keys: set[str] = set()
        for r in responses:
            for key in r.response_data.keys():
                if key not in seen_keys:
                    all_keys.append(key)
                    seen_keys.add(key)

        output = io.StringIO()
        writer = csv.writer(output)

        # En-tête
        writer.writerow(["submitted_at"] + all_keys)

        # Données
        for r in responses:
            row = [r.submitted_at.isoformat()]
            for key in all_keys:
                val = r.response_data.get(key, "")
                if isinstance(val, list):
                    val = ", ".join(
                        v.get("name", str(v)) if isinstance(v, dict) else str(v)
                        for v in val
                    )
                elif isinstance(val, dict):
                    val = val.get("name", val.get("content", str(val)))
                row.append(str(val) if val is not None else "")
            writer.writerow(row)

        return output.getvalue()

    # =========================================================================
    # ASSOCIATIONS
    # =========================================================================

    async def get_associations(self, campaign_id: str) -> list[SurveyAssociation]:
        """Lister les associations d'une campagne."""
        result = await self.db.execute(
            select(SurveyAssociation).where(SurveyAssociation.campaign_id == campaign_id)
        )
        return list(result.scalars().all())

    async def create_association(
        self,
        campaign_id: str,
        entity_type: str,
        entity_id: str,
    ) -> SurveyAssociation:
        """Associer une campagne à un élément du site."""
        # Vérifier le doublon
        existing = await self.db.execute(
            select(SurveyAssociation).where(
                SurveyAssociation.campaign_id == campaign_id,
                SurveyAssociation.entity_type == entity_type,
                SurveyAssociation.entity_id == entity_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Cette association existe déjà")

        association = SurveyAssociation(
            campaign_id=campaign_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        self.db.add(association)
        await self.db.commit()
        await self.db.refresh(association)
        return association

    async def delete_association(self, association_id: str) -> None:
        """Retirer une association."""
        result = await self.db.execute(
            select(SurveyAssociation).where(SurveyAssociation.id == association_id)
        )
        association = result.scalar_one_or_none()
        if not association:
            raise NotFoundException("Association non trouvée")

        await self.db.delete(association)
        await self.db.commit()

    async def get_campaigns_by_entity(
        self, entity_type: str, entity_id: str
    ) -> list[SurveyCampaign]:
        """Récupérer les campagnes actives liées à un élément du site."""
        result = await self.db.execute(
            select(SurveyCampaign)
            .join(SurveyAssociation, SurveyAssociation.campaign_id == SurveyCampaign.id)
            .where(
                SurveyAssociation.entity_type == entity_type,
                SurveyAssociation.entity_id == entity_id,
                SurveyCampaign.status == SurveyCampaignStatus.ACTIVE,
            )
        )
        return list(result.scalars().all())

    async def get_campaign_response_count(self, campaign_id: str) -> int:
        """Compter les réponses d'une campagne."""
        result = await self.db.execute(
            select(func.count(SurveyResponse.id)).where(
                SurveyResponse.campaign_id == campaign_id
            )
        )
        return result.scalar() or 0

    async def get_campaign_last_response_at(self, campaign_id: str) -> datetime | None:
        """Date de la dernière réponse d'une campagne."""
        result = await self.db.execute(
            select(func.max(SurveyResponse.submitted_at)).where(
                SurveyResponse.campaign_id == campaign_id
            )
        )
        return result.scalar()
