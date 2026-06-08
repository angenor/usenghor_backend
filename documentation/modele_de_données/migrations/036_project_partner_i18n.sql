-- =============================================================================
-- Migration 036 : Traduction automatique FR → EN/AR du domaine PROJECT / PARTNER
-- =============================================================================
-- Contexte :
--   - Le contenu dynamique (partners, project_categories, projects, project_calls)
--     était monolingue en base.
--   - On adopte la convention ADDITIVE (cf. MIGRATION_TRADUCTION_AUTO.md §2) :
--     la colonne FR existante reste la source, on AJOUTE les variantes _en/_ar.
--     Pour le rich text, le suffixe de langue s'insère avant _html / _md
--     (description_html → description_en_html).
--   - Migration purement additive (ADD COLUMN IF NOT EXISTS), toutes NULL :
--     la lecture FR existante ne change pas, aucun backfill.
--   - Les variantes traduites des champs COURTS (name/title) sont en TEXT (et
--     non VARCHAR(n) comme la source FR) : une traduction n'a aucune garantie
--     de longueur (FR→EN/AR peut dépasser la source) → évite un DataError au
--     flush qui rendrait la sauvegarde bloquante.
--
-- Périmètre traduit :
--   partners           : description            (name = NON traduit : raison sociale)
--   project_categories : name, description
--   projects           : title, summary (rich), description (rich)
--   project_calls      : title, description (rich), conditions (rich)
-- Jamais traduits : slug, icon, IDs externes, type, status, dates, budget,
--   currency, website, email, phone, display_order.
-- =============================================================================

BEGIN;

-- 1. partners -----------------------------------------------------------------
--    name reste en FR (raison sociale / nom propre), seul description est traduit.
ALTER TABLE partners
    ADD COLUMN IF NOT EXISTS description_en TEXT,
    ADD COLUMN IF NOT EXISTS description_ar TEXT;

-- 2. project_categories -------------------------------------------------------
ALTER TABLE project_categories
    ADD COLUMN IF NOT EXISTS name_en        TEXT,
    ADD COLUMN IF NOT EXISTS name_ar        TEXT,
    ADD COLUMN IF NOT EXISTS description_en TEXT,
    ADD COLUMN IF NOT EXISTS description_ar TEXT;

-- 3. projects -----------------------------------------------------------------
--    title = court ; summary et description = rich (paire _html/_md).
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS title_en           TEXT,
    ADD COLUMN IF NOT EXISTS title_ar           TEXT,
    ADD COLUMN IF NOT EXISTS summary_en_html    TEXT,
    ADD COLUMN IF NOT EXISTS summary_en_md      TEXT,
    ADD COLUMN IF NOT EXISTS summary_ar_html    TEXT,
    ADD COLUMN IF NOT EXISTS summary_ar_md      TEXT,
    ADD COLUMN IF NOT EXISTS description_en_html TEXT,
    ADD COLUMN IF NOT EXISTS description_en_md   TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_html TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_md   TEXT;

-- 4. project_calls ------------------------------------------------------------
--    title = court ; description et conditions = rich (paire _html/_md).
ALTER TABLE project_calls
    ADD COLUMN IF NOT EXISTS title_en            TEXT,
    ADD COLUMN IF NOT EXISTS title_ar            TEXT,
    ADD COLUMN IF NOT EXISTS description_en_html TEXT,
    ADD COLUMN IF NOT EXISTS description_en_md   TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_html TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_md   TEXT,
    ADD COLUMN IF NOT EXISTS conditions_en_html  TEXT,
    ADD COLUMN IF NOT EXISTS conditions_en_md    TEXT,
    ADD COLUMN IF NOT EXISTS conditions_ar_html  TEXT,
    ADD COLUMN IF NOT EXISTS conditions_ar_md    TEXT;

COMMIT;
