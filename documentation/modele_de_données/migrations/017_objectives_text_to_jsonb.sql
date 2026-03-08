-- Migration 017: Convertir programs.objectives de TEXT vers JSONB (tableau de chaînes)
-- ============================================================================

ALTER TABLE programs
    ALTER COLUMN objectives TYPE JSONB
    USING CASE
        WHEN objectives IS NULL THEN NULL
        WHEN objectives ~ '^\s*\[' THEN objectives::JSONB
        ELSE jsonb_build_array(objectives)
    END;

COMMENT ON COLUMN programs.objectives IS '[ACADEMIC] Liste des objectifs du programme (JSONB array)';
