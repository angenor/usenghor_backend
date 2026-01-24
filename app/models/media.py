"""
Modèles Media
=============

Modèles SQLAlchemy pour la gestion des médias (images, vidéos, documents).
"""

from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import MediaType, PublicationStatus, TimestampMixin, UUIDMixin


class Media(Base, UUIDMixin, TimestampMixin):
    """Modèle pour les fichiers médias."""

    __tablename__ = "media"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[MediaType] = mapped_column(
        Enum(MediaType, name="media_type", create_type=False),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_external_url: Mapped[bool] = mapped_column(Boolean, default=False)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    alt_text: Mapped[str | None] = mapped_column(String(255))
    credits: Mapped[str | None] = mapped_column(String(255))

    # Relations
    albums: Mapped[list["Album"]] = relationship(
        "Album",
        secondary="album_media",
        back_populates="media_items",
    )

    __table_args__ = (
        Index("idx_media_type", "type"),
    )

    def __repr__(self) -> str:
        return f"<Media {self.name} ({self.type.value})>"


class Album(Base, UUIDMixin, TimestampMixin):
    """Modèle pour les albums (regroupement de médias)."""

    __tablename__ = "albums"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="publication_status", create_type=False),
        default=PublicationStatus.DRAFT,
    )

    # Relations
    media_items: Mapped[list["Media"]] = relationship(
        "Media",
        secondary="album_media",
        back_populates="albums",
    )

    def __repr__(self) -> str:
        return f"<Album {self.title}>"


class AlbumMedia(Base):
    """Table de liaison entre albums et médias."""

    __tablename__ = "album_media"

    album_id: Mapped[str] = mapped_column(
        ForeignKey("albums.id", ondelete="CASCADE"),
        primary_key=True,
    )
    media_id: Mapped[str] = mapped_column(
        ForeignKey("media.id", ondelete="CASCADE"),
        primary_key=True,
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)
