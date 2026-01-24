"""
Models module - Modèles SQLAlchemy
"""

from app.models.base import (
    MediaType,
    PublicationStatus,
    Salutation,
    TimestampMixin,
    UUIDMixin,
)
from app.models.core import Country
from app.models.identity import (
    AuditLog,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
    UserToken,
)
from app.models.media import Album, AlbumMedia, Media
from app.models.organization import (
    Department,
    ProjectStatus,
    Service,
    ServiceAchievement,
    ServiceMediaLibrary,
    ServiceObjective,
    ServiceProject,
)
from app.models.content import (
    Event,
    EventMediaLibrary,
    EventPartner,
    EventRegistration,
    EventType,
    News,
    NewsHighlightStatus,
    NewsMedia,
    NewsTag,
    RegistrationStatus,
    Tag,
)
from app.models.campus import (
    Campus,
    CampusMediaLibrary,
    CampusPartner,
    CampusTeam,
)
from app.models.partner import Partner, PartnerType
from app.models.academic import (
    Program,
    ProgramCampus,
    ProgramCareerOpportunity,
    ProgramCourse,
    ProgramPartner,
    ProgramSemester,
    ProgramSkill,
    ProgramType,
)
from app.models.application import (
    Application,
    ApplicationCall,
    ApplicationDegree,
    ApplicationDocument,
    CallCoverage,
    CallEligibilityCriteria,
    CallRequiredDocument,
    CallSchedule,
    CallStatus,
    CallType,
    EmploymentStatus,
    ExperienceDuration,
    MaritalStatus,
    SubmittedApplicationStatus,
)

__all__ = [
    # Base
    "Salutation",
    "PublicationStatus",
    "MediaType",
    "TimestampMixin",
    "UUIDMixin",
    # Core
    "Country",
    # Identity
    "Permission",
    "Role",
    "RolePermission",
    "User",
    "UserRole",
    "UserToken",
    "AuditLog",
    # Media
    "Media",
    "Album",
    "AlbumMedia",
    # Organization
    "ProjectStatus",
    "Department",
    "Service",
    "ServiceObjective",
    "ServiceAchievement",
    "ServiceProject",
    "ServiceMediaLibrary",
    # Content
    "EventType",
    "NewsHighlightStatus",
    "RegistrationStatus",
    "Tag",
    "Event",
    "EventPartner",
    "EventRegistration",
    "EventMediaLibrary",
    "News",
    "NewsMedia",
    "NewsTag",
    # Campus
    "Campus",
    "CampusTeam",
    "CampusPartner",
    "CampusMediaLibrary",
    # Partner
    "PartnerType",
    "Partner",
    # Academic
    "ProgramType",
    "Program",
    "ProgramCampus",
    "ProgramPartner",
    "ProgramSemester",
    "ProgramCourse",
    "ProgramCareerOpportunity",
    "ProgramSkill",
    # Application
    "CallType",
    "CallStatus",
    "SubmittedApplicationStatus",
    "MaritalStatus",
    "EmploymentStatus",
    "ExperienceDuration",
    "ApplicationCall",
    "CallEligibilityCriteria",
    "CallCoverage",
    "CallRequiredDocument",
    "CallSchedule",
    "Application",
    "ApplicationDegree",
    "ApplicationDocument",
]
