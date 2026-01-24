"""
Modèles Partner
===============

Modèles SQLAlchemy pour la gestion des partenaires.
"""

import enum

from sqlalchemy import Boolean, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class PartnerType(str, enum.Enum):
    """Type de partenaire."""

    CHARTER_OPERATOR = "charter_operator"
    CAMPUS_PARTNER = "campus_partner"
    PROGRAM_PARTNER = "program_partner"
    PROJECT_PARTNER = "project_partner"
    OTHER = "other"


class Partner(Base, UUIDMixin, TimestampMixin):
    """Partenaire de l'université."""

    __tablename__ = "partners"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Références externes (pas de FK, car cross-service)
    logo_external_id: Mapped[str | None] = mapped_column(String(36))
    country_external_id: Mapped[str | None] = mapped_column(String(36))

    website: Mapped[str | None] = mapped_column(String(500))
    type: Mapped[PartnerType] = mapped_column(
        Enum(PartnerType, name="partner_type", create_type=False),
        nullable=False,
    )
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
