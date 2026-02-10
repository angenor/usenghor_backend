"""
Schémas PartnershipRequest
===========================

Schémas Pydantic pour les demandes de partenariat.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.partnership_request import (
    PartnershipRequestStatus,
    PartnershipRequestType,
)


# =============================================================================
# PUBLIC (formulaire sans auth)
# =============================================================================


class PartnershipRequestSubmit(BaseModel):
    """Schéma pour soumettre une demande de partenariat (route publique)."""

    contact_name: str = Field(..., min_length=1, max_length=255, description="Nom du contact")
    email: EmailStr = Field(..., description="Email du contact")
    organization: str = Field(..., min_length=1, max_length=255, description="Nom de l'organisation")
    type: PartnershipRequestType = Field(..., description="Type de partenariat souhaité")
    message: str | None = Field(None, description="Message complémentaire")


class PartnershipRequestPublicResponse(BaseModel):
    """Réponse publique après soumission."""

    id: str
    message: str


# =============================================================================
# ADMIN
# =============================================================================


class PartnershipRequestRead(BaseModel):
    """Schéma pour la lecture admin d'une demande."""

    id: str
    contact_name: str
    email: str
    organization: str
    type: PartnershipRequestType
    message: str | None
    status: PartnershipRequestStatus
    rejection_reason: str | None
    reviewed_by_external_id: str | None
    reviewed_at: datetime | None
    partner_external_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PartnershipRequestApprove(BaseModel):
    """Schéma pour l'approbation avec mapping de type optionnel."""

    partner_type: str | None = Field(
        None,
        description="Type de partenaire à créer (si différent du mapping par défaut)",
    )
    partner_name: str | None = Field(
        None,
        description="Nom du partenaire (par défaut: organization de la demande)",
    )


class PartnershipRequestReject(BaseModel):
    """Schéma pour le rejet."""

    reason: str | None = Field(None, description="Motif du rejet")


class PartnershipRequestStats(BaseModel):
    """Statistiques des demandes."""

    total: int
    pending: int
    approved: int
    rejected: int
