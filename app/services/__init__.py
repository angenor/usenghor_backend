"""
Services module - Logique métier
"""

from app.services.campus_service import CampusService
from app.services.content_service import ContentService
from app.services.core_service import CoreService
from app.services.identity_service import IdentityService
from app.services.media_service import MediaService
from app.services.organization_service import OrganizationService

__all__ = [
    "CampusService",
    "ContentService",
    "CoreService",
    "IdentityService",
    "MediaService",
    "OrganizationService",
]
