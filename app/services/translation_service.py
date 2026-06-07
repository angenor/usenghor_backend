"""
Service de traduction automatique
=================================

Traduction FR -> EN/AR via ``deep-translator`` (endpoint web Google, gratuit).

Principes :
- **Non bloquant pour l'event loop** : les appels réseau synchrones de
  ``deep-translator`` sont exécutés dans un thread (``asyncio.to_thread``).
- **Échec silencieux** : toute erreur réseau renvoie ``None`` (le texte source
  n'est pas traduit) ; l'appelant doit garder la sauvegarde fonctionnelle même
  si la traduction échoue. Le repli FR côté lecture publique reste assuré.
- **Préservation du rich text** : ``translate_html`` ne traduit que les *nœuds
  texte* (via BeautifulSoup) et conserve intacte la structure HTML produite par
  l'éditeur TOAST UI.

La traduction n'est appelée qu'à l'écriture (création / modification / bouton
« retraduire ») puis stockée en base — jamais à la lecture.
"""

import asyncio
import logging

from bs4 import BeautifulSoup, NavigableString

from app.config import settings

logger = logging.getLogger(__name__)

# Langues cibles gérées par le pilote.
SUPPORTED_TARGETS: tuple[str, ...] = ("en", "ar")

# Limite de caractères par requête (l'endpoint Google plafonne ~5000).
_MAX_CHUNK = 4500

# Balises dont le contenu ne doit jamais être traduit.
_SKIP_TAGS = {"script", "style", "code", "pre"}


def _is_translatable(value: str | None) -> bool:
    """Vrai si la chaîne contient autre chose que des espaces."""
    return bool(value and value.strip())


def _chunk(text: str, size: int = _MAX_CHUNK) -> list[str]:
    """Découpe un texte long en morceaux <= ``size`` (coupe sur un espace)."""
    if len(text) <= size:
        return [text]
    chunks: list[str] = []
    remaining = text
    while len(remaining) > size:
        cut = remaining.rfind(" ", 0, size)
        if cut <= 0:
            cut = size
        chunks.append(remaining[:cut])
        remaining = remaining[cut:]
    if remaining:
        chunks.append(remaining)
    return chunks


def _translate_sync(text: str, target: str, source: str) -> str:
    """Appel synchrone à deep-translator (exécuté dans un thread)."""
    # Import local : évite de charger la lib si la fonctionnalité est désactivée.
    from deep_translator import GoogleTranslator

    translator = GoogleTranslator(source=source, target=target)
    parts = _chunk(text)
    if len(parts) == 1:
        return translator.translate(text)
    # deep-translator peut renvoyer None sur un fragment intraduisible
    # (ponctuation/nombre seul) → repli sur le fragment d'origine.
    return "".join((translator.translate(p) or p) for p in parts)


def _translate_batch_sync(texts: list[str], target: str, source: str) -> list[str]:
    """Traduit une liste de segments en préservant l'ordre."""
    from deep_translator import GoogleTranslator

    translator = GoogleTranslator(source=source, target=target)
    out: list[str] = []
    for segment in texts:
        if _is_translatable(segment):
            chunks = _chunk(segment)
            # `translate(c)` peut renvoyer None (fragment intraduisible :
            # ponctuation, nombre seul…) → repli sur le fragment d'origine
            # pour ne pas faire échouer tout le bloc HTML.
            out.append("".join((translator.translate(c) or c) for c in chunks))
        else:
            out.append(segment)
    return out


async def translate_text(
    text: str | None,
    target: str,
    source: str | None = None,
) -> str | None:
    """
    Traduit un texte court (question, titre…).

    Renvoie ``None`` si la traduction est désactivée, l'entrée vide, ou en cas
    d'échec réseau.
    """
    if not settings.auto_translate_enabled:
        return None
    if not _is_translatable(text):
        return None
    source = source or settings.auto_translate_source
    if target == source:
        return text
    try:
        return await asyncio.to_thread(_translate_sync, text, target, source)
    except Exception as exc:  # noqa: BLE001 - échec non bloquant volontaire
        logger.warning("Traduction texte échouée (%s -> %s) : %s", source, target, exc)
        return None


async def translate_html(
    html: str | None,
    target: str,
    source: str | None = None,
) -> str | None:
    """
    Traduit le contenu HTML d'un champ rich text en préservant les balises.

    Seuls les nœuds texte sont traduits ; la structure (balises, attributs,
    liens) reste identique à celle produite par l'éditeur TOAST UI.
    Renvoie ``None`` si désactivé / vide / échec.
    """
    if not settings.auto_translate_enabled:
        return None
    if not _is_translatable(html):
        return None
    source = source or settings.auto_translate_source
    if target == source:
        return html

    try:
        soup = BeautifulSoup(html, "html.parser")

        # Collecte des nœuds texte traduisibles (hors balises techniques).
        nodes: list[NavigableString] = []
        for node in soup.find_all(string=True):
            parent = node.parent.name if node.parent else None
            if parent in _SKIP_TAGS:
                continue
            if _is_translatable(str(node)):
                nodes.append(node)

        if not nodes:
            return None

        originals = [str(n) for n in nodes]
        translations = await asyncio.to_thread(
            _translate_batch_sync, originals, target, source
        )

        for node, original, translated in zip(nodes, originals, translations):
            # Conserve l'espacement de bord (Google le supprime parfois).
            leading = original[: len(original) - len(original.lstrip())]
            trailing = original[len(original.rstrip()):]
            node.replace_with(f"{leading}{(translated or original).strip()}{trailing}")

        return str(soup)
    except Exception as exc:  # noqa: BLE001 - échec non bloquant volontaire
        logger.warning("Traduction HTML échouée (%s -> %s) : %s", source, target, exc)
        return None


# ---------------------------------------------------------------------------
# Remplissage automatique des champs traduits (convention additive)
# ---------------------------------------------------------------------------
# Helper réutilisable par tous les modules adoptant le nommage additif
# (colonne FR existante + variantes ``_en`` / ``_ar``). Voir
# MIGRATION_TRADUCTION_AUTO.md §2 et §3.4.


def _lang_attr(base: str, lang: str) -> str:
    """Nom de l'attribut traduit pour ``base`` et ``lang``.

    Pour un champ rich text, le suffixe de langue s'insère **avant**
    ``_html`` / ``_md`` :

    - ``content_html`` -> ``content_en_html``
    - ``content_md``   -> ``content_ar_md``

    Pour un champ texte simple, suffixe direct :

    - ``title`` -> ``title_en``
    """
    for suffix in ("_html", "_md"):
        if base.endswith(suffix):
            return f"{base[: -len(suffix)]}_{lang}{suffix}"
    return f"{base}_{lang}"


async def autofill_translations(
    obj,
    fields,
    *,
    force: bool = False,
    langs: tuple[str, ...] = SUPPORTED_TARGETS,
) -> None:
    """Remplit en place les champs traduits ``_en`` / ``_ar`` d'un objet ORM.

    Paramètres
    ----------
    obj
        Instance (modèle SQLAlchemy ou autre) portant les attributs source FR
        et les attributs cibles traduits.
    fields
        Liste de tuples ``(base_attr, kind)`` où ``kind`` ∈ ``{"text", "html"}``.
        ``base_attr`` est l'attribut FR existant (ex. ``"content_html"``,
        ``"title"``).
    force
        Si ``False`` (défaut), ne remplit que les champs cibles **vides** :
        les corrections manuelles déjà saisies sont préservées. Si ``True``,
        retraduit systématiquement depuis la source FR.
    langs
        Langues cibles (défaut : ``("en", "ar")``).

    Comportement : **non bloquant**. ``translate_text`` / ``translate_html``
    avalent leurs erreurs et renvoient ``None`` → en cas d'échec réseau ou de
    fonctionnalité désactivée, le champ cible est simplement laissé tel quel et
    la sauvegarde de l'appelant reste fonctionnelle (repli FR à la lecture).
    """
    for base, kind in fields:
        src = getattr(obj, base, None)
        if not _is_translatable(src):
            continue
        translate = translate_html if kind == "html" else translate_text
        for lang in langs:
            target = _lang_attr(base, lang)
            if force or not getattr(obj, target, None):
                value = await translate(src, lang)
                if value:
                    setattr(obj, target, value)
