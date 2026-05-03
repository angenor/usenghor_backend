"""
Service Slug FAQ
=================

Génération de slugs URL-safe pour les entrées FAQ depuis le libellé FR.
Translit ASCII basique (NFKD), résolution de collisions par suffixe -2/-3…
"""

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import FaqEntry

MAX_SLUG_LENGTH = 120
DEFAULT_FALLBACK = "question"


def _slugify(text: str) -> str:
    """Translit ASCII + lowercase + remplacement non-alphanum par tirets."""
    if not text:
        return ""
    # Décomposition Unicode -> retrait des diacritiques
    normalized = unicodedata.normalize("NFKD", text)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    # Lowercase + remplacement
    lowered = ascii_only.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", lowered)
    cleaned = cleaned.strip("-")
    return cleaned[:MAX_SLUG_LENGTH]


async def generate_slug(
    question_fr: str,
    db: AsyncSession,
    *,
    exclude_id: str | None = None,
) -> str:
    """
    Génère un slug unique pour une entrée FAQ.

    Args:
        question_fr: Libellé FR source.
        db: Session SQLAlchemy async.
        exclude_id: ID d'une entrée à exclure de la vérification (cas update).

    Returns:
        Slug unique conforme au pattern [a-z0-9][a-z0-9-]*.
    """
    base = _slugify(question_fr) or DEFAULT_FALLBACK

    candidate = base
    suffix = 2
    while await _slug_exists(candidate, db, exclude_id=exclude_id):
        suffix_str = f"-{suffix}"
        truncated = base[: MAX_SLUG_LENGTH - len(suffix_str)]
        candidate = f"{truncated}{suffix_str}"
        suffix += 1
        if suffix > 1000:
            raise RuntimeError(
                "Impossible de générer un slug unique après 1000 tentatives"
            )
    return candidate


async def _slug_exists(
    slug: str, db: AsyncSession, *, exclude_id: str | None = None
) -> bool:
    stmt = select(FaqEntry.id).where(FaqEntry.slug == slug)
    if exclude_id is not None:
        stmt = stmt.where(FaqEntry.id != exclude_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None
