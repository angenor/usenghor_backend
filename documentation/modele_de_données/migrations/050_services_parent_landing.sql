-- ============================================================================
-- Migration 050 : niveau « pôle » des services, rattachement du PEI à la DDE,
--                 entrée de menu « Entreprendre à Senghor », lien court /r/pei
-- Feature 026-pei-org-navigation-launch
-- ============================================================================
-- Effets :
--   1. services.parent_id (FK services.id ON DELETE SET NULL) + services.landing_path,
--      contraintes (pas d'auto-référence, forme du chemin), index partiel,
--      trigger services_check_hierarchy (un seul niveau, même secteur).
--   2. Service « Pôle Entrepreneuriat et Innovation » (PEI, /entrepreneuriat) rattaché
--      à la DDE (clé entrepreneurship.dde_service_id, sinon nom) — identifiant fixe.
--   3. Entrée « entrepreneurship » ajoutée en fin de navbar.secondary.about.children
--      (entrées éditées conservées ; retirée à la main, elle est rajoutée au rejeu).
--   4. Lien court pei → /entrepreneuriat.
-- Rejouable : IF NOT EXISTS, contraintes gardées, insertions conditionnelles, NOTICE.
-- Dépendances : 013 (short_links), 037 (traductions services), 045 (clé DDE, facultative).
-- Rollback : 050_services_parent_landing_rollback.sql — à jouer AVANT les rollbacks 049 → 045.
-- ============================================================================

BEGIN;

-- 1. Structure ----------------------------------------------------------------
ALTER TABLE services ADD COLUMN IF NOT EXISTS parent_id UUID;
ALTER TABLE services ADD COLUMN IF NOT EXISTS landing_path VARCHAR(255);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'services_parent_id_fkey') THEN
        ALTER TABLE services ADD CONSTRAINT services_parent_id_fkey
            FOREIGN KEY (parent_id) REFERENCES services(id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'services_parent_not_self') THEN
        ALTER TABLE services ADD CONSTRAINT services_parent_not_self
            CHECK (parent_id IS NULL OR parent_id <> id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'services_landing_path_format') THEN
        ALTER TABLE services ADD CONSTRAINT services_landing_path_format
            CHECK (landing_path IS NULL OR (landing_path ~ '^/' AND landing_path !~ '^//' AND landing_path !~ '\s'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_services_parent ON services(parent_id) WHERE parent_id IS NOT NULL;

CREATE OR REPLACE FUNCTION services_check_hierarchy() RETURNS TRIGGER AS $$
DECLARE
    parent_row RECORD;
    n_children INTEGER;
BEGIN
    SELECT count(*) INTO n_children FROM services WHERE parent_id = NEW.id AND id <> NEW.id;

    IF NEW.parent_id IS NOT NULL THEN
        SELECT id, parent_id, sector_id INTO parent_row FROM services WHERE id = NEW.parent_id;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Service parent introuvable' USING ERRCODE = 'check_violation';
        END IF;
        IF parent_row.parent_id IS NOT NULL THEN
            RAISE EXCEPTION 'Le service parent est lui-même un pôle (un seul niveau)' USING ERRCODE = 'check_violation';
        END IF;
        IF n_children > 0 THEN
            RAISE EXCEPTION 'Ce service a % pôle(s) : il ne peut pas être rattaché', n_children USING ERRCODE = 'check_violation';
        END IF;
        IF parent_row.sector_id IS DISTINCT FROM NEW.sector_id THEN
            RAISE EXCEPTION 'Le service parent doit appartenir au même secteur' USING ERRCODE = 'check_violation';
        END IF;
    END IF;

    IF TG_OP = 'UPDATE' AND n_children > 0 AND NEW.sector_id IS DISTINCT FROM OLD.sector_id THEN
        RAISE EXCEPTION 'Déplacez ou détachez d''abord ses % pôle(s)', n_children USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS services_check_hierarchy ON services;
CREATE TRIGGER services_check_hierarchy
    BEFORE INSERT OR UPDATE OF parent_id, sector_id ON services
    FOR EACH ROW EXECUTE FUNCTION services_check_hierarchy();

-- 2. Pôle Entrepreneuriat et Innovation ----------------------------------------
DO $$
DECLARE
    pole_fixed CONSTANT UUID := '5e1c0050-0000-4000-8000-00000000e1ab';
    key_value  TEXT;
    dde_id     UUID;
    dde_sector UUID;
    dde_parent UUID;
    dde_color  VARCHAR(7);
    n_match    INTEGER;
    pole_id    UUID;
BEGIN
    SELECT value INTO key_value FROM editorial_contents WHERE key = 'entrepreneurship.dde_service_id';
    IF key_value ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
        SELECT id, sector_id, parent_id, color INTO dde_id, dde_sector, dde_parent, dde_color FROM services WHERE id = key_value::uuid;
    END IF;

    IF dde_id IS NULL THEN
        -- « _ » : apostrophe droite ou typographique ; « veloppement » : évite la casse du « é »
        SELECT count(*) INTO n_match FROM services WHERE name ILIKE '%veloppement et de l_entrepreneuriat%';
        IF n_match = 1 THEN
            SELECT id, sector_id, parent_id, color INTO dde_id, dde_sector, dde_parent, dde_color FROM services
            WHERE name ILIKE '%veloppement et de l_entrepreneuriat%';
        ELSE
            RAISE NOTICE 'PEI : DDE non résolue (clé vide ou invalide, % service(s) correspondant au nom) — pôle non créé, rattachement à faire en backoffice', n_match;
            RETURN;
        END IF;
    END IF;

    IF dde_parent IS NOT NULL THEN
        RAISE NOTICE 'PEI : la DDE (%) est elle-même rattachée à un parent — pôle non créé', dde_id;
        RETURN;
    END IF;

    SELECT id INTO pole_id FROM services
    WHERE id = pole_fixed
       OR landing_path = '/entrepreneuriat'
       OR (sigle ILIKE 'PEI' AND sector_id IS NOT DISTINCT FROM dde_sector)
       OR name ILIKE 'p_le entrepreneuriat et innovation'
    ORDER BY (id = pole_fixed) DESC, (landing_path = '/entrepreneuriat') DESC NULLS LAST, created_at
    LIMIT 1;

    IF pole_id IS NULL THEN
        INSERT INTO services (id, sector_id, parent_id, name, name_en, name_ar, sigle, color,
                              landing_path, display_order, active)
        VALUES (pole_fixed, dde_sector, dde_id, 'Pôle Entrepreneuriat et Innovation',
                'Entrepreneurship and Innovation Hub', 'قطب ريادة الأعمال والابتكار', 'PEI', dde_color,
                '/entrepreneuriat', 0, TRUE);
        RAISE NOTICE 'PEI : pôle créé (%) sous la DDE (%)', pole_fixed, dde_id;
    ELSIF pole_id = dde_id THEN
        RAISE NOTICE 'PEI : le service trouvé est la DDE elle-même — rien à faire';
    ELSE
        UPDATE services
        SET parent_id    = COALESCE(parent_id, CASE WHEN sector_id IS NOT DISTINCT FROM dde_sector
                                                     AND NOT EXISTS (SELECT 1 FROM services c WHERE c.parent_id = pole_id)
                                                    THEN dde_id END),
            landing_path = COALESCE(landing_path, '/entrepreneuriat'),
            updated_at   = NOW()
        WHERE id = pole_id
          AND (parent_id IS NULL OR landing_path IS NULL);
        RAISE NOTICE 'PEI : pôle déjà présent (%) — complété si nécessaire, valeurs existantes conservées', pole_id;
    END IF;
END $$;

-- 3. Menu « Plus » › Nous connaître ---------------------------------------------
DO $$
DECLARE
    entry JSONB := jsonb_build_object(
        'id', 'entrepreneurship',
        'label', 'Entreprendre à Senghor',
        'label_en', 'Entrepreneurship at Senghor',
        'label_ar', 'ريادة الأعمال في سنغور',
        'route', '/entrepreneuriat',
        'icon', 'fa-solid fa-rocket');
    raw  TEXT;
    arr  JSONB;
    next_order INTEGER;
BEGIN
    SELECT value INTO raw FROM editorial_contents WHERE key = 'navbar.secondary.about.children';

    IF NOT FOUND OR raw IS NULL OR btrim(raw) = '' THEN
        INSERT INTO editorial_contents (key, value, value_type, category_id, description, admin_editable)
        VALUES ('navbar.secondary.about.children',
                jsonb_build_array(entry || '{"sort_order": 1}')::text, 'json',
                (SELECT id FROM editorial_categories WHERE code = 'values'),
                'Sous-items du menu secondaire "Nous connaitre"', TRUE)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
            WHERE editorial_contents.value IS NULL OR btrim(editorial_contents.value) = '';
        RAISE NOTICE 'Menu : liste « Nous connaître » créée avec l''entrée du pôle';
        RETURN;
    END IF;

    BEGIN
        arr := raw::jsonb;
    EXCEPTION WHEN others THEN
        RAISE NOTICE 'Menu : valeur de navbar.secondary.about.children illisible — non modifiée';
        RETURN;
    END;

    IF jsonb_typeof(arr) <> 'array' THEN
        RAISE NOTICE 'Menu : navbar.secondary.about.children n''est pas un tableau — non modifiée';
        RETURN;
    END IF;

    IF EXISTS (SELECT 1 FROM jsonb_array_elements(arr) e
               WHERE e->>'id' = 'entrepreneurship' OR e->>'route' = '/entrepreneuriat') THEN
        RAISE NOTICE 'Menu : entrée du pôle déjà présente — non modifiée';
        RETURN;
    END IF;

    SELECT COALESCE(max(CASE WHEN (e->>'sort_order') ~ '^-?[0-9]+$' THEN (e->>'sort_order')::int END), 0) + 1
    INTO next_order FROM jsonb_array_elements(arr) e;

    UPDATE editorial_contents
    SET value = (arr || jsonb_build_array(entry || jsonb_build_object('sort_order', next_order)))::text,
        updated_at = NOW()
    WHERE key = 'navbar.secondary.about.children';
    RAISE NOTICE 'Menu : entrée du pôle ajoutée (sort_order %)', next_order;
END $$;

-- 4. Lien court /r/pei -----------------------------------------------------------
INSERT INTO short_links (code, target_url, created_by)
VALUES ('pei', '/entrepreneuriat', NULL)
ON CONFLICT (code) DO NOTHING;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM short_links WHERE code = 'pei' AND target_url <> '/entrepreneuriat') THEN
        RAISE NOTICE 'Lien court : le code pei existe déjà vers une autre cible — non modifié';
    END IF;
END $$;

COMMIT;

\echo 'Migration 050_services_parent_landing terminée'
