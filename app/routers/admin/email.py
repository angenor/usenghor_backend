"""
Router Admin - Email
====================

Endpoint d'administration pour tester l'envoi d'email.
"""

import logging

from fastapi import APIRouter, Depends

from app.core.dependencies import PermissionChecker
from app.schemas.email import EmailTestRequest, EmailTestResponse
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["Email"])


@router.post(
    "/test",
    response_model=EmailTestResponse,
    dependencies=[Depends(PermissionChecker("dashboard.view"))],
)
async def send_test_email(
    payload: EmailTestRequest,
) -> EmailTestResponse:
    """
    Envoie un email de test pour vérifier la configuration SMTP.

    Nécessite la permission dashboard.view (administrateur).
    """
    success = await EmailService.send_email(
        to=str(payload.to),
        subject=payload.subject,
        template_name="test",
        context={"message": payload.message, "subject": payload.subject},
    )

    if success:
        return EmailTestResponse(
            success=True,
            message=f"Email envoyé avec succès à {payload.to}",
        )

    return EmailTestResponse(
        success=False,
        message="Erreur lors de l'envoi de l'email. Vérifiez les logs du backend.",
    )
