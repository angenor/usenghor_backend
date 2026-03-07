-- Migration 015: Convertir beneficiaries de TEXT vers JSONB (tableau de chaînes)
-- ============================================================================

-- Convertir la colonne beneficiaries de TEXT en JSONB
-- Les données existantes (texte simple) sont converties en tableau à un élément
ALTER TABLE projects
    ALTER COLUMN beneficiaries TYPE JSONB
    USING CASE
        WHEN beneficiaries IS NULL THEN NULL
        WHEN beneficiaries ~ '^\s*\[' THEN beneficiaries::JSONB
        ELSE jsonb_build_array(beneficiaries)
    END;

COMMENT ON COLUMN projects.beneficiaries IS '[PROJECT] Liste des bénéficiaires du projet (JSONB array)';
