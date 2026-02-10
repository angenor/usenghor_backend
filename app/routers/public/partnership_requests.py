"""
Router Public - Demandes de partenariat
========================================

Endpoint public pour soumettre une demande de partenariat.
"""

from fastapi import APIRouter

from app.core.dependencies import DbSession
from app.schemas.partnership_request import (
    PartnershipRequestPublicResponse,
    PartnershipRequestSubmit,
)
from app.services.partnership_request_service import PartnershipRequestService

router = APIRouter(prefix="/partnership-requests", tags=["Partnership Requests"])


@router.post("", response_model=PartnershipRequestPublicResponse)
async def submit_partnership_request(
    data: PartnershipRequestSubmit,
    db: DbSession,
) -> PartnershipRequestPublicResponse:
    """
    Soumettre une demande de partenariat.

    Endpoint public accessible sans authentification.
    """
    service = PartnershipRequestService(db)
    request = await service.submit_request(
        contact_name=data.contact_name,
        email=data.email,
        organization=data.organization,
        request_type=data.type,
        message=data.message,
    )
    return PartnershipRequestPublicResponse(
        id=request.id,
        message="Votre demande de partenariat a été soumise avec succès",
    )
