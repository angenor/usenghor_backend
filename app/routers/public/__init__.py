"""
Public routers - Routes sans authentification
"""

from fastapi import APIRouter

from app.routers.public import (
    albums,
    application_calls,
    campuses,
    countries,
    editorial,
    events,
    institutional_projects,
    media,
    news,
    newsletter,
    partners,
    programs,
    sectors,
    services,
)

router = APIRouter(prefix="/api/public", tags=["Public"])

# Inclusion des sous-routers
router.include_router(albums.router)
router.include_router(campuses.router)
router.include_router(countries.router)
router.include_router(news.router)
router.include_router(events.router)
router.include_router(partners.router)
router.include_router(programs.router)
router.include_router(application_calls.router)
router.include_router(newsletter.router)
router.include_router(editorial.router)
router.include_router(institutional_projects.router)
router.include_router(media.router)
router.include_router(sectors.router)
router.include_router(services.router)

__all__ = ["router"]
