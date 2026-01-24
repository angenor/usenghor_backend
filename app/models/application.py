"""
Modèles Application
===================

Modèles SQLAlchemy pour la gestion des appels à candidature et candidatures.
"""

import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import PublicationStatus, Salutation, TimestampMixin, UUIDMixin


class CallType(str, enum.Enum):
    """Type d'appel à candidature."""

    APPLICATION = "application"
    SCHOLARSHIP = "scholarship"
    PROJECT = "project"
    RECRUITMENT = "recruitment"
    TRAINING = "training"


class CallStatus(str, enum.Enum):
    """Statut d'un appel à candidature."""

    ONGOING = "ongoing"
    CLOSED = "closed"
    UPCOMING = "upcoming"


class SubmittedApplicationStatus(str, enum.Enum):
    """Statut d'une candidature soumise."""

    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"
    INCOMPLETE = "incomplete"


class MaritalStatus(str, enum.Enum):
    """Statut matrimonial."""

    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    OTHER = "other"


class EmploymentStatus(str, enum.Enum):
    """Statut professionnel."""

    STUDENT = "student"
    TEACHER = "teacher"
    CIVIL_SERVANT = "civil_servant"
    PRIVATE_EMPLOYEE = "private_employee"
    NGO_EMPLOYEE = "ngo_employee"
    UNEMPLOYED = "unemployed"
    OTHER = "other"


class ExperienceDuration(str, enum.Enum):
    """Durée d'expérience professionnelle."""

    LESS_THAN_1_YEAR = "less_than_1_year"
    BETWEEN_1_3_YEARS = "between_1_3_years"
    BETWEEN_3_5_YEARS = "between_3_5_years"
    BETWEEN_5_10_YEARS = "between_5_10_years"
    MORE_THAN_10_YEARS = "more_than_10_years"


class ApplicationCall(Base, UUIDMixin, TimestampMixin):
    """Appel à candidature."""

    __tablename__ = "application_calls"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Références externes (pas de FK)
    cover_image_external_id: Mapped[str | None] = mapped_column(String(36))
    program_external_id: Mapped[str | None] = mapped_column(String(36))
    campus_external_id: Mapped[str | None] = mapped_column(String(36))
    created_by_external_id: Mapped[str | None] = mapped_column(String(36))

    type: Mapped[CallType] = mapped_column(
        Enum(CallType, name="call_type", create_type=False), nullable=False
    )
    status: Mapped[CallStatus] = mapped_column(
        Enum(CallStatus, name="call_status", create_type=False),
        default=CallStatus.UPCOMING,
    )

    opening_date: Mapped[date | None] = mapped_column(Date)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    program_start_date: Mapped[date | None] = mapped_column(Date)
    program_end_date: Mapped[date | None] = mapped_column(Date)

    target_audience: Mapped[str | None] = mapped_column(Text)
    registration_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(10), default="EUR")

    external_form_url: Mapped[str | None] = mapped_column(String(500))
    use_internal_form: Mapped[bool] = mapped_column(Boolean, default=True)

    publication_status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="publication_status", create_type=False),
        default=PublicationStatus.DRAFT,
    )

    # Relations
    eligibility_criteria: Mapped[list["CallEligibilityCriteria"]] = relationship(
        "CallEligibilityCriteria",
        back_populates="call",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CallEligibilityCriteria.display_order",
    )
    coverage: Mapped[list["CallCoverage"]] = relationship(
        "CallCoverage",
        back_populates="call",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CallCoverage.display_order",
    )
    required_documents: Mapped[list["CallRequiredDocument"]] = relationship(
        "CallRequiredDocument",
        back_populates="call",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CallRequiredDocument.display_order",
    )
    schedule: Mapped[list["CallSchedule"]] = relationship(
        "CallSchedule",
        back_populates="call",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CallSchedule.display_order",
    )
    applications: Mapped[list["Application"]] = relationship(
        "Application",
        back_populates="call",
        lazy="selectin",
    )


class CallEligibilityCriteria(Base, UUIDMixin):
    """Critère d'éligibilité d'un appel."""

    __tablename__ = "call_eligibility_criteria"

    call_id: Mapped[str] = mapped_column(
        ForeignKey("application_calls.id", ondelete="CASCADE"), nullable=False
    )
    criterion: Mapped[str] = mapped_column(Text, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relations
    call: Mapped["ApplicationCall"] = relationship(
        "ApplicationCall", back_populates="eligibility_criteria"
    )


class CallCoverage(Base, UUIDMixin):
    """Prise en charge d'un appel."""

    __tablename__ = "call_coverage"

    call_id: Mapped[str] = mapped_column(
        ForeignKey("application_calls.id", ondelete="CASCADE"), nullable=False
    )
    item: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relations
    call: Mapped["ApplicationCall"] = relationship(
        "ApplicationCall", back_populates="coverage"
    )


class CallRequiredDocument(Base, UUIDMixin):
    """Document requis pour un appel."""

    __tablename__ = "call_required_documents"

    call_id: Mapped[str] = mapped_column(
        ForeignKey("application_calls.id", ondelete="CASCADE"), nullable=False
    )
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    accepted_formats: Mapped[str | None] = mapped_column(String(100))
    max_size_mb: Mapped[int | None] = mapped_column(Integer)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relations
    call: Mapped["ApplicationCall"] = relationship(
        "ApplicationCall", back_populates="required_documents"
    )


class CallSchedule(Base, UUIDMixin):
    """Étape du calendrier d'un appel."""

    __tablename__ = "call_schedule"

    call_id: Mapped[str] = mapped_column(
        ForeignKey("application_calls.id", ondelete="CASCADE"), nullable=False
    )
    step: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relations
    call: Mapped["ApplicationCall"] = relationship(
        "ApplicationCall", back_populates="schedule"
    )


class Application(Base, UUIDMixin, TimestampMixin):
    """Candidature soumise."""

    __tablename__ = "applications"

    reference_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    call_id: Mapped[str | None] = mapped_column(
        ForeignKey("application_calls.id", ondelete="SET NULL")
    )

    # Références externes (pas de FK)
    program_external_id: Mapped[str | None] = mapped_column(String(36))
    user_external_id: Mapped[str | None] = mapped_column(String(36))
    reviewer_external_id: Mapped[str | None] = mapped_column(String(36))

    # Informations personnelles
    salutation: Mapped[Salutation | None] = mapped_column(
        Enum(Salutation, name="salutation", create_type=False)
    )
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date)
    birth_city: Mapped[str | None] = mapped_column(String(100))

    # Références pays (externe)
    birth_country_external_id: Mapped[str | None] = mapped_column(String(36))
    nationality_external_id: Mapped[str | None] = mapped_column(String(36))
    country_external_id: Mapped[str | None] = mapped_column(String(36))
    employer_country_external_id: Mapped[str | None] = mapped_column(String(36))

    marital_status: Mapped[MaritalStatus | None] = mapped_column(
        Enum(MaritalStatus, name="marital_status", create_type=False)
    )
    employment_status: Mapped[EmploymentStatus | None] = mapped_column(
        Enum(EmploymentStatus, name="employment_status", create_type=False)
    )
    employment_status_other: Mapped[str | None] = mapped_column(String(255))

    # Coordonnées
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    phone: Mapped[str | None] = mapped_column(String(30))
    phone_whatsapp: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Informations professionnelles
    has_work_experience: Mapped[bool] = mapped_column(Boolean, default=False)
    current_job: Mapped[str | None] = mapped_column(String(255))
    job_title: Mapped[str | None] = mapped_column(String(255))
    employer_name: Mapped[str | None] = mapped_column(String(255))
    employer_address: Mapped[str | None] = mapped_column(Text)
    employer_city: Mapped[str | None] = mapped_column(String(100))
    employer_phone: Mapped[str | None] = mapped_column(String(30))
    employer_email: Mapped[str | None] = mapped_column(String(255))
    experience_duration: Mapped[ExperienceDuration | None] = mapped_column(
        Enum(ExperienceDuration, name="experience_duration", create_type=False)
    )

    # Formation académique
    highest_degree_level: Mapped[str | None] = mapped_column(String(100))
    highest_degree_title: Mapped[str | None] = mapped_column(String(255))
    degree_date: Mapped[date | None] = mapped_column(Date)
    degree_location: Mapped[str | None] = mapped_column(String(255))

    # Statut
    status: Mapped[SubmittedApplicationStatus] = mapped_column(
        Enum(SubmittedApplicationStatus, name="submitted_application_status", create_type=False),
        default=SubmittedApplicationStatus.SUBMITTED,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_notes: Mapped[str | None] = mapped_column(Text)
    review_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    # Relations
    call: Mapped["ApplicationCall | None"] = relationship(
        "ApplicationCall", back_populates="applications"
    )
    degrees: Mapped[list["ApplicationDegree"]] = relationship(
        "ApplicationDegree",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ApplicationDegree.display_order",
    )
    documents: Mapped[list["ApplicationDocument"]] = relationship(
        "ApplicationDocument",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ApplicationDegree(Base, UUIDMixin):
    """Diplôme d'un candidat."""

    __tablename__ = "application_degrees"

    application_id: Mapped[str] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int | None] = mapped_column(Integer)
    institution: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    country_external_id: Mapped[str | None] = mapped_column(String(36))
    specialization: Mapped[str | None] = mapped_column(String(255))
    honors: Mapped[str | None] = mapped_column(String(50))
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relations
    application: Mapped["Application"] = relationship(
        "Application", back_populates="degrees"
    )


class ApplicationDocument(Base, UUIDMixin, TimestampMixin):
    """Document soumis par un candidat."""

    __tablename__ = "application_documents"

    application_id: Mapped[str] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    required_document_id: Mapped[str | None] = mapped_column(
        ForeignKey("call_required_documents.id", ondelete="SET NULL")
    )
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    media_external_id: Mapped[str | None] = mapped_column(String(36))
    is_valid: Mapped[bool | None] = mapped_column(Boolean)
    validation_comment: Mapped[str | None] = mapped_column(Text)

    # Relations
    application: Mapped["Application"] = relationship(
        "Application", back_populates="documents"
    )
    required_document: Mapped["CallRequiredDocument | None"] = relationship(
        "CallRequiredDocument"
    )
