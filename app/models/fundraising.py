"""
Modèles Fundraising
===================

Modèles SQLAlchemy pour la gestion des levées de fonds.
"""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class FundraiserStatus(str, enum.Enum):
    """Statut d'une levée de fonds."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"


class ContributorCategory(str, enum.Enum):
    """Catégorie de contributeur."""

    STATE_ORGANIZATION = "state_organization"
    FOUNDATION_PHILANTHROPIST = "foundation_philanthropist"
    COMPANY = "company"


class Fundraiser(Base, UUIDMixin, TimestampMixin):
    """Levée de fonds."""

    __tablename__ = "fundraisers"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Contenu enrichi trilingue (HTML + Markdown)
    description_html: Mapped[str | None] = mapped_column(Text)
    description_md: Mapped[str | None] = mapped_column(Text)
    description_en_html: Mapped[str | None] = mapped_column(Text)
    description_en_md: Mapped[str | None] = mapped_column(Text)
    description_ar_html: Mapped[str | None] = mapped_column(Text)
    description_ar_md: Mapped[str | None] = mapped_column(Text)

    # Image de couverture (référence MEDIA)
    cover_image_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))

    # Objectif financier (EUR)
    goal_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Statut
    status: Mapped[FundraiserStatus] = mapped_column(
        Enum(
            FundraiserStatus,
            name="fundraiser_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=FundraiserStatus.DRAFT,
    )

    # Relations
    contributors: Mapped[list["FundraiserContributor"]] = relationship(
        "FundraiserContributor",
        back_populates="fundraiser",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    fundraiser_news: Mapped[list["FundraiserNews"]] = relationship(
        "FundraiserNews",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class FundraiserContributor(Base, UUIDMixin, TimestampMixin):
    """Contributeur d'une levée de fonds."""

    __tablename__ = "fundraiser_contributors"

    fundraiser_id: Mapped[str] = mapped_column(
        ForeignKey("fundraisers.id", ondelete="CASCADE"), nullable=False
    )

    # Nom trilingue
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255))
    name_ar: Mapped[str | None] = mapped_column(String(255))

    # Catégorie
    category: Mapped[ContributorCategory] = mapped_column(
        Enum(
            ContributorCategory,
            name="contributor_category",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )

    # Montant (EUR)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)

    # Logo (référence MEDIA, optionnel)
    logo_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))

    # Ordre d'affichage
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relation
    fundraiser: Mapped["Fundraiser"] = relationship(
        "Fundraiser", back_populates="contributors"
    )


class FundraiserNews(Base):
    """Table de liaison levée de fonds ↔ actualités (N:N)."""

    __tablename__ = "fundraiser_news"

    fundraiser_id: Mapped[str] = mapped_column(
        ForeignKey("fundraisers.id", ondelete="CASCADE"), primary_key=True
    )
    news_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
