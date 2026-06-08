-- =============================================================================
-- Migration 038 : Traduction automatique FR → EN/AR du domaine ACADEMIC / APPLICATION
-- =============================================================================
-- Contexte :
--   - Le contenu dynamique (programs + program_semesters/program_courses,
--     application_calls + 4 sous-tables) était monolingue en base.
--   - Convention ADDITIVE (cf. MIGRATION_TRADUCTION_AUTO.md §2) : la colonne FR
--     existante reste la source, on AJOUTE les variantes _en/_ar. Pour le rich
--     text, le suffixe de langue s'insère AVANT _html/_md
--     (description_html → description_en_html).
--   - Migration purement additive (ADD COLUMN IF NOT EXISTS), toutes NULL :
--     la lecture FR existante ne change pas, aucun backfill.
--   - Les variantes traduites des champs COURTS (title/subtitle/…) sont en TEXT
--     (et non VARCHAR(n) comme la source FR) : une traduction n'a aucune garantie
--     de longueur (FR→EN/AR peut dépasser la source) → évite un DataError au flush
--     qui rendrait la sauvegarde bloquante.
--   - Cas JSONB : programs.objectives / programs.target_audience sont des LISTES.
--     Les variantes objectives_en/ar et target_audience_en/ar sont aussi JSONB ;
--     la traduction se fait élément par élément côté service (translate_string_list),
--     jamais sur le JSON brut.
--
-- Périmètre traduit :
--   programs              : title, subtitle (text) ; description, teaching_methods,
--                           format, evaluation_methods (rich : paires _html/_md) ;
--                           required_degree (text) ; objectives, target_audience
--                           (JSONB, listes).
--   program_semesters     : title (text)
--   program_courses       : title, description (text)
--   application_calls     : title (text) ; description, target_audience (rich)
--                           ⚠ target_audience est RICH ici (≠ JSONB de programs)
--   call_eligibility_criteria : criterion (text)
--   call_coverage         : item, description (text)
--   call_required_documents   : document_name, description (text)
--   call_schedule         : step, description (text)
-- Jamais traduits : code, slug, degree_awarded, credits, number,
--   location_address, IDs externes, statuts/enums, dates, montants, coordonnées,
--   display_order. (program_fields / program_skills / program_career_opportunities
--   et les candidatures soumises = HORS périmètre.)
-- =============================================================================

BEGIN;

-- 1. programs -----------------------------------------------------------------
--    title/subtitle/required_degree = court ; description/teaching_methods/
--    format/evaluation_methods = rich (paires _html/_md) ;
--    objectives/target_audience = listes JSONB.
ALTER TABLE programs
    ADD COLUMN IF NOT EXISTS title_en                    TEXT,
    ADD COLUMN IF NOT EXISTS title_ar                    TEXT,
    ADD COLUMN IF NOT EXISTS subtitle_en                 TEXT,
    ADD COLUMN IF NOT EXISTS subtitle_ar                 TEXT,
    ADD COLUMN IF NOT EXISTS description_en_html         TEXT,
    ADD COLUMN IF NOT EXISTS description_en_md           TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_html         TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_md           TEXT,
    ADD COLUMN IF NOT EXISTS teaching_methods_en_html    TEXT,
    ADD COLUMN IF NOT EXISTS teaching_methods_en_md      TEXT,
    ADD COLUMN IF NOT EXISTS teaching_methods_ar_html    TEXT,
    ADD COLUMN IF NOT EXISTS teaching_methods_ar_md      TEXT,
    ADD COLUMN IF NOT EXISTS format_en_html              TEXT,
    ADD COLUMN IF NOT EXISTS format_en_md                TEXT,
    ADD COLUMN IF NOT EXISTS format_ar_html              TEXT,
    ADD COLUMN IF NOT EXISTS format_ar_md                TEXT,
    ADD COLUMN IF NOT EXISTS evaluation_methods_en_html  TEXT,
    ADD COLUMN IF NOT EXISTS evaluation_methods_en_md    TEXT,
    ADD COLUMN IF NOT EXISTS evaluation_methods_ar_html  TEXT,
    ADD COLUMN IF NOT EXISTS evaluation_methods_ar_md    TEXT,
    ADD COLUMN IF NOT EXISTS required_degree_en          TEXT,
    ADD COLUMN IF NOT EXISTS required_degree_ar          TEXT,
    ADD COLUMN IF NOT EXISTS objectives_en               JSONB,
    ADD COLUMN IF NOT EXISTS objectives_ar               JSONB,
    ADD COLUMN IF NOT EXISTS target_audience_en          JSONB,
    ADD COLUMN IF NOT EXISTS target_audience_ar          JSONB;

-- 2. program_semesters --------------------------------------------------------
--    title = court.
ALTER TABLE program_semesters
    ADD COLUMN IF NOT EXISTS title_en TEXT,
    ADD COLUMN IF NOT EXISTS title_ar TEXT;

-- 3. program_courses ----------------------------------------------------------
--    title + description = court (description est un TEXT plain, pas du rich).
ALTER TABLE program_courses
    ADD COLUMN IF NOT EXISTS title_en       TEXT,
    ADD COLUMN IF NOT EXISTS title_ar       TEXT,
    ADD COLUMN IF NOT EXISTS description_en TEXT,
    ADD COLUMN IF NOT EXISTS description_ar TEXT;

-- 4. application_calls --------------------------------------------------------
--    title = court ; description et target_audience = rich (paires _html/_md).
--    ⚠ target_audience est RICH ici, contrairement au JSONB de programs.
ALTER TABLE application_calls
    ADD COLUMN IF NOT EXISTS title_en                   TEXT,
    ADD COLUMN IF NOT EXISTS title_ar                   TEXT,
    ADD COLUMN IF NOT EXISTS description_en_html        TEXT,
    ADD COLUMN IF NOT EXISTS description_en_md          TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_html        TEXT,
    ADD COLUMN IF NOT EXISTS description_ar_md          TEXT,
    ADD COLUMN IF NOT EXISTS target_audience_en_html    TEXT,
    ADD COLUMN IF NOT EXISTS target_audience_en_md      TEXT,
    ADD COLUMN IF NOT EXISTS target_audience_ar_html    TEXT,
    ADD COLUMN IF NOT EXISTS target_audience_ar_md      TEXT;

-- 5. call_eligibility_criteria ------------------------------------------------
--    criterion = court.
ALTER TABLE call_eligibility_criteria
    ADD COLUMN IF NOT EXISTS criterion_en TEXT,
    ADD COLUMN IF NOT EXISTS criterion_ar TEXT;

-- 6. call_coverage ------------------------------------------------------------
--    item + description = court.
ALTER TABLE call_coverage
    ADD COLUMN IF NOT EXISTS item_en        TEXT,
    ADD COLUMN IF NOT EXISTS item_ar        TEXT,
    ADD COLUMN IF NOT EXISTS description_en TEXT,
    ADD COLUMN IF NOT EXISTS description_ar TEXT;

-- 7. call_required_documents --------------------------------------------------
--    document_name + description = court. accepted_formats reste en FR.
ALTER TABLE call_required_documents
    ADD COLUMN IF NOT EXISTS document_name_en TEXT,
    ADD COLUMN IF NOT EXISTS document_name_ar TEXT,
    ADD COLUMN IF NOT EXISTS description_en    TEXT,
    ADD COLUMN IF NOT EXISTS description_ar    TEXT;

-- 8. call_schedule ------------------------------------------------------------
--    step + description = court. dates restent inchangées.
ALTER TABLE call_schedule
    ADD COLUMN IF NOT EXISTS step_en        TEXT,
    ADD COLUMN IF NOT EXISTS step_ar        TEXT,
    ADD COLUMN IF NOT EXISTS description_en TEXT,
    ADD COLUMN IF NOT EXISTS description_ar TEXT;

-- 9. Vue v_programs_overview --------------------------------------------------
--    Définie en SELECT p.* : PostgreSQL fige la liste de colonnes à la création
--    → on la recrée pour qu'elle expose les nouvelles colonnes traduites
--    (convention projet, cf. migration 035). Définition identique à 99_views.sql.
DROP VIEW IF EXISTS v_programs_overview;
CREATE VIEW v_programs_overview AS
SELECT
    p.*,
    ARRAY_AGG(DISTINCT pc.campus_external_id) FILTER (WHERE pc.campus_external_id IS NOT NULL) as campus_ids
FROM programs p
LEFT JOIN program_campuses pc ON p.id = pc.program_id
GROUP BY p.id;

COMMIT;
