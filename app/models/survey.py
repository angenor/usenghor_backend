"""
Modèle Survey
==============

Modèles SQLAlchemy pour les campagnes de sondage.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, VARCHAR
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import SurveyCampaignStatus, TimestampMixin, UUIDMixin


class SurveyCampaign(Base, UUIDMixin, TimestampMixin):
    """Campagne de sondage/formulaire."""

    __tablename__ = "survey_campaigns"

    slug: Mapped[str] = mapped_column(VARCHAR(100), unique=True, nullable=False, index=True)
    title_fr: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    title_en: Mapped[str | None] = mapped_column(VARCHAR(255))
    title_ar: Mapped[str | None] = mapped_column(VARCHAR(255))
    description_fr: Mapped[str | None] = mapped_column(Text)
    description_en: Mapped[str | None] = mapped_column(Text)
    description_ar: Mapped[str | None] = mapped_column(Text)
    survey_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[SurveyCampaignStatus] = mapped_column(
        Enum(
            SurveyCampaignStatus,
            name="survey_campaign_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False, default=SurveyCampaignStatus.DRAFT
    )
    confirmation_email_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmation_email_field: Mapped[str | None] = mapped_column(VARCHAR(100))
    closes_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )

    # Relations
    responses: Mapped[list["SurveyResponse"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    associations: Mapped[list["SurveyAssociation"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class SurveyResponse(Base, UUIDMixin):
    """Soumission individuelle d'un répondant."""

    __tablename__ = "survey_responses"

    campaign_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("survey_campaigns.id", ondelete="CASCADE"), nullable=False
    )
    response_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(INET)
    session_id: Mapped[str | None] = mapped_column(VARCHAR(64))
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    # Relations
    campaign: Mapped["SurveyCampaign"] = relationship(back_populates="responses")


class SurveyAssociation(Base, UUIDMixin):
    """Lien polymorphe entre une campagne et un élément du site."""

    __tablename__ = "survey_associations"

    campaign_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("survey_campaigns.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    # Relations
    campaign: Mapped["SurveyCampaign"] = relationship(back_populates="associations")
