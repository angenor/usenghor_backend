#!/usr/bin/env python3
"""
Migration EditorJS vers TOAST UI Editor.

Lit les colonnes *_legacy (JSON EditorJS) et peuple *_html + *_md.
Doit etre execute APRES la migration SQL 018_migrate_editorjs_to_toastui.sql.

Usage:
    python scripts/migrate_editorjs_to_toastui.py [--dry-run] [--table TABLE] [--verbose]

Options:
    --dry-run   Affiche les conversions sans ecrire en base
    --table     Ne traiter qu'une table specifique (ex: --table news)
    --verbose   Affiche le detail de chaque conversion
"""

import argparse
import json
import logging
import re
import sys
from html import escape as html_escape

import psycopg2
import psycopg2.extras

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================
# Configuration : tables et colonnes a migrer
# ============================================================
# Format: { table: [(colonne_legacy, colonne_html, colonne_md), ...] }
MIGRATION_MAP: dict[str, list[tuple[str, str, str]]] = {
    "events": [
        ("content_legacy", "content_html", "content_md"),
    ],
    "news": [
        ("content_legacy", "content_html", "content_md"),
    ],
    "projects": [
        ("description_legacy", "description_html", "description_md"),
        ("summary_legacy", "summary_html", "summary_md"),
    ],
    "project_calls": [
        ("description_legacy", "description_html", "description_md"),
        ("conditions_legacy", "conditions_html", "conditions_md"),
    ],
    "programs": [
        ("description_legacy", "description_html", "description_md"),
        ("teaching_methods_legacy", "teaching_methods_html", "teaching_methods_md"),
        ("format_legacy", "format_html", "format_md"),
        ("evaluation_methods_legacy", "evaluation_methods_html", "evaluation_methods_md"),
    ],
    "application_calls": [
        ("description_legacy", "description_html", "description_md"),
        ("target_audience_legacy", "target_audience_html", "target_audience_md"),
    ],
    "sectors": [
        ("description_legacy", "description_html", "description_md"),
        ("mission_legacy", "mission_html", "mission_md"),
    ],
    "services": [
        ("description_legacy", "description_html", "description_md"),
        ("mission_legacy", "mission_html", "mission_md"),
    ],
    "service_objectives": [
        ("description_legacy", "description_html", "description_md"),
    ],
    "service_achievements": [
        ("description_legacy", "description_html", "description_md"),
    ],
    "service_projects": [
        ("description_legacy", "description_html", "description_md"),
    ],
}


# ============================================================
# Convertisseur EditorJS JSON -> HTML
# ============================================================

def editorjs_to_html(data: dict) -> str:
    """Convertit un objet EditorJS OutputData en HTML."""
    blocks = data.get("blocks", [])
    if not blocks:
        return ""
    parts = []
    for block in blocks:
        block_type = block.get("type", "")
        block_data = block.get("data", {})
        html = render_block_html(block_type, block_data)
        if html:
            parts.append(html)
    return "\n".join(parts)


def render_block_html(block_type: str, data: dict) -> str:
    """Rend un bloc EditorJS en HTML (miroir de EditorJSRenderer.vue)."""
    match block_type:
        case "paragraph":
            text = data.get("text", "")
            return f"<p>{text}</p>"

        case "header":
            level = data.get("level", 2)
            text = data.get("text", "")
            return f"<h{level}>{text}</h{level}>"

        case "list":
            style = data.get("style", "unordered")
            tag = "ol" if style == "ordered" else "ul"
            items = data.get("items", [])
            list_items = _render_list_items_html(items, tag)
            return f"<{tag}>{list_items}</{tag}>"

        case "image":
            url = data.get("file", {}).get("url", "")
            caption = data.get("caption", "")
            classes = []
            if data.get("withBorder"):
                classes.append("border border-gray-300 dark:border-gray-600")
            if data.get("withBackground"):
                classes.append("bg-gray-100 dark:bg-gray-800 p-4")
            if data.get("stretched"):
                classes.append("w-full")
            class_attr = " ".join(classes)
            caption_html = ""
            if caption:
                caption_html = f'<figcaption class="text-center text-sm text-gray-500 dark:text-gray-400 mt-2">{caption}</figcaption>'
            return f'<figure class="{class_attr}"><img src="{url}" alt="{caption}" class="mx-auto" />{caption_html}</figure>'

        case "quote":
            text = data.get("text", "")
            caption = data.get("caption", "")
            caption_html = ""
            if caption:
                caption_html = f'<cite class="block text-sm text-gray-500 dark:text-gray-400 mt-2">— {caption}</cite>'
            return f'<blockquote class="border-l-4 border-brand-red-500 pl-4 italic"><p>{text}</p>{caption_html}</blockquote>'

        case "delimiter":
            return '<hr class="my-8 border-gray-300 dark:border-gray-600" />'

        case "embed":
            embed_url = data.get("embed", "")
            width = data.get("width", "100%")
            height = data.get("height", 400)
            caption = data.get("caption", "")
            caption_html = ""
            if caption:
                caption_html = f'<p class="text-center text-sm text-gray-500 dark:text-gray-400 mt-2">{caption}</p>'
            return (
                f'<div class="embed-container aspect-video">'
                f'<iframe src="{embed_url}" width="{width}" height="{height}" '
                f'frameborder="0" allowfullscreen class="w-full"></iframe>'
                f'{caption_html}</div>'
            )

        case "table":
            return _render_table_html(data)

        case "linkTool":
            link = data.get("link", "")
            meta = data.get("meta", {})
            title = meta.get("title", link)
            description = meta.get("description", "")
            image_url = meta.get("image", {}).get("url", "")
            img_html = ""
            if image_url:
                img_html = f'<img src="{image_url}" alt="" class="w-16 h-16 object-cover rounded" />'
            desc_html = ""
            if description:
                desc_html = f'<p class="text-sm text-gray-500 dark:text-gray-400">{description}</p>'
            return (
                f'<a href="{link}" target="_blank" rel="noopener noreferrer" '
                f'class="block p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">'
                f'<div class="flex gap-4">{img_html}<div>'
                f'<p class="font-medium text-gray-900 dark:text-gray-100">{title}</p>'
                f'{desc_html}</div></div></a>'
            )

        case "checklist":
            items = data.get("items", [])
            list_items = ""
            for item in items:
                text = item.get("text", "")
                checked = item.get("checked", False)
                checkbox = "☑" if checked else "☐"
                list_items += f"<li>{checkbox} {text}</li>"
            return f"<ul>{list_items}</ul>"

        case _:
            logger.warning("Type de bloc inconnu ignore: %s", block_type)
            return ""


def _render_list_items_html(items: list, tag: str) -> str:
    """Rend les items de liste (supporte les formats v1 string et v2 nested)."""
    parts = []
    for item in items:
        if isinstance(item, str):
            parts.append(f"<li>{item}</li>")
        elif isinstance(item, dict):
            content = item.get("content", "")
            children = item.get("items", [])
            nested = ""
            if children:
                nested_items = _render_list_items_html(children, tag)
                nested = f'<{tag} class="ml-4">{nested_items}</{tag}>'
            parts.append(f"<li>{content}{nested}</li>")
    return "".join(parts)


def _render_table_html(data: dict) -> str:
    """Rend un bloc table EditorJS (format simple et MergeTable)."""
    rows = data.get("content", [])
    if not rows:
        return ""
    with_headings = data.get("withHeadings", True)
    column_widths = data.get("columnWidths", [])

    # Detecter le format (objets = MergeTable, strings = table simple)
    is_new_format = (
        len(rows) > 0
        and len(rows[0]) > 0
        and isinstance(rows[0][0], dict)
        and "content" in rows[0][0]
    )

    colgroup = ""
    if column_widths:
        cols = "".join(f'<col style="width: {w}px">' for w in column_widths)
        colgroup = f"<colgroup>{cols}</colgroup>"

    table_rows = []
    for row_idx, row in enumerate(rows):
        cells = []
        for cell in row:
            if is_new_format:
                if isinstance(cell, dict):
                    if cell.get("merged"):
                        continue
                    is_header = with_headings and row_idx == 0
                    tag = "th" if is_header else "td"
                    header_class = " bg-gray-50 dark:bg-gray-700 font-semibold" if is_header else ""
                    attrs = ""
                    colspan = cell.get("colspan", 1)
                    rowspan = cell.get("rowspan", 1)
                    if colspan and colspan > 1:
                        attrs += f' colspan="{colspan}"'
                    if rowspan and rowspan > 1:
                        attrs += f' rowspan="{rowspan}"'
                    content = cell.get("content", "")
                    cells.append(
                        f'<{tag} class="border border-gray-300 dark:border-gray-600 px-4 py-2{header_class}"{attrs}>{content}</{tag}>'
                    )
            else:
                is_header = with_headings and row_idx == 0
                tag = "th" if is_header else "td"
                header_class = " bg-gray-50 dark:bg-gray-700 font-semibold" if is_header else ""
                cells.append(
                    f'<{tag} class="border border-gray-300 dark:border-gray-600 px-4 py-2{header_class}">{cell}</{tag}>'
                )
        table_rows.append(f"<tr>{''.join(cells)}</tr>")

    table_style = ' style="table-layout: fixed;"' if column_widths else ""
    return (
        f'<div class="table-scroll-wrapper">'
        f'<table class="w-full border-collapse"{table_style}>'
        f'{colgroup}{"".join(table_rows)}</table></div>'
    )


# ============================================================
# Convertisseur EditorJS JSON -> Markdown
# ============================================================

def editorjs_to_markdown(data: dict) -> str:
    """Convertit un objet EditorJS OutputData en Markdown."""
    blocks = data.get("blocks", [])
    if not blocks:
        return ""
    parts = []
    for block in blocks:
        block_type = block.get("type", "")
        block_data = block.get("data", {})
        md = render_block_md(block_type, block_data)
        if md is not None:
            parts.append(md)
    return "\n\n".join(parts)


def _strip_html(text: str) -> str:
    """Supprime les balises HTML pour le markdown brut."""
    # Convertir <b>/<strong> en **
    text = re.sub(r"<(?:b|strong)>(.*?)</(?:b|strong)>", r"**\1**", text, flags=re.DOTALL)
    # Convertir <i>/<em> en *
    text = re.sub(r"<(?:i|em)>(.*?)</(?:i|em)>", r"*\1*", text, flags=re.DOTALL)
    # Convertir <code> en `
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", text, flags=re.DOTALL)
    # Convertir <mark> en ==
    text = re.sub(r"<mark[^>]*>(.*?)</mark>", r"==\1==", text, flags=re.DOTALL)
    # Convertir <a href="url">text</a> en [text](url)
    text = re.sub(r'<a\s+href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.DOTALL)
    # Convertir <br> en newline
    text = re.sub(r"<br\s*/?>", "\n", text)
    # Supprimer les balises restantes
    text = re.sub(r"<[^>]+>", "", text)
    return text


def render_block_md(block_type: str, data: dict) -> str | None:
    """Rend un bloc EditorJS en Markdown."""
    match block_type:
        case "paragraph":
            text = _strip_html(data.get("text", ""))
            return text

        case "header":
            level = data.get("level", 2)
            text = _strip_html(data.get("text", ""))
            return f"{'#' * level} {text}"

        case "list":
            style = data.get("style", "unordered")
            items = data.get("items", [])
            return _render_list_items_md(items, style, indent=0)

        case "image":
            url = data.get("file", {}).get("url", "")
            caption = data.get("caption", "")
            alt = _strip_html(caption) if caption else ""
            return f"![{alt}]({url})"

        case "quote":
            text = _strip_html(data.get("text", ""))
            caption = data.get("caption", "")
            lines = text.split("\n")
            quoted = "\n".join(f"> {line}" for line in lines)
            if caption:
                quoted += f"\n> — {_strip_html(caption)}"
            return quoted

        case "delimiter":
            return "---"

        case "embed":
            embed_url = data.get("embed", "")
            caption = data.get("caption", "")
            if caption:
                return f"[{_strip_html(caption)}]({embed_url})"
            return f"<{embed_url}>"

        case "table":
            return _render_table_md(data)

        case "linkTool":
            link = data.get("link", "")
            meta = data.get("meta", {})
            title = meta.get("title", link)
            return f"[{_strip_html(title)}]({link})"

        case "checklist":
            items = data.get("items", [])
            lines = []
            for item in items:
                text = _strip_html(item.get("text", ""))
                checked = item.get("checked", False)
                mark = "x" if checked else " "
                lines.append(f"- [{mark}] {text}")
            return "\n".join(lines)

        case _:
            return None


def _render_list_items_md(items: list, style: str, indent: int) -> str:
    """Rend les items de liste en Markdown avec indentation."""
    lines = []
    for i, item in enumerate(items):
        prefix = "  " * indent
        if isinstance(item, str):
            text = _strip_html(item)
            marker = f"{i + 1}." if style == "ordered" else "-"
            lines.append(f"{prefix}{marker} {text}")
        elif isinstance(item, dict):
            content = _strip_html(item.get("content", ""))
            marker = f"{i + 1}." if style == "ordered" else "-"
            lines.append(f"{prefix}{marker} {content}")
            children = item.get("items", [])
            if children:
                lines.append(_render_list_items_md(children, style, indent + 1))
    return "\n".join(lines)


def _render_table_md(data: dict) -> str:
    """Rend un bloc table en Markdown."""
    rows = data.get("content", [])
    if not rows:
        return ""
    with_headings = data.get("withHeadings", True)

    # Extraire le texte de chaque cellule
    md_rows = []
    for row in rows:
        cells = []
        for cell in row:
            if isinstance(cell, dict):
                if cell.get("merged"):
                    cells.append("")
                else:
                    cells.append(_strip_html(cell.get("content", "")))
            else:
                cells.append(_strip_html(str(cell)))
        md_rows.append(cells)

    if not md_rows:
        return ""

    # Calculer largeurs de colonnes
    num_cols = max(len(r) for r in md_rows) if md_rows else 0
    # Normaliser les lignes
    for row in md_rows:
        while len(row) < num_cols:
            row.append("")

    lines = []
    # Premiere ligne (header ou donnees)
    lines.append("| " + " | ".join(md_rows[0]) + " |")
    # Separateur
    lines.append("| " + " | ".join("---" for _ in range(num_cols)) + " |")
    # Lignes suivantes
    for row in md_rows[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


# ============================================================
# Conversion principale
# ============================================================

def parse_editorjs_json(raw: str) -> dict | None:
    """Parse une chaine JSON EditorJS. Retourne None si invalide.

    Gere deux formats :
    - Direct : {"time": ..., "blocks": [...]}
    - Multilingue : {"fr": {"time": ..., "blocks": [...]}, "en": null, "ar": null}
      Dans ce cas, extrait la locale FR (prioritaire), puis EN, puis AR.
    """
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    if not raw.startswith("{"):
        return None
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None

        # Format direct EditorJS
        if "blocks" in data:
            return data

        # Format multilingue {"fr": {...}, "en": ..., "ar": ...}
        locales = ("fr", "en", "ar")
        if any(k in data for k in locales):
            # Extraire la premiere locale non-null (priorite: fr > en > ar)
            for locale in locales:
                locale_data = data.get(locale)
                if isinstance(locale_data, dict) and "blocks" in locale_data:
                    logger.debug("Contenu multilingue detecte, extraction locale '%s'", locale)
                    return locale_data
            logger.debug("Wrapper multilingue sans contenu EditorJS valide")
            return None

        logger.debug("JSON valide mais pas de cle 'blocks': %s...", raw[:80])
        return None
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("JSON invalide (skip): %s — %s", raw[:80], e)
        return None


def convert_column(raw_value: str | None) -> tuple[str | None, str | None]:
    """Convertit une valeur de colonne legacy en (html, md). NULL -> (NULL, NULL)."""
    if raw_value is None:
        return None, None

    data = parse_editorjs_json(raw_value)
    if data is None:
        # Pas du JSON EditorJS — traiter comme du texte brut ou HTML existant
        text = raw_value.strip()
        if not text:
            return None, None
        # Si c'est deja du HTML, le garder tel quel
        if "<" in text and ">" in text:
            md = _strip_html(text)
            return text, md
        # Texte brut : envelopper dans un <p>
        return f"<p>{text}</p>", text

    html = editorjs_to_html(data)
    md = editorjs_to_markdown(data)
    return html or None, md or None


# ============================================================
# Execution de la migration
# ============================================================

def get_db_connection():
    """Connexion a la base PostgreSQL locale.

    Utilise les variables d'environnement si disponibles,
    sinon les valeurs par defaut du docker-compose.
    """
    import os
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "usenghor"),
        user=os.getenv("POSTGRES_USER", "usenghor"),
        password=os.getenv("POSTGRES_PASSWORD", "usenghor_secret"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
    )


def migrate_table(
    conn,
    table: str,
    columns: list[tuple[str, str, str]],
    dry_run: bool = False,
    verbose: bool = False,
):
    """Migre toutes les colonnes d'une table."""
    logger.info("=== Table: %s ===", table)

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Construire la requete SELECT
        legacy_cols = [c[0] for c in columns]
        select_cols = ", ".join(["id"] + legacy_cols)
        cur.execute(f"SELECT {select_cols} FROM {table}")
        rows = cur.fetchall()

        total = len(rows)
        converted = 0
        skipped = 0
        errors = 0

        for row in rows:
            row_id = row["id"]
            updates = {}

            for legacy_col, html_col, md_col in columns:
                raw_value = row[legacy_col]
                try:
                    html_val, md_val = convert_column(raw_value)
                    updates[html_col] = html_val
                    updates[md_col] = md_val
                except Exception as e:
                    logger.error(
                        "Erreur conversion %s.%s id=%s: %s",
                        table, legacy_col, row_id, e,
                    )
                    errors += 1
                    continue

            if updates:
                if verbose:
                    for key, val in updates.items():
                        preview = (val[:80] + "...") if val and len(val) > 80 else val
                        logger.info("  %s.id=%s -> %s = %s", table, row_id, key, preview)

                if not dry_run:
                    set_clause = ", ".join(f"{k} = %s" for k in updates)
                    values = list(updates.values()) + [row_id]
                    cur.execute(
                        f"UPDATE {table} SET {set_clause} WHERE id = %s",
                        values,
                    )
                converted += 1

        if not dry_run:
            conn.commit()

        logger.info(
            "  %s: %d total, %d convertis, %d ignores, %d erreurs",
            table, total, converted, skipped, errors,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Migration EditorJS vers TOAST UI Editor"
    )
    parser.add_argument("--dry-run", action="store_true", help="Mode simulation")
    parser.add_argument("--table", type=str, help="Ne traiter qu'une table")
    parser.add_argument("--verbose", action="store_true", help="Mode verbeux")
    args = parser.parse_args()

    if args.dry_run:
        logger.info("*** MODE DRY-RUN — aucune ecriture en base ***")

    conn = get_db_connection()

    try:
        tables_to_process = MIGRATION_MAP
        if args.table:
            if args.table not in MIGRATION_MAP:
                logger.error("Table inconnue: %s", args.table)
                logger.info("Tables disponibles: %s", ", ".join(MIGRATION_MAP.keys()))
                sys.exit(1)
            tables_to_process = {args.table: MIGRATION_MAP[args.table]}

        for table, columns in tables_to_process.items():
            migrate_table(conn, table, columns, args.dry_run, args.verbose)

        logger.info("Migration terminee avec succes.")

    except Exception as e:
        logger.error("Erreur fatale: %s", e)
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
