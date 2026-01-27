"""
Modèle de base SQLAlchemy
=========================

Classes et mixins de base pour tous les modèles.
"""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Salutation(str, enum.Enum):
    """Civilité - alignée sur l'enum PostgreSQL ('Mr', 'Mrs', 'Dr', 'Pr')."""

    Mr = "Mr"
    Mrs = "Mrs"
    Dr = "Dr"
    Pr = "Pr"


class PublicationStatus(str, enum.Enum):
    """Statut de publication."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class MediaType(str, enum.Enum):
    """Type de média."""

    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"


class TimestampMixin:
    """Mixin pour les colonnes created_at et updated_at."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """Mixin pour les clés primaires UUID."""

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
