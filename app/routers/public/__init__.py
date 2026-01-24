"""
Public routers - Routes sans authentification
"""

from fastapi import APIRouter

from app.routers.public import application_calls, countries, events, news, partners, programs

router = APIRouter(prefix="/api/public", tags=["Public"])

# Inclusion des sous-routers
router.include_router(countries.router)
router.include_router(news.router)
router.include_router(events.router)
router.include_router(partners.router)
router.include_router(programs.router)
router.include_router(application_calls.router)

__all__ = ["router"]
