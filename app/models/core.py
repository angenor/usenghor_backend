"""
Modèles Core
============

Modèles SQLAlchemy pour les données de référence partagées (pays).
"""

from sqlalchemy import Boolean, String, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Country(Base, UUIDMixin, TimestampMixin):
    """Modèle pour les pays."""

    __tablename__ = "countries"

    iso_code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    iso_code3: Mapped[str | None] = mapped_column(String(3), unique=True)
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(100))
    name_ar: Mapped[str | None] = mapped_column(String(100))
    phone_code: Mapped[str | None] = mapped_column(String(10))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("idx_countries_iso_code", "iso_code"),
        Index("idx_countries_name_fr", "name_fr"),
    )

    def __repr__(self) -> str:
        return f"<Country {self.iso_code} - {self.name_fr}>"
