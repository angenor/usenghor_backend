"""
Modèles Fundraising (Levées de fonds)
======================================

Campagnes, contributeurs, manifestations d'intérêt,
sections éditoriales et médiathèque.
"""

import enum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


# ── Enums ────────────────────────────────────────────────────────────

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


class InterestExpressionStatus(str, enum.Enum):
    """Statut de suivi d'une manifestation d'intérêt."""

    NEW = "new"
    CONTACTED = "contacted"


# ── Modèles ──────────────────────────────────────────────────────────

class Fundraiser(Base, UUIDMixin, TimestampMixin):
    """Campagne de levée de fonds."""

    __tablename__ = "fundraisers"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Contenu enrichi trilingue
    description_html: Mapped[str | None] = mapped_column(Text)
    description_md: Mapped[str | None] = mapped_column(Text)
    description_en_html: Mapped[str | None] = mapped_column(Text)
    description_en_md: Mapped[str | None] = mapped_column(Text)
    description_ar_html: Mapped[str | None] = mapped_column(Text)
    description_ar_md: Mapped[str | None] = mapped_column(Text)

    reason_html: Mapped[str | None] = mapped_column(Text)
    reason_md: Mapped[str | None] = mapped_column(Text)
    reason_en_html: Mapped[str | None] = mapped_column(Text)
    reason_en_md: Mapped[str | None] = mapped_column(Text)
    reason_ar_html: Mapped[str | None] = mapped_column(Text)
    reason_ar_md: Mapped[str | None] = mapped_column(Text)

    # Image de couverture
    cover_image_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))

    # Objectif financier
    goal_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)

    # Statut
    status: Mapped[str] = mapped_column(
        Enum(
            FundraiserStatus,
            name="fundraiser_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=FundraiserStatus.DRAFT.value,
        nullable=False,
    )

    # Relations
    contributors: Mapped[list["FundraiserContributor"]] = relationship(
        "FundraiserContributor",
        back_populates="fundraiser",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="FundraiserContributor.display_order",
    )
    news_associations: Mapped[list["FundraiserNews"]] = relationship(
        "FundraiserNews",
        back_populates="fundraiser",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="FundraiserNews.display_order",
    )
    interest_expressions: Mapped[list["FundraiserInterestExpression"]] = relationship(
        "FundraiserInterestExpression",
        back_populates="fundraiser",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    media_items: Mapped[list["FundraiserMedia"]] = relationship(
        "FundraiserMedia",
        back_populates="fundraiser",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="FundraiserMedia.display_order",
    )


class FundraiserContributor(Base, UUIDMixin, TimestampMixin):
    """Contributeur d'une campagne."""

    __tablename__ = "fundraiser_contributors"

    fundraiser_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("fundraisers.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255))
    name_ar: Mapped[str | None] = mapped_column(String(255))

    category: Mapped[str] = mapped_column(
        Enum(
            ContributorCategory,
            name="contributor_category",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    show_amount_publicly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    logo_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relations
    fundraiser: Mapped["Fundraiser"] = relationship(
        "Fundraiser",
        back_populates="contributors",
    )


class FundraiserNews(Base):
    """Table de liaison levée de fonds ↔ actualités (N:N)."""

    __tablename__ = "fundraiser_news"

    fundraiser_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("fundraisers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    news_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relations
    fundraiser: Mapped["Fundraiser"] = relationship(
        "Fundraiser",
        back_populates="news_associations",
    )


class FundraiserInterestExpression(Base, UUIDMixin, TimestampMixin):
    """Manifestation d'intérêt d'un visiteur."""

    __tablename__ = "fundraiser_interest_expressions"
    __table_args__ = (
        UniqueConstraint("email", "fundraiser_id", name="uq_interest_email_fundraiser"),
    )

    fundraiser_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("fundraisers.id", ondelete="CASCADE"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Enum(
            InterestExpressionStatus,
            name="interest_expression_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=InterestExpressionStatus.NEW.value,
        nullable=False,
    )

    # Relations
    fundraiser: Mapped["Fundraiser"] = relationship(
        "Fundraiser",
        back_populates="interest_expressions",
    )


class FundraiserEditorialSection(Base, UUIDMixin, TimestampMixin):
    """Section éditoriale de la page principale."""

    __tablename__ = "fundraiser_editorial_sections"

    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title_fr: Mapped[str] = mapped_column(String(255), nullable=False)
    title_en: Mapped[str | None] = mapped_column(String(255))
    title_ar: Mapped[str | None] = mapped_column(String(255))
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relations
    items: Mapped[list["FundraiserEditorialItem"]] = relationship(
        "FundraiserEditorialItem",
        back_populates="section",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="FundraiserEditorialItem.display_order",
    )


class FundraiserEditorialItem(Base, UUIDMixin, TimestampMixin):
    """Item structuré au sein d'une section éditoriale."""

    __tablename__ = "fundraiser_editorial_items"

    section_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("fundraiser_editorial_sections.id", ondelete="CASCADE"),
        nullable=False,
    )
    icon: Mapped[str] = mapped_column(String(100), nullable=False)
    title_fr: Mapped[str] = mapped_column(String(255), nullable=False)
    title_en: Mapped[str | None] = mapped_column(String(255))
    title_ar: Mapped[str | None] = mapped_column(String(255))
    description_fr: Mapped[str] = mapped_column(Text, nullable=False)
    description_en: Mapped[str | None] = mapped_column(Text)
    description_ar: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relations
    section: Mapped["FundraiserEditorialSection"] = relationship(
        "FundraiserEditorialSection",
        back_populates="items",
    )


class FundraiserMedia(Base, UUIDMixin):
    """Table de jonction campagne ↔ médias."""

    __tablename__ = "fundraiser_media"
    __table_args__ = (
        UniqueConstraint("fundraiser_id", "media_external_id", name="uq_fundraiser_media"),
    )

    fundraiser_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("fundraisers.id", ondelete="CASCADE"),
        nullable=False,
    )
    media_external_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    caption_fr: Mapped[str | None] = mapped_column(String(500))
    caption_en: Mapped[str | None] = mapped_column(String(500))
    caption_ar: Mapped[str | None] = mapped_column(String(500))
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relations
    fundraiser: Mapped["Fundraiser"] = relationship(
        "Fundraiser",
        back_populates="media_items",
    )
