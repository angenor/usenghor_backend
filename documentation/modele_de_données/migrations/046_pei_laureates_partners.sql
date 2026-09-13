-- =============================================================================
-- Migration 046 : Portraits (lauréats FSE, étudiants-entrepreneurs) et
--                 partenaires du pôle PEI
-- =============================================================================
-- Contexte :
--   Feature 022-pei-laureates-partners. Étend le socle PEI (045) avec les
--   portraits de lauréats / étudiants-entrepreneurs rattachés à une cohorte, et
--   le rattachement de partenaires existants (table partners) à l'une des trois
--   familles du pôle. Schéma de référence : services/16_entrepreneurship.sql.
--
-- Effets :
--   1. Types ENUM pei_laureate_type, pei_partner_family
--   2. Tables pei_laureates, pei_partners (+ index, triggers updated_at)
--   3. Rattachement initial des partenaires du cahier des charges, s'ils
--      existent déjà dans partners (aucun partenaire n'est créé)
--   4. Renumérotation contiguë de l'ordre par famille
--
-- Dépendances : 045_entrepreneurship.sql (pei_cohorts), table partners.
-- Rejouable : types gardés, IF NOT EXISTS, ON CONFLICT DO NOTHING (la famille
-- choisie par un éditeur n'est jamais écrasée).
-- Aucune permission ni clé éditoriale : entrepreneurship.* existent depuis 045.
--
-- Rollback : 046_pei_laureates_partners_rollback.sql (à jouer AVANT le rollback 045)
-- =============================================================================

BEGIN;

-- 1. Types ENUM
DO $$ BEGIN
    CREATE TYPE pei_laureate_type AS ENUM ('fse_laureate', 'student_entrepreneur');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE pei_partner_family AS ENUM ('academic', 'support', 'international');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 2. Tables et index
-- Portraits : lauréats du FSE et étudiants-entrepreneurs
CREATE TABLE IF NOT EXISTS pei_laureates (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cohort_id           UUID NOT NULL REFERENCES pei_cohorts(id) ON DELETE RESTRICT,
    type                pei_laureate_type NOT NULL,
    full_name           VARCHAR(200) NOT NULL,
    project_name        VARCHAR(200) NOT NULL,
    department_label    VARCHAR(200),
    department_label_en VARCHAR(200),
    department_label_ar VARCHAR(200),
    quote               TEXT,
    quote_en            TEXT,
    quote_ar            TEXT,
    photo_external_id   UUID,                          -- → MEDIA.media.id (sans FK)
    website_url         VARCHAR(500),
    linkedin_url        VARCHAR(500),
    instagram_url       VARCHAR(500),
    facebook_url        VARCHAR(500),
    video_url           VARCHAR(500),
    grant_amount        NUMERIC(10,2),                 -- euros
    is_featured         BOOLEAN      NOT NULL DEFAULT FALSE,
    is_published        BOOLEAN      NOT NULL DEFAULT FALSE,
    published_at        TIMESTAMPTZ,
    display_order       INTEGER      NOT NULL DEFAULT 0,   -- relatif à la cohorte
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by          UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_pei_laureates_full_name    CHECK (char_length(full_name) >= 2),
    CONSTRAINT chk_pei_laureates_project_name CHECK (char_length(project_name) >= 2),
    CONSTRAINT chk_pei_laureates_quote_len    CHECK (
        (quote    IS NULL OR char_length(quote)    <= 600) AND
        (quote_en IS NULL OR char_length(quote_en) <= 600) AND
        (quote_ar IS NULL OR char_length(quote_ar) <= 600)),
    CONSTRAINT chk_pei_laureates_grant        CHECK (grant_amount IS NULL OR grant_amount >= 0)
);

CREATE INDEX IF NOT EXISTS idx_pei_laureates_cohort_order   ON pei_laureates (cohort_id, display_order);
CREATE INDEX IF NOT EXISTS idx_pei_laureates_published_type ON pei_laureates (is_published, type);

-- Partenaires du pôle : rattachement + famille
CREATE TABLE IF NOT EXISTS pei_partners (
    partner_id     UUID PRIMARY KEY REFERENCES partners(id) ON DELETE CASCADE,
    family         pei_partner_family NOT NULL,
    display_order  INTEGER     NOT NULL DEFAULT 0,       -- relatif à la famille
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by     UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by     UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pei_partners_family_order ON pei_partners (family, display_order);

COMMENT ON TABLE pei_laureates IS '[PEI] Portraits de lauréats FSE et d''étudiants-entrepreneurs (ordre relatif à la cohorte).';
COMMENT ON TABLE pei_partners  IS '[PEI] Rattachement d''un partenaire (table partners) à une famille du pôle (ordre relatif à la famille).';

-- 3. Triggers updated_at
DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['pei_laureates', 'pei_partners'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_' || t || '_updated_at') THEN
            EXECUTE format(
                'CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON %I
                 FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', t, t);
        END IF;
    END LOOP;
END $$;

-- 4. Rattachement initial des partenaires du cahier des charges (research R13)
--    Motifs insensibles à la casse ; « . » absorbe un accent ou une apostrophe
--    typographique. Au plus UN partenaire par motif (la prod contient des doublons,
--    ex. deux fiches OIF) : le plus complet (actif, logo, description, ancienneté).
--    Aucun rattachement si un partenaire du motif est déjà rattaché : la famille et
--    le choix faits par un éditeur ne sont jamais écrasés.
DO $$
DECLARE
    spec RECORD;
    n    INTEGER;
BEGIN
    FOR spec IN
        SELECT * FROM (VALUES
            ('academic',      0, 'r.seau senghor'),
            ('academic',      1, 'campus france'),
            ('support',       0, '\mCEF\M'),
            ('support',       1, '\mCCI\M|chambre de commerce'),
            ('international', 0, '\mAUF\M|agence universitaire de la francophonie'),
            ('international', 1, '\mAFD\M|agence fran.aise de d.veloppement'),
            ('international', 2, '\mOIF\M|organisation internationale de la francophonie')
        ) AS t(family, rank, pattern)
    LOOP
        INSERT INTO pei_partners (partner_id, family, display_order)
        SELECT p.id, spec.family::pei_partner_family, spec.rank
        FROM partners p
        WHERE p.name ~* spec.pattern
          AND NOT EXISTS (
              SELECT 1 FROM pei_partners pp
              JOIN partners linked ON linked.id = pp.partner_id
              WHERE linked.name ~* spec.pattern)
        ORDER BY p.active DESC,
                 (p.logo_external_id IS NOT NULL) DESC,
                 (p.description IS NOT NULL) DESC,
                 p.created_at
        LIMIT 1
        ON CONFLICT (partner_id) DO NOTHING;
        GET DIAGNOSTICS n = ROW_COUNT;
        IF n = 0 THEN
            RAISE NOTICE 'pei_partners : aucun partenaire (nouveau) pour le motif « % » (famille %)',
                spec.pattern, spec.family;
        END IF;
    END LOOP;
END $$;

-- 5. Renumérotation contiguë par famille (les rangs fixes ci-dessus peuvent laisser des trous)
WITH ranked AS (
    SELECT partner_id,
           ROW_NUMBER() OVER (PARTITION BY family ORDER BY display_order, created_at) - 1 AS rn
    FROM pei_partners
)
UPDATE pei_partners pp
SET display_order = r.rn
FROM ranked r
WHERE pp.partner_id = r.partner_id
  AND pp.display_order <> r.rn;

COMMIT;

\echo 'Migration 046_pei_laureates_partners terminée'
