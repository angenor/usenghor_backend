-- =============================================================================
-- Migration 037 : Traduction automatique FR → EN/AR du domaine ORGANIZATION / CAMPUS
-- =============================================================================
-- Contexte :
--   - Le contenu dynamique (sectors, services + sous-tables objectives/
--     achievements/projects, campuses) était monolingue en base.
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
--   campuses             : name, description (rich : paire description_html/_md)
--                          ⚠ la colonne legacy `description` (TEXT brut) reste
--                          INCHANGÉE et n'est PAS traduite. city/address = FR.
--   sectors              : name, description (rich), mission (rich)
--   services             : name, description (rich), mission (rich)
--                          ⚠ sigle (acronyme) = NON traduit
--   service_objectives   : title, description (rich)
--   service_achievements : title, description (rich)   [type = NON traduit]
--   service_projects     : title, description (rich)   [status = NON traduit]
-- Jamais traduits : slug, code, sigle, city, address, IDs externes, statuts/
--   enums, dates, coordonnées (email, phone), display_order. service_team /
--   campus_team exclus (position = rôle interne).
-- =============================================================================

BEGIN;

-- 1. campuses -----------------------------------------------------------------
--    name = court ; description = rich (paire _html/_md). La colonne legacy
--    `description` (TEXT) reste en FR et n'est pas dupliquée.
ALTER TABLE campuses
    ADD COLUMN IF NOT EXISTS name_en             TEXT,
    ADD COLUMN IF NOT EXISTS name_ar             TEXT,
    ADD COLUMN IF NOT EXISTS description_en_html TEXT,
    ADD COLUMN IF NOT EXISTS description_en_md   TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_html TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_md   TEXT;

-- 2. sectors ------------------------------------------------------------------
--    name = court ; description et mission = rich (paire _html/_md).
ALTER TABLE sectors
    ADD COLUMN IF NOT EXISTS name_en             TEXT,
    ADD COLUMN IF NOT EXISTS name_ar             TEXT,
    ADD COLUMN IF NOT EXISTS description_en_html TEXT,
    ADD COLUMN IF NOT EXISTS description_en_md   TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_html TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_md   TEXT,
    ADD COLUMN IF NOT EXISTS mission_en_html     TEXT,
    ADD COLUMN IF NOT EXISTS mission_en_md       TEXT,
    ADD COLUMN IF NOT EXISTS mission_ar_html     TEXT,
    ADD COLUMN IF NOT EXISTS mission_ar_md       TEXT;

-- 3. services -----------------------------------------------------------------
--    name = court ; description et mission = rich. sigle reste en FR.
ALTER TABLE services
    ADD COLUMN IF NOT EXISTS name_en             TEXT,
    ADD COLUMN IF NOT EXISTS name_ar             TEXT,
    ADD COLUMN IF NOT EXISTS description_en_html TEXT,
    ADD COLUMN IF NOT EXISTS description_en_md   TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_html TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_md   TEXT,
    ADD COLUMN IF NOT EXISTS mission_en_html     TEXT,
    ADD COLUMN IF NOT EXISTS mission_en_md       TEXT,
    ADD COLUMN IF NOT EXISTS mission_ar_html     TEXT,
    ADD COLUMN IF NOT EXISTS mission_ar_md       TEXT;

-- 4. service_objectives -------------------------------------------------------
--    title = court ; description = rich (paire _html/_md).
ALTER TABLE service_objectives
    ADD COLUMN IF NOT EXISTS title_en            TEXT,
    ADD COLUMN IF NOT EXISTS title_ar            TEXT,
    ADD COLUMN IF NOT EXISTS description_en_html TEXT,
    ADD COLUMN IF NOT EXISTS description_en_md   TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_html TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_md   TEXT;

-- 5. service_achievements -----------------------------------------------------
--    title = court ; description = rich. type reste en FR.
ALTER TABLE service_achievements
    ADD COLUMN IF NOT EXISTS title_en            TEXT,
    ADD COLUMN IF NOT EXISTS title_ar            TEXT,
    ADD COLUMN IF NOT EXISTS description_en_html TEXT,
    ADD COLUMN IF NOT EXISTS description_en_md   TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_html TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_md   TEXT;

-- 6. service_projects ---------------------------------------------------------
--    title = court ; description = rich. status reste un enum non traduit.
ALTER TABLE service_projects
    ADD COLUMN IF NOT EXISTS title_en            TEXT,
    ADD COLUMN IF NOT EXISTS title_ar            TEXT,
    ADD COLUMN IF NOT EXISTS description_en_html TEXT,
    ADD COLUMN IF NOT EXISTS description_en_md   TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_html TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_md   TEXT;

COMMIT;
