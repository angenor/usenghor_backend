-- ============================================================================
-- Rollback 050 : à jouer AVANT les rollbacks 049 → 045.
-- Retire exactement ce que la migration 050 a ajouté, dans l'ordre inverse :
-- lien court pei, entrée de menu « entrepreneurship », pôle créé (identifiant fixe),
-- trigger, fonction, contraintes, index et colonnes. Rejouable sans erreur.
-- ============================================================================

BEGIN;

DELETE FROM short_links WHERE code = 'pei' AND target_url = '/entrepreneuriat';

DO $$
DECLARE
    raw TEXT;
    arr JSONB;
BEGIN
    SELECT value INTO raw FROM editorial_contents WHERE key = 'navbar.secondary.about.children';
    IF raw IS NULL OR btrim(raw) = '' THEN
        RETURN;
    END IF;
    BEGIN
        arr := raw::jsonb;
    EXCEPTION WHEN others THEN
        RAISE NOTICE 'Menu : valeur illisible — non modifiée';
        RETURN;
    END;
    IF jsonb_typeof(arr) = 'array' THEN
        UPDATE editorial_contents
        SET value = COALESCE((SELECT jsonb_agg(e ORDER BY ord) FROM jsonb_array_elements(arr) WITH ORDINALITY AS t(e, ord)
                              WHERE e->>'id' IS DISTINCT FROM 'entrepreneurship'), '[]'::jsonb)::text,
            updated_at = NOW()
        WHERE key = 'navbar.secondary.about.children'
          AND EXISTS (SELECT 1 FROM jsonb_array_elements(arr) e WHERE e->>'id' = 'entrepreneurship');
    END IF;
END $$;

DO $$
DECLARE
    pole_fixed CONSTANT UUID := '5e1c0050-0000-4000-8000-00000000e1ab';
    has_content BOOLEAN;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM services WHERE id = pole_fixed) THEN
        RETURN;
    END IF;
    SELECT EXISTS (SELECT 1 FROM service_team WHERE service_id = pole_fixed)
        OR EXISTS (SELECT 1 FROM service_objectives WHERE service_id = pole_fixed)
        OR EXISTS (SELECT 1 FROM service_achievements WHERE service_id = pole_fixed)
        OR EXISTS (SELECT 1 FROM service_projects WHERE service_id = pole_fixed)
        OR EXISTS (SELECT 1 FROM service_media_library WHERE service_id = pole_fixed)
    INTO has_content;
    IF has_content THEN
        RAISE NOTICE 'PEI : le pôle (%) a du contenu rattaché — conservé comme service de premier niveau', pole_fixed;
    ELSE
        DELETE FROM services WHERE id = pole_fixed;
        RAISE NOTICE 'PEI : pôle créé par la migration 050 supprimé';
    END IF;
END $$;

DROP TRIGGER IF EXISTS services_check_hierarchy ON services;
DROP FUNCTION IF EXISTS services_check_hierarchy();
DROP INDEX IF EXISTS idx_services_parent;
ALTER TABLE services DROP CONSTRAINT IF EXISTS services_landing_path_format;
ALTER TABLE services DROP CONSTRAINT IF EXISTS services_parent_not_self;
ALTER TABLE services DROP CONSTRAINT IF EXISTS services_parent_id_fkey;
ALTER TABLE services DROP COLUMN IF EXISTS landing_path;
ALTER TABLE services DROP COLUMN IF EXISTS parent_id;

COMMIT;

\echo 'Rollback 050_services_parent_landing terminé'
