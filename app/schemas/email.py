"""
Schémas Email
=============

Schémas Pydantic pour les endpoints email.
"""

from pydantic import BaseModel, EmailStr


class EmailTestRequest(BaseModel):
    """Requête d'envoi d'email de test."""

    to: EmailStr
    subject: str = "Test email USenghor"
    message: str = "Ceci est un email de test envoyé depuis l'application USenghor."


class EmailTestResponse(BaseModel):
    """Réponse d'envoi d'email de test."""

    success: bool
    message: str
