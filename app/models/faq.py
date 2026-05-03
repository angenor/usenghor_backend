"""
Modèles FAQ
===========

Modèles SQLAlchemy pour les catégories et entrées de la FAQ trilingue.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class FaqCategory(Base, UUIDMixin, TimestampMixin):
    """Catégorie de la FAQ (trilingue, ordonnable, désactivable)."""

    __tablename__ = "faq_categories"

    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    label_fr: Mapped[str] = mapped_column(String(120), nullable=False)
    label_en: Mapped[str | None] = mapped_column(String(120))
    label_ar: Mapped[str | None] = mapped_column(String(120))
    description_fr: Mapped[str | None] = mapped_column(Text)
    description_en: Mapped[str | None] = mapped_column(Text)
    description_ar: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    entries: Mapped[list["FaqEntry"]] = relationship(
        back_populates="category",
        order_by="FaqEntry.display_order",
    )

    __table_args__ = (
        CheckConstraint("code ~ '^[a-z0-9_-]+$'", name="chk_faq_categories_code"),
    )


class FaqEntry(Base, UUIDMixin, TimestampMixin):
    """Entrée de la FAQ (question + réponse riche FR/EN/AR)."""

    __tablename__ = "faq_entries"

    category_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("faq_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    question_fr: Mapped[str] = mapped_column(String(300), nullable=False)
    question_en: Mapped[str | None] = mapped_column(String(300))
    question_ar: Mapped[str | None] = mapped_column(String(300))
    answer_fr_md: Mapped[str] = mapped_column(Text, nullable=False)
    answer_fr_html: Mapped[str] = mapped_column(Text, nullable=False)
    answer_en_md: Mapped[str | None] = mapped_column(Text)
    answer_en_html: Mapped[str | None] = mapped_column(Text)
    answer_ar_md: Mapped[str | None] = mapped_column(Text)
    answer_ar_html: Mapped[str | None] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    updated_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    category: Mapped[FaqCategory] = relationship(back_populates="entries")

    __table_args__ = (
        CheckConstraint(
            "slug ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]$' OR slug ~ '^[a-z0-9]$'",
            name="chk_faq_entries_slug",
        ),
        CheckConstraint(
            "LENGTH(question_fr) >= 3",
            name="chk_faq_entries_question_fr_min",
        ),
    )
