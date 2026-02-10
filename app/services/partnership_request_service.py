"""
Service PartnershipRequest
===========================

Logique métier pour les demandes de partenariat.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.partner import Partner, PartnerType
from app.models.partnership_request import (
    PartnershipRequest,
    PartnershipRequestStatus,
    PartnershipRequestType,
)

# Mapping type demande → type partenaire
REQUEST_TYPE_TO_PARTNER_TYPE: dict[PartnershipRequestType, PartnerType] = {
    PartnershipRequestType.ACADEMIC: PartnerType.PROGRAM_PARTNER,
    PartnershipRequestType.INSTITUTIONAL: PartnerType.CHARTER_OPERATOR,
    PartnershipRequestType.BUSINESS: PartnerType.PROJECT_PARTNER,
    PartnershipRequestType.OTHER: PartnerType.OTHER,
}


class PartnershipRequestService:
    """Service pour la gestion des demandes de partenariat."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # PUBLIC
    # =========================================================================

    async def submit_request(
        self,
        contact_name: str,
        email: str,
        organization: str,
        request_type: PartnershipRequestType,
        message: str | None = None,
    ) -> PartnershipRequest:
        """Soumet une nouvelle demande de partenariat (route publique)."""
        request = PartnershipRequest(
            id=str(uuid4()),
            contact_name=contact_name,
            email=email.lower(),
            organization=organization,
            type=request_type,
            message=message,
            status=PartnershipRequestStatus.PENDING,
        )
        self.db.add(request)
        await self.db.flush()
        return request

    # =========================================================================
    # ADMIN - LECTURE
    # =========================================================================

    async def get_requests(
        self,
        search: str | None = None,
        status: PartnershipRequestStatus | None = None,
        request_type: PartnershipRequestType | None = None,
    ) -> select:
        """Construit une requête pour lister les demandes."""
        query = select(PartnershipRequest)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    PartnershipRequest.contact_name.ilike(search_filter),
                    PartnershipRequest.email.ilike(search_filter),
                    PartnershipRequest.organization.ilike(search_filter),
                )
            )

        if status:
            query = query.where(PartnershipRequest.status == status)

        if request_type:
            query = query.where(PartnershipRequest.type == request_type)

        query = query.order_by(PartnershipRequest.created_at.desc())
        return query

    async def get_request_by_id(self, request_id: str) -> PartnershipRequest | None:
        """Récupère une demande par son ID."""
        result = await self.db.execute(
            select(PartnershipRequest).where(PartnershipRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_stats(self) -> dict:
        """Récupère les statistiques des demandes."""
        total_result = await self.db.execute(
            select(func.count()).select_from(PartnershipRequest)
        )
        total = total_result.scalar() or 0

        pending_result = await self.db.execute(
            select(func.count())
            .select_from(PartnershipRequest)
            .where(PartnershipRequest.status == PartnershipRequestStatus.PENDING)
        )
        pending = pending_result.scalar() or 0

        approved_result = await self.db.execute(
            select(func.count())
            .select_from(PartnershipRequest)
            .where(PartnershipRequest.status == PartnershipRequestStatus.APPROVED)
        )
        approved = approved_result.scalar() or 0

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": total - pending - approved,
        }

    # =========================================================================
    # ADMIN - ACTIONS
    # =========================================================================

    async def approve_request(
        self,
        request_id: str,
        reviewer_id: str,
        partner_type_override: str | None = None,
        partner_name_override: str | None = None,
    ) -> tuple[PartnershipRequest, Partner]:
        """
        Approuve une demande et crée automatiquement un Partner.

        Returns:
            Tuple (demande mise à jour, partenaire créé).
        """
        request = await self.get_request_by_id(request_id)
        if not request:
            raise NotFoundException("Demande de partenariat non trouvée")

        if request.status != PartnershipRequestStatus.PENDING:
            raise ValidationException(
                f"Seules les demandes en attente peuvent être approuvées "
                f"(statut actuel: {request.status.value})"
            )

        # Déterminer le type de partenaire
        if partner_type_override:
            partner_type = PartnerType(partner_type_override)
        else:
            partner_type = REQUEST_TYPE_TO_PARTNER_TYPE.get(
                request.type, PartnerType.OTHER
            )

        # Créer le partenaire
        partner = Partner(
            id=str(uuid4()),
            name=partner_name_override or request.organization,
            type=partner_type,
            email=request.email,
            description=request.message,
            active=True,
            display_order=0,
        )
        self.db.add(partner)
        await self.db.flush()

        # Mettre à jour la demande
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(PartnershipRequest)
            .where(PartnershipRequest.id == request_id)
            .values(
                status=PartnershipRequestStatus.APPROVED,
                reviewed_by_external_id=reviewer_id,
                reviewed_at=now,
                partner_external_id=partner.id,
                updated_at=now,
            )
        )
        await self.db.flush()

        updated_request = await self.get_request_by_id(request_id)
        return updated_request, partner

    async def reject_request(
        self,
        request_id: str,
        reviewer_id: str,
        reason: str | None = None,
    ) -> PartnershipRequest:
        """Rejette une demande de partenariat."""
        request = await self.get_request_by_id(request_id)
        if not request:
            raise NotFoundException("Demande de partenariat non trouvée")

        if request.status != PartnershipRequestStatus.PENDING:
            raise ValidationException(
                f"Seules les demandes en attente peuvent être rejetées "
                f"(statut actuel: {request.status.value})"
            )

        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(PartnershipRequest)
            .where(PartnershipRequest.id == request_id)
            .values(
                status=PartnershipRequestStatus.REJECTED,
                rejection_reason=reason,
                reviewed_by_external_id=reviewer_id,
                reviewed_at=now,
                updated_at=now,
            )
        )
        await self.db.flush()
        return await self.get_request_by_id(request_id)

    async def delete_request(self, request_id: str) -> None:
        """Supprime une demande de partenariat."""
        request = await self.get_request_by_id(request_id)
        if not request:
            raise NotFoundException("Demande de partenariat non trouvée")

        await self.db.execute(
            sql_delete(PartnershipRequest).where(
                PartnershipRequest.id == request_id
            )
        )
        await self.db.flush()
