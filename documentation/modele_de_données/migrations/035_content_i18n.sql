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
--   - Les variantes traduites des champs COURTS (name/title) sont en TEXT (et
--     non VARCHAR(n) comme la source FR) : une traduction n'a aucune garantie
--     de longueur (FR→EN/AR peut dépasser la source) → évite un DataError au
--     flush qui rendrait la sauvegarde bloquante.
--
-- Périmètre traduit :
--   tags   : name, description
--   news   : title, summary, content (rich)
--   events : title, description, content (rich)   [venue/city restent en FR]
-- =============================================================================

BEGIN;

-- 1. tags ---------------------------------------------------------------------
ALTER TABLE tags
    ADD COLUMN IF NOT EXISTS name_en        TEXT,
    ADD COLUMN IF NOT EXISTS name_ar        TEXT,
    ADD COLUMN IF NOT EXISTS description_en TEXT,
    ADD COLUMN IF NOT EXISTS description_ar TEXT;

-- 2. news ---------------------------------------------------------------------
ALTER TABLE news
    ADD COLUMN IF NOT EXISTS title_en        TEXT,
    ADD COLUMN IF NOT EXISTS title_ar        TEXT,
    ADD COLUMN IF NOT EXISTS summary_en      TEXT,
    ADD COLUMN IF NOT EXISTS summary_ar      TEXT,
    ADD COLUMN IF NOT EXISTS content_en_html TEXT,
    ADD COLUMN IF NOT EXISTS content_en_md   TEXT,
    ADD COLUMN IF NOT EXISTS content_ar_html TEXT,
    ADD COLUMN IF NOT EXISTS content_ar_md   TEXT;

-- 3. events -------------------------------------------------------------------
ALTER TABLE events
    ADD COLUMN IF NOT EXISTS title_en        TEXT,
    ADD COLUMN IF NOT EXISTS title_ar        TEXT,
    ADD COLUMN IF NOT EXISTS description_en  TEXT,
    ADD COLUMN IF NOT EXISTS description_ar  TEXT,
    ADD COLUMN IF NOT EXISTS content_en_html TEXT,
    ADD COLUMN IF NOT EXISTS content_en_md   TEXT,
    ADD COLUMN IF NOT EXISTS content_ar_html TEXT,
    ADD COLUMN IF NOT EXISTS content_ar_md   TEXT;

-- 4. Vues dépendantes (SELECT * fige la liste des colonnes à la création) ------
--    À recréer pour qu'elles exposent les nouvelles colonnes _en/_ar (convention
--    du projet, cf. migration 010). Aucun usage applicatif aujourd'hui, mais
--    maintient la cohérence prod vs schéma de référence (99_views.sql).
DROP VIEW IF EXISTS v_upcoming_events;
CREATE VIEW v_upcoming_events AS
SELECT *
FROM events
WHERE status = 'published'
AND start_date >= NOW()
ORDER BY start_date ASC;

DROP VIEW IF EXISTS v_published_news;
CREATE VIEW v_published_news AS
SELECT *
FROM news
WHERE status = 'published'
AND (visible_from IS NULL OR visible_from <= NOW())
ORDER BY published_at DESC;

COMMIT;
