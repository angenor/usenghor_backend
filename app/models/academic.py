"""
Modèles Academic
================

Modèles SQLAlchemy pour la gestion des programmes et formations.
"""

import enum
from decimal import Decimal

from sqlalchemy import (
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import PublicationStatus, TimestampMixin, UUIDMixin


class ProgramType(str, enum.Enum):
    """Type de programme."""

    MASTER = "master"
    DOCTORATE = "doctorate"
    UNIVERSITY_DIPLOMA = "university_diploma"
    CERTIFICATE = "certificate"


class Program(Base, UUIDMixin, TimestampMixin):
    """Programme de formation."""

    __tablename__ = "programs"

    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    teaching_methods: Mapped[str | None] = mapped_column(Text)

    # Références externes (pas de FK)
    cover_image_external_id: Mapped[str | None] = mapped_column(String(36))
    department_external_id: Mapped[str | None] = mapped_column(String(36))
    coordinator_external_id: Mapped[str | None] = mapped_column(String(36))

    type: Mapped[ProgramType] = mapped_column(
        Enum(ProgramType, name="program_type", create_type=False), nullable=False
    )
    duration_months: Mapped[int | None] = mapped_column(Integer)
    credits: Mapped[int | None] = mapped_column(Integer)
    degree_awarded: Mapped[str | None] = mapped_column(String(255))
    required_degree: Mapped[str | None] = mapped_column(Text)

    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="publication_status", create_type=False),
        default=PublicationStatus.DRAFT,
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relations
    semesters: Mapped[list["ProgramSemester"]] = relationship(
        "ProgramSemester",
        back_populates="program",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProgramSemester.display_order",
    )
    skills: Mapped[list["ProgramSkill"]] = relationship(
        "ProgramSkill",
        back_populates="program",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProgramSkill.display_order",
    )
    career_opportunities: Mapped[list["ProgramCareerOpportunity"]] = relationship(
        "ProgramCareerOpportunity",
        back_populates="program",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProgramCareerOpportunity.display_order",
    )


class ProgramCampus(Base):
    """Table de liaison programme-campus."""

    __tablename__ = "program_campuses"

    program_id: Mapped[str] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), primary_key=True
    )
    campus_external_id: Mapped[str] = mapped_column(String(36), primary_key=True)


class ProgramPartner(Base):
    """Table de liaison programme-partenaires."""

    __tablename__ = "program_partners"

    program_id: Mapped[str] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), primary_key=True
    )
    partner_external_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    partnership_type: Mapped[str | None] = mapped_column(String(100))


class ProgramSemester(Base, UUIDMixin):
    """Semestre d'un programme."""

    __tablename__ = "program_semesters"

    program_id: Mapped[str] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    credits: Mapped[int] = mapped_column(Integer, default=1)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relations
    program: Mapped["Program"] = relationship("Program", back_populates="semesters")
    courses: Mapped[list["ProgramCourse"]] = relationship(
        "ProgramCourse",
        back_populates="semester",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProgramCourse.display_order",
    )


class ProgramCourse(Base, UUIDMixin):
    """Unité d'enseignement (cours) d'un semestre."""

    __tablename__ = "program_courses"

    semester_id: Mapped[str] = mapped_column(
        ForeignKey("program_semesters.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str | None] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    credits: Mapped[int | None] = mapped_column(Integer)
    lecture_hours: Mapped[int] = mapped_column(Integer, default=0)
    tutorial_hours: Mapped[int] = mapped_column(Integer, default=0)
    practical_hours: Mapped[int] = mapped_column(Integer, default=0)
    coefficient: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relations
    semester: Mapped["ProgramSemester"] = relationship(
        "ProgramSemester", back_populates="courses"
    )


class ProgramCareerOpportunity(Base, UUIDMixin):
    """Débouché professionnel d'un programme."""

    __tablename__ = "program_career_opportunities"

    program_id: Mapped[str] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relations
    program: Mapped["Program"] = relationship(
        "Program", back_populates="career_opportunities"
    )


class ProgramSkill(Base, UUIDMixin):
    """Compétence visée par un programme."""

    __tablename__ = "program_skills"

    program_id: Mapped[str] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relations
    program: Mapped["Program"] = relationship("Program", back_populates="skills")
