-- ============================================================================
-- Migration: Renommer sector_external_id en service_external_id dans events
-- Date: 2026-02-02
-- Description: Correction du schéma - les événements sont associés à des
--              services (pas des secteurs). Cette migration renomme la colonne
--              et l'index associé sans perdre de données.
-- ============================================================================

-- IMPORTANT: Faire une sauvegarde AVANT d'exécuter cette migration !
-- ./deploy.sh backup

-- ============================================================================
-- Étape 1: Renommer la colonne sector_external_id → service_external_id
-- ============================================================================
DO $$
BEGIN
    -- Vérifier si l'ancienne colonne existe
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'events'
        AND column_name = 'sector_external_id'
    ) THEN
        -- Renommer la colonne (préserve les données)
        ALTER TABLE events
        RENAME COLUMN sector_external_id TO service_external_id;

        RAISE NOTICE 'Colonne sector_external_id renommée en service_external_id';
    ELSIF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'events'
        AND column_name = 'service_external_id'
    ) THEN
        RAISE NOTICE 'La colonne service_external_id existe déjà - migration déjà appliquée';
    ELSE
        RAISE EXCEPTION 'Ni sector_external_id ni service_external_id n''existe dans la table events';
    END IF;
END $$;

-- ============================================================================
-- Étape 2: Renommer l'index idx_events_sector → idx_events_service
-- ============================================================================
DO $$
BEGIN
    -- Vérifier si l'ancien index existe
    IF EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE tablename = 'events'
        AND indexname = 'idx_events_sector'
    ) THEN
        -- Renommer l'index
        ALTER INDEX idx_events_sector RENAME TO idx_events_service;

        RAISE NOTICE 'Index idx_events_sector renommé en idx_events_service';
    ELSIF EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE tablename = 'events'
        AND indexname = 'idx_events_service'
    ) THEN
        RAISE NOTICE 'L''index idx_events_service existe déjà';
    ELSE
        -- L'index n'existe pas, le créer
        CREATE INDEX idx_events_service ON events(service_external_id);
        RAISE NOTICE 'Index idx_events_service créé';
    END IF;
END $$;

-- ============================================================================
-- Étape 3: Mettre à jour le commentaire
-- ============================================================================
COMMENT ON COLUMN events.service_external_id IS 'Référence externe vers ORGANIZATION.services.id';

-- ============================================================================
-- Vérification finale
-- ============================================================================
DO $$
DECLARE
    col_exists BOOLEAN;
    idx_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'events' AND column_name = 'service_external_id'
    ) INTO col_exists;

    SELECT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'events' AND indexname = 'idx_events_service'
    ) INTO idx_exists;

    IF col_exists AND idx_exists THEN
        RAISE NOTICE '✅ Migration réussie: colonne service_external_id et index idx_events_service présents';
    ELSE
        RAISE EXCEPTION '❌ Migration échouée: vérifier manuellement la table events';
    END IF;
END $$;

-- ============================================================================
-- Rollback (à exécuter manuellement si nécessaire)
-- ============================================================================
-- ALTER TABLE events RENAME COLUMN service_external_id TO sector_external_id;
-- ALTER INDEX idx_events_service RENAME TO idx_events_sector;
-- COMMENT ON COLUMN events.sector_external_id IS 'Référence externe vers ORGANIZATION.sectors.id';
