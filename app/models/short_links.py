"""
Modèles Short Links
====================

Modèles SQLAlchemy pour le réducteur de liens.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class ShortLink(Base, UUIDMixin, TimestampMixin):
    """Lien court avec redirection."""

    __tablename__ = "short_links"

    code: Mapped[str] = mapped_column(String(4), unique=True, nullable=False)
    target_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True, default=None
    )


class AllowedDomain(Base, UUIDMixin):
    """Domaine externe autorisé pour les liens courts."""

    __tablename__ = "allowed_domains"

    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
