"""
Schémas Newsletter
==================

Schémas Pydantic pour la gestion de la newsletter.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.newsletter import CampaignStatus, SendStatus


# =============================================================================
# SUBSCRIBERS
# =============================================================================


class SubscriberBase(BaseModel):
    """Schéma de base pour les abonnés."""

    email: EmailStr = Field(..., description="Adresse email")
    last_name: str | None = Field(None, max_length=100, description="Nom")
    first_name: str | None = Field(None, max_length=100, description="Prénom")
    source: str | None = Field(None, max_length=100, description="Source d'inscription")


class SubscriberCreate(SubscriberBase):
    """Schéma pour la création d'un abonné."""

    user_external_id: str | None = Field(None, description="ID utilisateur lié")


class SubscriberUpdate(BaseModel):
    """Schéma pour la mise à jour d'un abonné."""

    last_name: str | None = Field(None, max_length=100)
    first_name: str | None = Field(None, max_length=100)
    active: bool | None = None


class SubscriberRead(SubscriberBase):
    """Schéma pour la lecture d'un abonné."""

    id: str
    user_external_id: str | None
    active: bool
    unsubscribe_token: str | None
    subscribed_at: datetime
    unsubscribed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SubscriberPublic(BaseModel):
    """Schéma public (sans token de désinscription)."""

    id: str
    email: EmailStr
    first_name: str | None
    last_name: str | None
    subscribed_at: datetime

    model_config = {"from_attributes": True}


class SubscribeRequest(BaseModel):
    """Schéma pour s'abonner à la newsletter (route publique)."""

    email: EmailStr = Field(..., description="Adresse email")
    first_name: str | None = Field(None, max_length=100, description="Prénom")
    last_name: str | None = Field(None, max_length=100, description="Nom")
    source: str | None = Field(None, max_length=100, description="Source d'inscription")


class UnsubscribeRequest(BaseModel):
    """Schéma pour se désabonner."""

    token: str = Field(..., description="Token de désinscription")


# =============================================================================
# CAMPAIGNS
# =============================================================================


class CampaignBase(BaseModel):
    """Schéma de base pour les campagnes."""

    title: str = Field(..., min_length=1, max_length=255, description="Titre interne")
    subject: str = Field(..., min_length=1, max_length=255, description="Sujet de l'email")
    html_content: str | None = Field(None, description="Contenu HTML")
    text_content: str | None = Field(None, description="Contenu texte brut")


class CampaignCreate(CampaignBase):
    """Schéma pour la création d'une campagne."""

    scheduled_send_at: datetime | None = Field(None, description="Date d'envoi programmé")


class CampaignUpdate(BaseModel):
    """Schéma pour la mise à jour d'une campagne."""

    title: str | None = Field(None, min_length=1, max_length=255)
    subject: str | None = Field(None, min_length=1, max_length=255)
    html_content: str | None = None
    text_content: str | None = None
    scheduled_send_at: datetime | None = None


class CampaignRead(CampaignBase):
    """Schéma pour la lecture d'une campagne."""

    id: str
    status: CampaignStatus
    scheduled_send_at: datetime | None
    sent_at: datetime | None
    recipient_count: int
    open_count: int
    click_count: int
    created_by_external_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CampaignSchedule(BaseModel):
    """Schéma pour programmer l'envoi d'une campagne."""

    scheduled_send_at: datetime = Field(..., description="Date d'envoi programmé")


class CampaignStatistics(BaseModel):
    """Statistiques d'une campagne."""

    campaign_id: str
    recipient_count: int
    sent_count: int
    open_count: int
    click_count: int
    error_count: int
    open_rate: float
    click_rate: float


# =============================================================================
# SENDS
# =============================================================================


class SendRead(BaseModel):
    """Schéma pour la lecture d'un envoi."""

    id: str
    campaign_id: str
    subscriber_id: str
    email: str
    status: SendStatus
    sent_at: datetime
    opened_at: datetime | None
    clicked_at: datetime | None
    error_message: str | None

    model_config = {"from_attributes": True}


class SendWithSubscriber(SendRead):
    """Schéma d'envoi avec les infos de l'abonné."""

    subscriber_first_name: str | None = None
    subscriber_last_name: str | None = None


# =============================================================================
# BULK OPERATIONS
# =============================================================================


class BulkImportResult(BaseModel):
    """Résultat d'un import en masse."""

    total: int
    imported: int
    duplicates: int
    errors: int


class SubscriberImport(BaseModel):
    """Schéma pour l'import d'un abonné."""

    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None


class BulkSubscriberImport(BaseModel):
    """Schéma pour l'import en masse d'abonnés."""

    subscribers: list[SubscriberImport]
    source: str | None = Field(None, description="Source de l'import")


# =============================================================================
# NEWSLETTER STATISTICS
# =============================================================================


class NewsletterStatistics(BaseModel):
    """Statistiques globales de la newsletter."""

    total_subscribers: int
    active_subscribers: int
    total_campaigns: int
    sent_campaigns: int
    total_sends: int
    average_open_rate: float
    average_click_rate: float
