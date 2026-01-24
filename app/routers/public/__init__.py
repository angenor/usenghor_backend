"""
Public routers - Routes sans authentification
"""

from fastapi import APIRouter

from app.routers.public import (
    application_calls,
    countries,
    editorial,
    events,
    institutional_projects,
    news,
    newsletter,
    partners,
    programs,
)

router = APIRouter(prefix="/api/public", tags=["Public"])

# Inclusion des sous-routers
router.include_router(countries.router)
router.include_router(news.router)
router.include_router(events.router)
router.include_router(partners.router)
router.include_router(programs.router)
router.include_router(application_calls.router)
router.include_router(newsletter.router)
router.include_router(editorial.router)
router.include_router(institutional_projects.router)

__all__ = ["router"]
