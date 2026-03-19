-- Migration 025: Convertir les descriptions campus de JSON EditorJS vers HTML
-- Les données étaient stockées au format EditorJS (JSON avec blocks)
-- Cette migration les convertit en HTML propre pour description_html
-- et en texte brut pour description_md

BEGIN;

-- Fonction temporaire pour convertir EditorJS JSON en HTML
CREATE OR REPLACE FUNCTION _tmp_editorjs_to_html(raw TEXT) RETURNS TEXT AS $$
DECLARE
    json_data JSONB;
    block JSONB;
    block_type TEXT;
    block_data JSONB;
    html TEXT := '';
    item JSONB;
    list_style TEXT;
    level INT;
BEGIN
    -- Vérifier si c'est du JSON EditorJS
    IF raw IS NULL OR raw = '' THEN
        RETURN NULL;
    END IF;

    -- Essayer de parser comme JSON
    BEGIN
        json_data := raw::JSONB;
    EXCEPTION WHEN OTHERS THEN
        -- Pas du JSON, retourner tel quel (peut-être déjà du HTML)
        RETURN raw;
    END;

    -- Vérifier la structure EditorJS (doit avoir "blocks")
    IF NOT (json_data ? 'blocks') THEN
        RETURN raw;
    END IF;

    -- Parcourir les blocks
    FOR block IN SELECT * FROM jsonb_array_elements(json_data -> 'blocks')
    LOOP
        block_type := block ->> 'type';
        block_data := block -> 'data';

        CASE block_type
            WHEN 'paragraph' THEN
                html := html || '<p>' || COALESCE(block_data ->> 'text', '') || '</p>' || E'\n';

            WHEN 'header' THEN
                level := COALESCE((block_data ->> 'level')::INT, 2);
                html := html || '<h' || level || '>' || COALESCE(block_data ->> 'text', '') || '</h' || level || '>' || E'\n';

            WHEN 'list' THEN
                list_style := COALESCE(block_data ->> 'style', 'unordered');
                IF list_style = 'ordered' THEN
                    html := html || '<ol>' || E'\n';
                ELSE
                    html := html || '<ul>' || E'\n';
                END IF;

                FOR item IN SELECT * FROM jsonb_array_elements(block_data -> 'items')
                LOOP
                    -- Les items peuvent être des objets avec "content" ou des strings simples
                    IF jsonb_typeof(item) = 'object' THEN
                        html := html || '<li>' || COALESCE(item ->> 'content', '') || '</li>' || E'\n';
                    ELSE
                        html := html || '<li>' || COALESCE(item #>> '{}', '') || '</li>' || E'\n';
                    END IF;
                END LOOP;

                IF list_style = 'ordered' THEN
                    html := html || '</ol>' || E'\n';
                ELSE
                    html := html || '</ul>' || E'\n';
                END IF;

            WHEN 'quote' THEN
                html := html || '<blockquote><p>' || COALESCE(block_data ->> 'text', '') || '</p></blockquote>' || E'\n';

            WHEN 'delimiter' THEN
                html := html || '<hr />' || E'\n';

            WHEN 'image' THEN
                html := html || '<img src="' || COALESCE(block_data -> 'file' ->> 'url', block_data ->> 'url', '') || '" alt="' || COALESCE(block_data ->> 'caption', '') || '" />' || E'\n';

            WHEN 'table' THEN
                html := html || '<table>' || E'\n';
                FOR item IN SELECT * FROM jsonb_array_elements(block_data -> 'content')
                LOOP
                    html := html || '<tr>';
                    DECLARE cell JSONB;
                    BEGIN
                        FOR cell IN SELECT * FROM jsonb_array_elements(item)
                        LOOP
                            html := html || '<td>' || COALESCE(cell #>> '{}', '') || '</td>';
                        END LOOP;
                    END;
                    html := html || '</tr>' || E'\n';
                END LOOP;
                html := html || '</table>' || E'\n';

            ELSE
                -- Type inconnu : essayer d'extraire le texte
                IF block_data ? 'text' THEN
                    html := html || '<p>' || COALESCE(block_data ->> 'text', '') || '</p>' || E'\n';
                END IF;
        END CASE;
    END LOOP;

    RETURN NULLIF(TRIM(html), '');
END;
$$ LANGUAGE plpgsql;

-- Fonction temporaire pour extraire le texte brut (markdown simplifié)
CREATE OR REPLACE FUNCTION _tmp_editorjs_to_md(raw TEXT) RETURNS TEXT AS $$
DECLARE
    json_data JSONB;
    block JSONB;
    block_type TEXT;
    block_data JSONB;
    md TEXT := '';
    item JSONB;
    level INT;
    heading_prefix TEXT;
BEGIN
    IF raw IS NULL OR raw = '' THEN
        RETURN NULL;
    END IF;

    BEGIN
        json_data := raw::JSONB;
    EXCEPTION WHEN OTHERS THEN
        RETURN raw;
    END;

    IF NOT (json_data ? 'blocks') THEN
        RETURN raw;
    END IF;

    FOR block IN SELECT * FROM jsonb_array_elements(json_data -> 'blocks')
    LOOP
        block_type := block ->> 'type';
        block_data := block -> 'data';

        CASE block_type
            WHEN 'paragraph' THEN
                md := md || COALESCE(block_data ->> 'text', '') || E'\n\n';

            WHEN 'header' THEN
                level := COALESCE((block_data ->> 'level')::INT, 2);
                heading_prefix := repeat('#', level);
                md := md || heading_prefix || ' ' || COALESCE(block_data ->> 'text', '') || E'\n\n';

            WHEN 'list' THEN
                FOR item IN SELECT * FROM jsonb_array_elements(block_data -> 'items')
                LOOP
                    IF jsonb_typeof(item) = 'object' THEN
                        md := md || '- ' || COALESCE(item ->> 'content', '') || E'\n';
                    ELSE
                        md := md || '- ' || COALESCE(item #>> '{}', '') || E'\n';
                    END IF;
                END LOOP;
                md := md || E'\n';

            WHEN 'quote' THEN
                md := md || '> ' || COALESCE(block_data ->> 'text', '') || E'\n\n';

            WHEN 'delimiter' THEN
                md := md || '---' || E'\n\n';

            ELSE
                IF block_data ? 'text' THEN
                    md := md || COALESCE(block_data ->> 'text', '') || E'\n\n';
                END IF;
        END CASE;
    END LOOP;

    RETURN NULLIF(TRIM(md), '');
END;
$$ LANGUAGE plpgsql;

-- Appliquer la conversion sur tous les campus avec du JSON EditorJS
UPDATE campuses
SET description_html = _tmp_editorjs_to_html(description),
    description_md = _tmp_editorjs_to_md(description)
WHERE description IS NOT NULL
  AND description LIKE '{%"blocks"%';

-- Nettoyer les fonctions temporaires
DROP FUNCTION _tmp_editorjs_to_html(TEXT);
DROP FUNCTION _tmp_editorjs_to_md(TEXT);

COMMIT;
