"""
Modèles Project
===============

Gestion des projets institutionnels de l'université.
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
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import PublicationStatus, TimestampMixin, UUIDMixin
from app.models.organization import ProjectStatus


class ProjectCallType(str, enum.Enum):
    """Type d'appel lié à un projet."""

    APPLICATION = "application"
    SCHOLARSHIP = "scholarship"
    PROJECT = "project"
    RECRUITMENT = "recruitment"
    TRAINING = "training"


class ProjectCallStatus(str, enum.Enum):
    """Statut d'un appel lié à un projet."""

    ONGOING = "ongoing"
    CLOSED = "closed"
    UPCOMING = "upcoming"


class ProjectCategory(Base, UUIDMixin):
    """Catégorie de projets."""

    __tablename__ = "project_categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relations
    projects: Mapped[list["Project"]] = relationship(
        secondary="project_category_links",
        back_populates="categories",
    )


class Project(Base, UUIDMixin, TimestampMixin):
    """Projet institutionnel de l'université."""

    __tablename__ = "projects"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    # Références externes (sans FK)
    cover_image_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    department_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    manager_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    album_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))

    # Dates et budget
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    beneficiaries: Mapped[str | None] = mapped_column(Text)

    # Statuts
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(
            ProjectStatus,
            name="project_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=ProjectStatus.PLANNED,
        nullable=False,
    )
    publication_status: Mapped[PublicationStatus] = mapped_column(
        Enum(
            PublicationStatus,
            name="publication_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=PublicationStatus.DRAFT,
        nullable=False,
    )

    # Relations
    categories: Mapped[list["ProjectCategory"]] = relationship(
        secondary="project_category_links",
        back_populates="projects",
    )
    countries: Mapped[list["ProjectCountry"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    partners: Mapped[list["ProjectPartner"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    calls: Mapped[list["ProjectCall"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    media_library: Mapped[list["ProjectMediaLibrary"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ProjectCategoryLink(Base):
    """Association entre projets et catégories."""

    __tablename__ = "project_category_links"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    category_id: Mapped[str] = mapped_column(
        ForeignKey("project_categories.id", ondelete="CASCADE"),
        primary_key=True,
    )


class ProjectCountry(Base):
    """Pays concerné par un projet."""

    __tablename__ = "project_countries"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    country_external_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
    )

    # Relations
    project: Mapped["Project"] = relationship(back_populates="countries")


class ProjectPartner(Base):
    """Partenaire d'un projet."""

    __tablename__ = "project_partners"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    partner_external_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
    )
    partner_role: Mapped[str | None] = mapped_column(String(255))

    # Relations
    project: Mapped["Project"] = relationship(back_populates="partners")


class ProjectCall(Base, UUIDMixin, TimestampMixin):
    """Appel lié à un projet (bourse, recrutement, etc.)."""

    __tablename__ = "project_calls"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectCallStatus] = mapped_column(
        Enum(
            ProjectCallStatus,
            name="call_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=ProjectCallStatus.UPCOMING,
        nullable=False,
    )
    conditions: Mapped[str | None] = mapped_column(Text)
    type: Mapped[ProjectCallType | None] = mapped_column(
        Enum(
            ProjectCallType,
            name="call_type",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
    )
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relations
    project: Mapped["Project"] = relationship(back_populates="calls")


class ProjectMediaLibrary(Base):
    """Album de la médiathèque d'un projet."""

    __tablename__ = "project_media_library"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    album_external_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
    )

    # Relations
    project: Mapped["Project"] = relationship(back_populates="media_library")
