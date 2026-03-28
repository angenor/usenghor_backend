-- ============================================================================
-- Migration 030: Ajout du champ slug à la table albums
-- Feature: 015-mediatheque
-- ============================================================================

-- 1. Ajouter la colonne slug (nullable temporairement)
ALTER TABLE albums ADD COLUMN IF NOT EXISTS slug VARCHAR(300);

-- 2. Fonction de slugification SQL
CREATE OR REPLACE FUNCTION _slugify(input TEXT) RETURNS TEXT AS $$
DECLARE
    result TEXT;
BEGIN
    result := lower(input);
    -- Translitération des caractères accentués courants
    result := translate(result,
        'àâäáãåèéêëìíîïòóôöõùúûüýÿñçœæ',
        'aaaaaaeeeeiiiioooooouuuuyyncoa');
    -- Remplacer tout ce qui n'est pas alphanumérique par un tiret
    result := regexp_replace(result, '[^a-z0-9]+', '-', 'g');
    -- Supprimer les tirets en début et fin
    result := trim(both '-' from result);
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 3. Générer les slugs pour les albums existants
DO $$
DECLARE
    rec RECORD;
    base_slug TEXT;
    final_slug TEXT;
    counter INT;
BEGIN
    FOR rec IN SELECT id, title FROM albums WHERE slug IS NULL ORDER BY created_at ASC LOOP
        base_slug := _slugify(rec.title);
        IF base_slug = '' THEN
            base_slug := 'album';
        END IF;
        final_slug := base_slug;
        counter := 2;
        WHILE EXISTS (SELECT 1 FROM albums WHERE slug = final_slug AND id != rec.id) LOOP
            final_slug := base_slug || '-' || counter;
            counter := counter + 1;
        END LOOP;
        UPDATE albums SET slug = final_slug WHERE id = rec.id;
    END LOOP;
END;
$$;

-- 4. Rendre la colonne NOT NULL
ALTER TABLE albums ALTER COLUMN slug SET NOT NULL;

-- 5. Créer l'index unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_albums_slug ON albums(slug);

-- 6. Nettoyer la fonction temporaire
DROP FUNCTION IF EXISTS _slugify(TEXT);
