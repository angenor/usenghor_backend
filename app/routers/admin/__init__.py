"""
Admin routers - Routes avec authentification
"""

from fastapi import APIRouter

from app.routers.admin import (
    albums,
    audit_logs,
    campus_team,
    campuses,
    career_opportunities,
    countries,
    departments,
    event_registrations,
    events,
    media,
    news,
    partners,
    permissions,
    programs,
    program_semesters,
    program_skills,
    roles,
    services,
    tags,
    users,
)

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Inclusion des sous-routers
router.include_router(users.router)
router.include_router(roles.router)
router.include_router(permissions.router)
router.include_router(audit_logs.router)
router.include_router(countries.router)
router.include_router(media.router)
router.include_router(albums.router)
router.include_router(departments.router)
router.include_router(services.router)
router.include_router(news.router)
router.include_router(events.router)
router.include_router(tags.router)
router.include_router(event_registrations.router)
router.include_router(campuses.router)
router.include_router(campus_team.router)
router.include_router(partners.router)
router.include_router(programs.router)
router.include_router(program_semesters.router)
router.include_router(program_skills.router)
router.include_router(career_opportunities.router)

__all__ = ["router"]
