-- =============================================================================
-- Rollback Migration 037 : retire les colonnes i18n du domaine ORGANIZATION / CAMPUS
-- =============================================================================
-- ATTENTION : DROP COLUMN détruit les traductions EN/AR stockées.
--             À n'exécuter qu'en connaissance de cause.
-- =============================================================================

BEGIN;

ALTER TABLE campuses
    DROP COLUMN IF EXISTS name_en,
    DROP COLUMN IF EXISTS name_ar,
    DROP COLUMN IF EXISTS description_en_html,
    DROP COLUMN IF EXISTS description_en_md,
    DROP COLUMN IF EXISTS description_ar_html,
    DROP COLUMN IF EXISTS description_ar_md;

ALTER TABLE sectors
    DROP COLUMN IF EXISTS name_en,
    DROP COLUMN IF EXISTS name_ar,
    DROP COLUMN IF EXISTS description_en_html,
    DROP COLUMN IF EXISTS description_en_md,
    DROP COLUMN IF EXISTS description_ar_html,
    DROP COLUMN IF EXISTS description_ar_md,
    DROP COLUMN IF EXISTS mission_en_html,
    DROP COLUMN IF EXISTS mission_en_md,
    DROP COLUMN IF EXISTS mission_ar_html,
    DROP COLUMN IF EXISTS mission_ar_md;

ALTER TABLE services
    DROP COLUMN IF EXISTS name_en,
    DROP COLUMN IF EXISTS name_ar,
    DROP COLUMN IF EXISTS description_en_html,
    DROP COLUMN IF EXISTS description_en_md,
    DROP COLUMN IF EXISTS description_ar_html,
    DROP COLUMN IF EXISTS description_ar_md,
    DROP COLUMN IF EXISTS mission_en_html,
    DROP COLUMN IF EXISTS mission_en_md,
    DROP COLUMN IF EXISTS mission_ar_html,
    DROP COLUMN IF EXISTS mission_ar_md;

ALTER TABLE service_objectives
    DROP COLUMN IF EXISTS title_en,
    DROP COLUMN IF EXISTS title_ar,
    DROP COLUMN IF EXISTS description_en_html,
    DROP COLUMN IF EXISTS description_en_md,
    DROP COLUMN IF EXISTS description_ar_html,
    DROP COLUMN IF EXISTS description_ar_md;

ALTER TABLE service_achievements
    DROP COLUMN IF EXISTS title_en,
    DROP COLUMN IF EXISTS title_ar,
    DROP COLUMN IF EXISTS description_en_html,
    DROP COLUMN IF EXISTS description_en_md,
    DROP COLUMN IF EXISTS description_ar_html,
    DROP COLUMN IF EXISTS description_ar_md;

ALTER TABLE service_projects
    DROP COLUMN IF EXISTS title_en,
    DROP COLUMN IF EXISTS title_ar,
    DROP COLUMN IF EXISTS description_en_html,
    DROP COLUMN IF EXISTS description_en_md,
    DROP COLUMN IF EXISTS description_ar_html,
    DROP COLUMN IF EXISTS description_ar_md;

COMMIT;
