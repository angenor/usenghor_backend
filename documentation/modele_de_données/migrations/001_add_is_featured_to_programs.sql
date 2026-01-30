-- ============================================================================
-- Migration: Ajout du champ is_featured à la table programs
-- Date: 2025-01-30
-- Description: Permet de marquer des formations comme "à la une" pour
--              les afficher sur la page d'accueil
-- ============================================================================

-- Vérifier si la colonne n'existe pas déjà avant de l'ajouter
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'programs'
        AND column_name = 'is_featured'
    ) THEN
        -- Ajouter la colonne is_featured
        ALTER TABLE programs
        ADD COLUMN is_featured BOOLEAN DEFAULT FALSE;

        -- Ajouter un commentaire
        COMMENT ON COLUMN programs.is_featured IS 'Formation mise à la une sur la page d''accueil';

        -- Créer un index partiel pour optimiser les requêtes
        CREATE INDEX idx_programs_featured ON programs(is_featured) WHERE is_featured = TRUE;

        RAISE NOTICE 'Colonne is_featured ajoutée à la table programs';
    ELSE
        RAISE NOTICE 'La colonne is_featured existe déjà dans la table programs';
    END IF;
END $$;

-- ============================================================================
-- Rollback (à exécuter manuellement si nécessaire)
-- ============================================================================
-- DROP INDEX IF EXISTS idx_programs_featured;
-- ALTER TABLE programs DROP COLUMN IF EXISTS is_featured;
