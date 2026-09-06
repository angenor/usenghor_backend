-- =============================================================================
-- Rollback de la migration 041 : Ordre d'affichage des partenaires de formation
-- =============================================================================
-- Supprime la colonne `display_order` et son index sur `program_partners`.
-- Les associations programme ↔ partenaire elles-mêmes sont préservées.
-- =============================================================================

BEGIN;

DROP INDEX IF EXISTS idx_program_partners_program_order;

ALTER TABLE program_partners
    DROP COLUMN IF EXISTS display_order;

COMMIT;
