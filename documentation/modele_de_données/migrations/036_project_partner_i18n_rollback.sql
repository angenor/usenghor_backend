-- =============================================================================
-- Rollback Migration 036 : retire les colonnes i18n du domaine PROJECT / PARTNER
-- =============================================================================
-- ATTENTION : DROP COLUMN détruit les traductions EN/AR stockées.
--             À n'exécuter qu'en connaissance de cause.
-- =============================================================================

BEGIN;

ALTER TABLE partners
    DROP COLUMN IF EXISTS description_en,
    DROP COLUMN IF EXISTS description_ar;

ALTER TABLE project_categories
    DROP COLUMN IF EXISTS name_en,
    DROP COLUMN IF EXISTS name_ar,
    DROP COLUMN IF EXISTS description_en,
    DROP COLUMN IF EXISTS description_ar;

ALTER TABLE projects
    DROP COLUMN IF EXISTS title_en,
    DROP COLUMN IF EXISTS title_ar,
    DROP COLUMN IF EXISTS summary_en_html,
    DROP COLUMN IF EXISTS summary_en_md,
    DROP COLUMN IF EXISTS summary_ar_html,
    DROP COLUMN IF EXISTS summary_ar_md,
    DROP COLUMN IF EXISTS description_en_html,
    DROP COLUMN IF EXISTS description_en_md,
    DROP COLUMN IF EXISTS description_ar_html,
    DROP COLUMN IF EXISTS description_ar_md;

ALTER TABLE project_calls
    DROP COLUMN IF EXISTS title_en,
    DROP COLUMN IF EXISTS title_ar,
    DROP COLUMN IF EXISTS description_en_html,
    DROP COLUMN IF EXISTS description_en_md,
    DROP COLUMN IF EXISTS description_ar_html,
    DROP COLUMN IF EXISTS description_ar_md,
    DROP COLUMN IF EXISTS conditions_en_html,
    DROP COLUMN IF EXISTS conditions_en_md,
    DROP COLUMN IF EXISTS conditions_ar_html,
    DROP COLUMN IF EXISTS conditions_ar_md;

COMMIT;
