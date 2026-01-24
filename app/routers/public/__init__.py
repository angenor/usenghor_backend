"""
Public routers - Routes sans authentification
"""

from fastapi import APIRouter

from app.routers.public import countries, events, news

router = APIRouter(prefix="/api/public", tags=["Public"])

# Inclusion des sous-routers
router.include_router(countries.router)
router.include_router(news.router)
router.include_router(events.router)

__all__ = ["router"]
