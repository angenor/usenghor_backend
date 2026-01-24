"""
Services module - Logique métier
"""

from app.services.campus_service import CampusService
from app.services.content_service import ContentService
from app.services.core_service import CoreService
from app.services.identity_service import IdentityService
from app.services.media_service import MediaService
from app.services.organization_service import OrganizationService
from app.services.partner_service import PartnerService
from app.services.academic_service import AcademicService

__all__ = [
    "AcademicService",
    "CampusService",
    "ContentService",
    "CoreService",
    "IdentityService",
    "MediaService",
    "OrganizationService",
    "PartnerService",
]
