"""
Modèles Organization
====================

Modèles SQLAlchemy pour la gestion de la structure organisationnelle.
"""

import enum

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class ProjectStatus(str, enum.Enum):
    """Statut d'un projet de service."""

    ONGOING = "ongoing"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    PLANNED = "planned"


class Department(Base, UUIDMixin, TimestampMixin):
    """Département / Direction de l'université."""

    __tablename__ = "departments"

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    mission: Mapped[str | None] = mapped_column(Text)

    # Références externes (pas de FK, car cross-service)
    icon_external_id: Mapped[str | None] = mapped_column(String(36))
    cover_image_external_id: Mapped[str | None] = mapped_column(String(36))
    head_external_id: Mapped[str | None] = mapped_column(String(36))

    display_order: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relations
    services: Mapped[list["Service"]] = relationship(
        "Service",
        back_populates="department",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Service(Base, UUIDMixin, TimestampMixin):
    """Service rattaché à un département."""

    __tablename__ = "services"

    department_id: Mapped[str | None] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    mission: Mapped[str | None] = mapped_column(Text)

    # Références externes
    head_external_id: Mapped[str | None] = mapped_column(String(36))
    album_external_id: Mapped[str | None] = mapped_column(String(36))

    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))

    display_order: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relations
    department: Mapped["Department"] = relationship(
        "Department", back_populates="services"
    )
    objectives: Mapped[list["ServiceObjective"]] = relationship(
        "ServiceObjective",
        back_populates="service",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    achievements: Mapped[list["ServiceAchievement"]] = relationship(
        "ServiceAchievement",
        back_populates="service",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    projects: Mapped[list["ServiceProject"]] = relationship(
        "ServiceProject",
        back_populates="service",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ServiceObjective(Base, UUIDMixin):
    """Objectif d'un service."""

    __tablename__ = "service_objectives"

    service_id: Mapped[str] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relation
    service: Mapped["Service"] = relationship(
        "Service", back_populates="objectives"
    )


class ServiceAchievement(Base, UUIDMixin, TimestampMixin):
    """Réalisation d'un service."""

    __tablename__ = "service_achievements"

    service_id: Mapped[str] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str | None] = mapped_column(String(100))
    cover_image_external_id: Mapped[str | None] = mapped_column(String(36))
    achievement_date: Mapped[str | None] = mapped_column(Date)

    # Relation
    service: Mapped["Service"] = relationship(
        "Service", back_populates="achievements"
    )


class ServiceProject(Base, UUIDMixin, TimestampMixin):
    """Projet interne d'un service."""

    __tablename__ = "service_projects"

    service_id: Mapped[str] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    cover_image_external_id: Mapped[str | None] = mapped_column(String(36))
    progress: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(
            ProjectStatus,
            name="project_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=ProjectStatus.PLANNED,
    )
    start_date: Mapped[str | None] = mapped_column(Date)
    expected_end_date: Mapped[str | None] = mapped_column(Date)

    # Relation
    service: Mapped["Service"] = relationship(
        "Service", back_populates="projects"
    )


class ServiceMediaLibrary(Base):
    """Table de liaison service-albums."""

    __tablename__ = "service_media_library"

    service_id: Mapped[str] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), primary_key=True
    )
    album_external_id: Mapped[str] = mapped_column(String(36), primary_key=True)
