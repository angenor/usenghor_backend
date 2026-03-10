-- Migration 020: Convertir les colonnes credits de INT à NUMERIC(5,1)
-- Permet les crédits ECTS décimaux (ex: 2.5)

BEGIN;

-- La vue v_programs_overview dépend de program_courses.credits, il faut la supprimer d'abord
DROP VIEW IF EXISTS v_programs_overview;

ALTER TABLE programs ALTER COLUMN credits TYPE NUMERIC(5, 1);
ALTER TABLE program_semesters ALTER COLUMN credits TYPE NUMERIC(5, 1);
ALTER TABLE program_courses ALTER COLUMN credits TYPE NUMERIC(5, 1);

-- Recréer la vue
CREATE VIEW v_programs_overview AS
SELECT p.id,
    p.code,
    p.title,
    p.subtitle,
    p.slug,
    p.description_legacy AS description,
    p.teaching_methods_legacy AS teaching_methods,
    p.cover_image_external_id,
    p.sector_external_id,
    p.coordinator_external_id,
    p.type,
    p.duration_months,
    p.credits,
    p.degree_awarded,
    p.required_degree,
    p.status,
    p.is_featured,
    p.display_order,
    p.created_at,
    p.updated_at,
    array_agg(DISTINCT pc.campus_external_id) FILTER (WHERE pc.campus_external_id IS NOT NULL) AS campus_ids
FROM programs p
    LEFT JOIN program_campuses pc ON p.id = pc.program_id
GROUP BY p.id;

COMMIT;
