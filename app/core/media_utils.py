"""
Utilitaires Média
=================

Fonctions partagées pour la résolution d'URLs de médias.
"""

from app.models.media import Media


def resolve_media_url(media: Media | None) -> str | None:
    """
    Résout l'URL d'un média.

    Retourne l'URL relative de l'endpoint de téléchargement public.
    Le frontend préfixera avec son apiBase configuré.
    """
    if not media:
        return None
    if media.is_external_url:
        return media.url
    # Pour les fichiers locaux, retourner l'URL de l'endpoint de téléchargement
    return f"/api/public/media/{media.id}/download"
