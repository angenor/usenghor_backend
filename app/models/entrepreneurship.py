"""
Modèles Entrepreneuriat (PEI)
=============================

Modèles SQLAlchemy du Pôle Entrepreneuriat et Innovation :
dispositifs du parcours, cohortes (FSE / SEE) et boîte à outils.

Schéma de référence : documentation/modele_de_données/services/16_entrepreneurship.sql
Convention trilingue additive : ``champ`` (FR), ``champ_en``, ``champ_ar`` ;
rich text ``champ_html`` / ``champ_md`` + ``champ_en_html`` / ``champ_ar_md``…
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class PeiProgramPhase(str, enum.Enum):
    """Phase du parcours entrepreneurial (ENUM ``pei_program_phase``)."""

    AWARENESS = "awareness"
    STATUS = "status"
    PRE_INCUBATION = "pre_incubation"
    INCUBATION = "incubation"
    FUNDING = "funding"
    ECOSYSTEM = "ecosystem"


class PeiCohortType(str, enum.Enum):
    """Type de cohorte (ENUM ``pei_cohort_type``)."""

    FSE = "fse"
    SEE = "see"


class PeiResourceType(str, enum.Enum):
    """Type de ressource de la boîte à outils (ENUM ``pei_resource_type``)."""

    DOCUMENT = "document"
    LINK = "link"
    VIDEO = "video"


def _enum_values(enum_cls):
    return [e.value for e in enum_cls]


def _audit_user_fk() -> Mapped[str | None]:
    return mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
    )


class PeiProgram(Base, UUIDMixin, TimestampMixin):
    """Dispositif du parcours entrepreneurial (OSER, SEE, MTI, Senghor'Innov, FSE)."""

    __tablename__ = "pei_programs"

    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    sigle: Mapped[str | None] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    title_en: Mapped[str | None] = mapped_column(String(200))
    title_ar: Mapped[str | None] = mapped_column(String(200))
    phase: Mapped[PeiProgramPhase] = mapped_column(
        Enum(
            PeiProgramPhase,
            name="pei_program_phase",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    tagline: Mapped[str | None] = mapped_column(Text)
    tagline_en: Mapped[str | None] = mapped_column(Text)
    tagline_ar: Mapped[str | None] = mapped_column(Text)
    content_html: Mapped[str | None] = mapped_column(Text)
    content_md: Mapped[str | None] = mapped_column(Text)
    content_en_html: Mapped[str | None] = mapped_column(Text)
    content_en_md: Mapped[str | None] = mapped_column(Text)
    content_ar_html: Mapped[str | None] = mapped_column(Text)
    content_ar_md: Mapped[str | None] = mapped_column(Text)
    highlight: Mapped[str | None] = mapped_column(String(120))
    highlight_en: Mapped[str | None] = mapped_column(String(120))
    highlight_ar: Mapped[str | None] = mapped_column(String(120))
    color: Mapped[str] = mapped_column(
        String(20), nullable=False, default="blue", server_default="blue"
    )
    # Référence inter-service vers media.id (sans FK)
    cover_image_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str | None] = _audit_user_fk()
    updated_by: Mapped[str | None] = _audit_user_fk()

    __table_args__ = (
        CheckConstraint("code ~ '^[a-z0-9][a-z0-9-]*$'", name="chk_pei_programs_code"),
        CheckConstraint("LENGTH(title) >= 3", name="chk_pei_programs_title"),
        CheckConstraint(
            "color IN ('blue', 'blue_dark', 'red', 'amber', 'teal')",
            name="chk_pei_programs_color",
        ),
    )


class PeiCohort(Base, UUIDMixin, TimestampMixin):
    """Cohorte FSE / SEE (les lauréats arrivent en feature 022)."""

    __tablename__ = "pei_cohorts"

    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    label_en: Mapped[str | None] = mapped_column(String(200))
    label_ar: Mapped[str | None] = mapped_column(String(200))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[PeiCohortType] = mapped_column(
        Enum(
            PeiCohortType,
            name="pei_cohort_type",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    focus: Mapped[str | None] = mapped_column(Text)
    focus_en: Mapped[str | None] = mapped_column(Text)
    focus_ar: Mapped[str | None] = mapped_column(Text)
    summary_html: Mapped[str | None] = mapped_column(Text)
    summary_md: Mapped[str | None] = mapped_column(Text)
    summary_en_html: Mapped[str | None] = mapped_column(Text)
    summary_en_md: Mapped[str | None] = mapped_column(Text)
    summary_ar_html: Mapped[str | None] = mapped_column(Text)
    summary_ar_md: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str | None] = _audit_user_fk()
    updated_by: Mapped[str | None] = _audit_user_fk()

    __table_args__ = (
        CheckConstraint("code ~ '^[a-z0-9][a-z0-9-]*$'", name="chk_pei_cohorts_code"),
        CheckConstraint("year BETWEEN 2000 AND 2100", name="chk_pei_cohorts_year"),
    )


class PeiResource(Base, UUIDMixin, TimestampMixin):
    """Ressource de la boîte à outils : document de la médiathèque, lien ou vidéo."""

    __tablename__ = "pei_resources"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    title_en: Mapped[str | None] = mapped_column(String(200))
    title_ar: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    description_en: Mapped[str | None] = mapped_column(Text)
    description_ar: Mapped[str | None] = mapped_column(Text)
    type: Mapped[PeiResourceType] = mapped_column(
        Enum(
            PeiResourceType,
            name="pei_resource_type",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    # Référence inter-service vers media.id (sans FK), type = document
    media_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    # Adresse externe, type = link | video
    url: Mapped[str | None] = mapped_column(String(500))
    category: Mapped[str | None] = mapped_column(String(120))
    category_en: Mapped[str | None] = mapped_column(String(120))
    category_ar: Mapped[str | None] = mapped_column(String(120))
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = _audit_user_fk()
    updated_by: Mapped[str | None] = _audit_user_fk()

    __table_args__ = (
        CheckConstraint(
            "(type = 'document' AND media_external_id IS NOT NULL) "
            "OR (type IN ('link', 'video') AND url IS NOT NULL AND LENGTH(url) > 0)",
            name="chk_pei_resources_source",
        ),
    )
