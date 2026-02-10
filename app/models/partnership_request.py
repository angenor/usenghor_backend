"""
Modèles PartnershipRequest
===========================

Modèles SQLAlchemy pour les demandes de partenariat.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class PartnershipRequestType(str, enum.Enum):
    """Type de partenariat demandé."""

    ACADEMIC = "academic"
    INSTITUTIONAL = "institutional"
    BUSINESS = "business"
    OTHER = "other"


class PartnershipRequestStatus(str, enum.Enum):
    """Statut d'une demande de partenariat."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PartnershipRequest(Base, UUIDMixin, TimestampMixin):
    """Demande de partenariat soumise via le formulaire public."""

    __tablename__ = "partnership_requests"

    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[PartnershipRequestType] = mapped_column(
        Enum(
            PartnershipRequestType,
            name="partnership_request_type",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PartnershipRequestStatus] = mapped_column(
        Enum(
            PartnershipRequestStatus,
            name="partnership_request_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=PartnershipRequestStatus.PENDING,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    reviewed_by_external_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True, default=None
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    partner_external_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True, default=None
    )
