"""
Modèles Newsletter
==================

Gestion des abonnés, campagnes et envois de newsletter.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class CampaignStatus(str, enum.Enum):
    """Statut d'une campagne."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"


class SendStatus(str, enum.Enum):
    """Statut d'un envoi individuel."""

    SENT = "sent"
    OPENED = "opened"
    CLICKED = "clicked"
    ERROR = "error"


class NewsletterSubscriber(Base, UUIDMixin):
    """Abonné à la newsletter."""

    __tablename__ = "newsletter_subscribers"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100))
    first_name: Mapped[str | None] = mapped_column(String(100))
    user_external_id: Mapped[str | None] = mapped_column(String(36))
    active: Mapped[bool] = mapped_column(default=True)
    unsubscribe_token: Mapped[str | None] = mapped_column(String(255), unique=True)
    source: Mapped[str | None] = mapped_column(String(100))
    subscribed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relations
    sends: Mapped[list["NewsletterSend"]] = relationship(
        back_populates="subscriber",
        cascade="all, delete-orphan",
    )


class NewsletterCampaign(Base, UUIDMixin, TimestampMixin):
    """Campagne de newsletter."""

    __tablename__ = "newsletter_campaigns"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    html_content: Mapped[str | None] = mapped_column(Text)
    text_content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CampaignStatus] = mapped_column(
        default=CampaignStatus.DRAFT,
        nullable=False,
    )
    scheduled_send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recipient_count: Mapped[int] = mapped_column(Integer, default=0)
    open_count: Mapped[int] = mapped_column(Integer, default=0)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by_external_id: Mapped[str | None] = mapped_column(String(36))

    # Relations
    sends: Mapped[list["NewsletterSend"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
    )


class NewsletterSend(Base, UUIDMixin):
    """Envoi individuel d'une campagne à un abonné."""

    __tablename__ = "newsletter_sends"

    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("newsletter_campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscriber_id: Mapped[str] = mapped_column(
        ForeignKey("newsletter_subscribers.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[SendStatus] = mapped_column(
        default=SendStatus.SENT,
        nullable=False,
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)

    # Relations
    campaign: Mapped["NewsletterCampaign"] = relationship(back_populates="sends")
    subscriber: Mapped["NewsletterSubscriber"] = relationship(back_populates="sends")
