"""
Admin routers - Routes avec authentification
"""

from fastapi import APIRouter

from app.routers.admin import albums, audit_logs, countries, media, permissions, roles, users

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Inclusion des sous-routers
router.include_router(users.router)
router.include_router(roles.router)
router.include_router(permissions.router)
router.include_router(audit_logs.router)
router.include_router(countries.router)
router.include_router(media.router)
router.include_router(albums.router)

__all__ = ["router"]
