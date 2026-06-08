-- =============================================================================
-- ROLLBACK Migration 038 : Traduction auto FR → EN/AR ACADEMIC / APPLICATION
-- =============================================================================
-- Supprime les colonnes _en/_ar additives et recrée la vue v_programs_overview
-- dans sa définition d'origine. Purement réversible (aucune donnée FR touchée).
-- =============================================================================

BEGIN;

ALTER TABLE programs
    DROP COLUMN IF EXISTS title_en,
    DROP COLUMN IF EXISTS title_ar,
    DROP COLUMN IF EXISTS subtitle_en,
    DROP COLUMN IF EXISTS subtitle_ar,
    DROP COLUMN IF EXISTS description_en_html,
    DROP COLUMN IF EXISTS description_en_md,
    DROP COLUMN IF EXISTS description_ar_html,
    DROP COLUMN IF EXISTS description_ar_md,
    DROP COLUMN IF EXISTS teaching_methods_en_html,
    DROP COLUMN IF EXISTS teaching_methods_en_md,
    DROP COLUMN IF EXISTS teaching_methods_ar_html,
    DROP COLUMN IF EXISTS teaching_methods_ar_md,
    DROP COLUMN IF EXISTS format_en_html,
    DROP COLUMN IF EXISTS format_en_md,
    DROP COLUMN IF EXISTS format_ar_html,
    DROP COLUMN IF EXISTS format_ar_md,
    DROP COLUMN IF EXISTS evaluation_methods_en_html,
    DROP COLUMN IF EXISTS evaluation_methods_en_md,
    DROP COLUMN IF EXISTS evaluation_methods_ar_html,
    DROP COLUMN IF EXISTS evaluation_methods_ar_md,
    DROP COLUMN IF EXISTS required_degree_en,
    DROP COLUMN IF EXISTS required_degree_ar,
    DROP COLUMN IF EXISTS objectives_en,
    DROP COLUMN IF EXISTS objectives_ar,
    DROP COLUMN IF EXISTS target_audience_en,
    DROP COLUMN IF EXISTS target_audience_ar;

ALTER TABLE program_semesters
    DROP COLUMN IF EXISTS title_en,
    DROP COLUMN IF EXISTS title_ar;

ALTER TABLE program_courses
    DROP COLUMN IF EXISTS title_en,
    DROP COLUMN IF EXISTS title_ar,
    DROP COLUMN IF EXISTS description_en,
    DROP COLUMN IF EXISTS description_ar;

ALTER TABLE application_calls
    DROP COLUMN IF EXISTS title_en,
    DROP COLUMN IF EXISTS title_ar,
    DROP COLUMN IF EXISTS description_en_html,
    DROP COLUMN IF EXISTS description_en_md,
    DROP COLUMN IF EXISTS description_ar_html,
    DROP COLUMN IF EXISTS description_ar_md,
    DROP COLUMN IF EXISTS target_audience_en_html,
    DROP COLUMN IF EXISTS target_audience_en_md,
    DROP COLUMN IF EXISTS target_audience_ar_html,
    DROP COLUMN IF EXISTS target_audience_ar_md;

ALTER TABLE call_eligibility_criteria
    DROP COLUMN IF EXISTS criterion_en,
    DROP COLUMN IF EXISTS criterion_ar;

ALTER TABLE call_coverage
    DROP COLUMN IF EXISTS item_en,
    DROP COLUMN IF EXISTS item_ar,
    DROP COLUMN IF EXISTS description_en,
    DROP COLUMN IF EXISTS description_ar;

ALTER TABLE call_required_documents
    DROP COLUMN IF EXISTS document_name_en,
    DROP COLUMN IF EXISTS document_name_ar,
    DROP COLUMN IF EXISTS description_en,
    DROP COLUMN IF EXISTS description_ar;

ALTER TABLE call_schedule
    DROP COLUMN IF EXISTS step_en,
    DROP COLUMN IF EXISTS step_ar,
    DROP COLUMN IF EXISTS description_en,
    DROP COLUMN IF EXISTS description_ar;

DROP VIEW IF EXISTS v_programs_overview;
CREATE VIEW v_programs_overview AS
SELECT
    p.*,
    ARRAY_AGG(DISTINCT pc.campus_external_id) FILTER (WHERE pc.campus_external_id IS NOT NULL) as campus_ids
FROM programs p
LEFT JOIN program_campuses pc ON p.id = pc.program_id
GROUP BY p.id;

COMMIT;
