"""
Modèles Campus
==============

Modèles SQLAlchemy pour la gestion des campus.
"""

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Campus(Base, UUIDMixin, TimestampMixin):
    """Campus de l'université (siège et externalisés)."""

    __tablename__ = "campuses"

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Références externes (pas de FK, car cross-service)
    cover_image_external_id: Mapped[str | None] = mapped_column(String(36))
    country_external_id: Mapped[str | None] = mapped_column(String(36))
    head_external_id: Mapped[str | None] = mapped_column(String(36))
    album_external_id: Mapped[str | None] = mapped_column(String(36))

    # Coordonnées
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    city: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)
    postal_code: Mapped[str | None] = mapped_column(String(20))

    # Géolocalisation
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 8))
    longitude: Mapped[float | None] = mapped_column(Numeric(11, 8))

    is_headquarters: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relations
    team_members: Mapped[list["CampusTeam"]] = relationship(
        "CampusTeam",
        back_populates="campus",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CampusPartner(Base):
    """Table de liaison campus-partenaires."""

    __tablename__ = "campus_partners"

    campus_id: Mapped[str] = mapped_column(
        ForeignKey("campuses.id", ondelete="CASCADE"), primary_key=True
    )
    partner_external_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)


class CampusTeam(Base, UUIDMixin):
    """Membre de l'équipe d'un campus."""

    __tablename__ = "campus_team"

    campus_id: Mapped[str] = mapped_column(
        ForeignKey("campuses.id", ondelete="CASCADE"), nullable=False
    )
    user_external_id: Mapped[str] = mapped_column(String(36), nullable=False)
    position: Mapped[str] = mapped_column(String(255), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str | None] = mapped_column(
        String(50), server_default="now()"
    )

    # Relation
    campus: Mapped["Campus"] = relationship("Campus", back_populates="team_members")


class CampusMediaLibrary(Base):
    """Table de liaison campus-albums."""

    __tablename__ = "campus_media_library"

    campus_id: Mapped[str] = mapped_column(
        ForeignKey("campuses.id", ondelete="CASCADE"), primary_key=True
    )
    album_external_id: Mapped[str] = mapped_column(String(36), primary_key=True)
