"""
Schémas communs
===============

Schémas Pydantic partagés entre les différents modules.
"""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Réponse simple avec message."""

    message: str


class IdResponse(BaseModel):
    """Réponse avec ID et message."""

    id: str
    message: str


class PaginatedResponse(BaseModel):
    """Réponse paginée générique."""

    items: list
    total: int
    page: int
    limit: int
    pages: int
