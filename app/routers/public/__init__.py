"""
Public routers - Routes sans authentification
"""

from fastapi import APIRouter

from app.routers.public import countries

router = APIRouter(prefix="/api/public", tags=["Public"])

# Inclusion des sous-routers
router.include_router(countries.router)

__all__ = ["router"]
