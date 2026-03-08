-- Migration 016: Convertir programs.target_audience de TEXT vers JSONB (tableau de chaînes)
-- ============================================================================

ALTER TABLE programs
    ALTER COLUMN target_audience TYPE JSONB
    USING CASE
        WHEN target_audience IS NULL THEN NULL
        WHEN target_audience ~ '^\s*\[' THEN target_audience::JSONB
        ELSE jsonb_build_array(target_audience)
    END;

COMMENT ON COLUMN programs.target_audience IS '[ACADEMIC] Liste du public cible du programme (JSONB array)';
