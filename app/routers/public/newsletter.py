"""
Router Public - Newsletter
===========================

Endpoints publics pour l'inscription/désinscription à la newsletter
et le tracking des ouvertures/clics.
"""

from fastapi import APIRouter, Response
from fastapi.responses import RedirectResponse

from app.core.dependencies import DbSession
from app.schemas.common import MessageResponse
from app.schemas.newsletter import SubscribeRequest, SubscriberPublic, UnsubscribeRequest
from app.services.newsletter_service import NewsletterService

router = APIRouter(prefix="/newsletter", tags=["Newsletter"])


@router.post("/subscribe", response_model=SubscriberPublic)
async def subscribe(
    data: SubscribeRequest,
    db: DbSession,
) -> SubscriberPublic:
    """
    S'abonner à la newsletter.

    Crée un nouvel abonnement ou réactive un abonnement existant.
    """
    service = NewsletterService(db)
    subscriber = await service.subscribe(**data.model_dump(exclude_unset=True))
    return SubscriberPublic.model_validate(subscriber)


@router.post("/unsubscribe", response_model=MessageResponse)
async def unsubscribe(
    data: UnsubscribeRequest,
    db: DbSession,
) -> MessageResponse:
    """
    Se désabonner de la newsletter via le token.

    Le token est envoyé dans chaque email de la newsletter.
    """
    service = NewsletterService(db)
    await service.unsubscribe_by_token(data.token)
    return MessageResponse(message="Vous avez été désabonné avec succès")


@router.get("/unsubscribe/{token}", response_model=MessageResponse)
async def unsubscribe_via_link(
    token: str,
    db: DbSession,
) -> MessageResponse:
    """
    Se désabonner de la newsletter via un lien GET.

    Cette route permet le désabonnement via un simple clic dans l'email.
    """
    service = NewsletterService(db)
    await service.unsubscribe_by_token(token)
    return MessageResponse(message="Vous avez été désabonné avec succès")


@router.get("/track/open/{send_id}")
async def track_open(
    send_id: str,
    db: DbSession,
) -> Response:
    """
    Pixel de tracking pour l'ouverture d'un email.

    Retourne une image transparente 1x1 pixel.
    """
    service = NewsletterService(db)
    await service.track_open(send_id)

    # Image transparente 1x1 pixel (GIF)
    gif_1x1 = (
        b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
        b"\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00"
        b"\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
        b"\x44\x01\x00\x3b"
    )

    return Response(
        content=gif_1x1,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/track/click/{send_id}")
async def track_click(
    send_id: str,
    url: str,
    db: DbSession,
) -> RedirectResponse:
    """
    Tracking des clics dans un email.

    Enregistre le clic puis redirige vers l'URL cible.
    """
    service = NewsletterService(db)
    await service.track_click(send_id)

    return RedirectResponse(url=url, status_code=302)
