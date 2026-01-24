"""
Exceptions personnalisées
=========================

Exceptions HTTP personnalisées pour l'API.
"""

from fastapi import HTTPException, status


class CredentialsException(HTTPException):
    """Exception pour les erreurs d'authentification."""

    def __init__(self, detail: str = "Identifiants invalides"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionDeniedException(HTTPException):
    """Exception pour les erreurs de permission."""

    def __init__(self, detail: str = "Permission refusée"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class NotFoundException(HTTPException):
    """Exception pour les ressources non trouvées."""

    def __init__(self, detail: str = "Ressource non trouvée"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class ConflictException(HTTPException):
    """Exception pour les conflits (doublon, etc.)."""

    def __init__(self, detail: str = "Conflit détecté"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class ValidationException(HTTPException):
    """Exception pour les erreurs de validation."""

    def __init__(self, detail: str = "Erreur de validation"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )
