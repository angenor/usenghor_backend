-- =============================================================================
-- Migration 035 : Traduction automatique FR → EN/AR du domaine CONTENT
-- =============================================================================
-- Contexte :
--   - Le contenu dynamique (tags, news, events) était monolingue en base.
--   - On adopte la convention ADDITIVE (cf. MIGRATION_TRADUCTION_AUTO.md §2) :
--     la colonne FR existante reste la source, on AJOUTE les variantes _en/_ar.
--     Pour le rich text, le suffixe de langue s'insère avant _html / _md
--     (content_html → content_en_html).
--   - Migration purement additive (ADD COLUMN IF NOT EXISTS), toutes NULL :
--     la lecture FR existante ne change pas, aucun backfill.
--
-- Périmètre traduit :
--   tags   : name, description
--   news   : title, summary, content (rich)
--   events : title, description, content (rich)   [venue/city restent en FR]
-- =============================================================================

BEGIN;

-- 1. tags ---------------------------------------------------------------------
ALTER TABLE tags
    ADD COLUMN IF NOT EXISTS name_en        VARCHAR(100),
    ADD COLUMN IF NOT EXISTS name_ar        VARCHAR(100),
    ADD COLUMN IF NOT EXISTS description_en TEXT,
    ADD COLUMN IF NOT EXISTS description_ar TEXT;

-- 2. news ---------------------------------------------------------------------
ALTER TABLE news
    ADD COLUMN IF NOT EXISTS title_en        VARCHAR(255),
    ADD COLUMN IF NOT EXISTS title_ar        VARCHAR(255),
    ADD COLUMN IF NOT EXISTS summary_en      TEXT,
    ADD COLUMN IF NOT EXISTS summary_ar      TEXT,
    ADD COLUMN IF NOT EXISTS content_en_html TEXT,
    ADD COLUMN IF NOT EXISTS content_en_md   TEXT,
    ADD COLUMN IF NOT EXISTS content_ar_html TEXT,
    ADD COLUMN IF NOT EXISTS content_ar_md   TEXT;

-- 3. events -------------------------------------------------------------------
ALTER TABLE events
    ADD COLUMN IF NOT EXISTS title_en        VARCHAR(255),
    ADD COLUMN IF NOT EXISTS title_ar        VARCHAR(255),
    ADD COLUMN IF NOT EXISTS description_en  TEXT,
    ADD COLUMN IF NOT EXISTS description_ar  TEXT,
    ADD COLUMN IF NOT EXISTS content_en_html TEXT,
    ADD COLUMN IF NOT EXISTS content_en_md   TEXT,
    ADD COLUMN IF NOT EXISTS content_ar_html TEXT,
    ADD COLUMN IF NOT EXISTS content_ar_md   TEXT;

COMMIT;
