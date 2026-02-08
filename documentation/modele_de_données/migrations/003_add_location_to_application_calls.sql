-- ============================================================================
-- Migration: Ajouter pays et adresse aux appels à candidature
-- Date: 2026-02-08
-- Description: Ajout des colonnes country_external_id (référence vers
--              CORE.countries) et location_address (adresse exacte du lieu
--              de la formation ou de l'exercice) dans application_calls.
-- ============================================================================

-- IMPORTANT: Faire une sauvegarde AVANT d'exécuter cette migration !
-- ./deploy.sh backup

BEGIN;

-- 1) Ajouter la colonne pays (référence inter-service vers CORE.countries)
ALTER TABLE application_calls
    ADD COLUMN IF NOT EXISTS country_external_id UUID;

COMMENT ON COLUMN application_calls.country_external_id
    IS 'Référence inter-service → CORE.countries.id – Pays du lieu de formation/exercice';

-- 2) Ajouter la colonne adresse exacte
ALTER TABLE application_calls
    ADD COLUMN IF NOT EXISTS location_address TEXT;

COMMENT ON COLUMN application_calls.location_address
    IS 'Adresse exacte du lieu de formation ou d''exercice';

-- 3) Index sur le pays pour faciliter les filtres
CREATE INDEX IF NOT EXISTS idx_application_calls_country
    ON application_calls(country_external_id);

COMMIT;
