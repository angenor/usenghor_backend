"""
Modèles Content
===============

Modèles SQLAlchemy pour la gestion des actualités et événements.
"""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
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
from app.models.base import PublicationStatus, TimestampMixin, UUIDMixin


class EventType(str, enum.Enum):
    """Type d'événement."""

    CONFERENCE = "conference"
    WORKSHOP = "workshop"
    CEREMONY = "ceremony"
    SEMINAR = "seminar"
    SYMPOSIUM = "symposium"
    OTHER = "other"


class NewsHighlightStatus(str, enum.Enum):
    """Statut de mise en avant d'une actualité."""

    STANDARD = "standard"
    FEATURED = "featured"
    HEADLINE = "headline"


class RegistrationStatus(str, enum.Enum):
    """Statut d'inscription à un événement."""

    REGISTERED = "registered"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    ATTENDED = "attended"


class Tag(Base, UUIDMixin):
    """Tag/catégorie pour les actualités."""

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    # Relations
    news_items: Mapped[list["News"]] = relationship(
        "News", secondary="news_tags", back_populates="tags"
    )


class Event(Base, UUIDMixin, TimestampMixin):
    """Événement organisé par l'université."""

    __tablename__ = "events"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)

    # Références externes (pas de FK) - UUID pour correspondre au schéma SQL
    cover_image_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    country_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    campus_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    service_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    project_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    organizer_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    album_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))

    type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    type_other: Mapped[str | None] = mapped_column(String(100))

    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    venue: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(11, 8))

    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    video_conference_link: Mapped[str | None] = mapped_column(String(500))

    registration_required: Mapped[bool] = mapped_column(Boolean, default=False)
    registration_link: Mapped[str | None] = mapped_column(String(500))
    max_attendees: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="publication_status", create_type=False, values_callable=lambda x: [e.value for e in x]),
        default=PublicationStatus.DRAFT,
    )

    # Relations
    registrations: Mapped[list["EventRegistration"]] = relationship(
        "EventRegistration",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class EventPartner(Base):
    """Table de liaison événement-partenaires."""

    __tablename__ = "event_partners"

    event_id: Mapped[str] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    partner_external_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)


class EventRegistration(Base, UUIDMixin):
    """Inscription à un événement."""

    __tablename__ = "event_registrations"

    event_id: Mapped[str] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    user_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))

    # Pour les non-inscrits
    last_name: Mapped[str | None] = mapped_column(String(100))
    first_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    organization: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus, name="registration_status", create_type=False, values_callable=lambda x: [e.value for e in x]),
        default=RegistrationStatus.REGISTERED,
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    # Relation
    event: Mapped["Event"] = relationship("Event", back_populates="registrations")


class EventMediaLibrary(Base):
    """Table de liaison événement-albums."""

    __tablename__ = "event_media_library"

    event_id: Mapped[str] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    album_external_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)


class News(Base, UUIDMixin, TimestampMixin):
    """Actualité/article de news."""

    __tablename__ = "news"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    video_url: Mapped[str | None] = mapped_column(String(500))

    # Références externes (pas de FK) - UUID pour correspondre au schéma SQL
    cover_image_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    campus_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    sector_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    service_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    event_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    project_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    call_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    program_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    author_external_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))

    highlight_status: Mapped[NewsHighlightStatus] = mapped_column(
        Enum(NewsHighlightStatus, name="news_highlight_status", create_type=False, values_callable=lambda x: [e.value for e in x]),
        default=NewsHighlightStatus.STANDARD,
    )
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="publication_status", create_type=False, values_callable=lambda x: [e.value for e in x]),
        default=PublicationStatus.DRAFT,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    visible_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relations
    tags: Mapped[list["Tag"]] = relationship(
        "Tag", secondary="news_tags", back_populates="news_items"
    )


class NewsMedia(Base):
    """Table de liaison actualité-médias."""

    __tablename__ = "news_media"

    news_id: Mapped[str] = mapped_column(
        ForeignKey("news.id", ondelete="CASCADE"), primary_key=True
    )
    media_external_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)


class NewsTag(Base):
    """Table de liaison actualités-tags."""

    __tablename__ = "news_tags"

    news_id: Mapped[str] = mapped_column(
        ForeignKey("news.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[str] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
