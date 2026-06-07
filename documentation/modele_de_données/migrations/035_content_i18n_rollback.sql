-- =============================================================================
-- Rollback Migration 035 : retire les colonnes i18n du domaine CONTENT
-- =============================================================================
-- ATTENTION : DROP COLUMN détruit les traductions EN/AR stockées.
--             À n'exécuter qu'en connaissance de cause.
-- =============================================================================

BEGIN;

ALTER TABLE tags
    DROP COLUMN IF EXISTS name_en,
    DROP COLUMN IF EXISTS name_ar,
    DROP COLUMN IF EXISTS description_en,
    DROP COLUMN IF EXISTS description_ar;

ALTER TABLE news
    DROP COLUMN IF EXISTS title_en,
    DROP COLUMN IF EXISTS title_ar,
    DROP COLUMN IF EXISTS summary_en,
    DROP COLUMN IF EXISTS summary_ar,
    DROP COLUMN IF EXISTS content_en_html,
    DROP COLUMN IF EXISTS content_en_md,
    DROP COLUMN IF EXISTS content_ar_html,
    DROP COLUMN IF EXISTS content_ar_md;

ALTER TABLE events
    DROP COLUMN IF EXISTS title_en,
    DROP COLUMN IF EXISTS title_ar,
    DROP COLUMN IF EXISTS description_en,
    DROP COLUMN IF EXISTS description_ar,
    DROP COLUMN IF EXISTS content_en_html,
    DROP COLUMN IF EXISTS content_en_md,
    DROP COLUMN IF EXISTS content_ar_html,
    DROP COLUMN IF EXISTS content_ar_md;

COMMIT;
