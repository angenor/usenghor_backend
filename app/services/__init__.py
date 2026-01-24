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
from app.services.application_service import ApplicationService
from app.services.newsletter_service import NewsletterService
from app.services.editorial_service import EditorialService
from app.services.project_service import ProjectService
from app.services.dashboard_service import DashboardService

__all__ = [
    "AcademicService",
    "ApplicationService",
    "CampusService",
    "ContentService",
    "CoreService",
    "DashboardService",
    "EditorialService",
    "IdentityService",
    "MediaService",
    "NewsletterService",
    "OrganizationService",
    "PartnerService",
    "ProjectService",
]
