"""
Modèles Editorial
=================

Gestion des contenus éditoriaux de configuration et leur historique.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class EditorialValueType(str, enum.Enum):
    """Type de valeur d'un contenu éditorial."""

    TEXT = "text"
    NUMBER = "number"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"


class EditorialCategory(Base, UUIDMixin):
    """Catégorie de contenus éditoriaux."""

    __tablename__ = "editorial_categories"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relations
    contents: Mapped[list["EditorialContent"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )


class EditorialContent(Base, UUIDMixin):
    """Contenu éditorial de configuration."""

    __tablename__ = "editorial_contents"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text)
    value_type: Mapped[EditorialValueType] = mapped_column(
        default=EditorialValueType.TEXT,
        nullable=False,
    )
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("editorial_categories.id", ondelete="SET NULL"),
    )
    year: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    admin_editable: Mapped[bool] = mapped_column(default=True)
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

    # Relations
    category: Mapped["EditorialCategory | None"] = relationship(
        back_populates="contents",
    )
    history: Mapped[list["EditorialContentHistory"]] = relationship(
        back_populates="content",
        cascade="all, delete-orphan",
        order_by="EditorialContentHistory.modified_at.desc()",
    )


class EditorialContentHistory(Base, UUIDMixin):
    """Historique des modifications d'un contenu éditorial."""

    __tablename__ = "editorial_contents_history"

    content_id: Mapped[str] = mapped_column(
        ForeignKey("editorial_contents.id", ondelete="CASCADE"),
        nullable=False,
    )
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    modified_by_external_id: Mapped[str | None] = mapped_column(String(36))
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relations
    content: Mapped["EditorialContent"] = relationship(back_populates="history")
