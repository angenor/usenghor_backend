-- =============================================================================
-- Rollback Migration 034 : Association projet <-> levée de fonds
-- =============================================================================
-- ATTENTION : restaure les colonnes is_fundraising_featured /
-- fundraising_display_order (valeurs perdues) et supprime l'association
-- projet <-> levée (project_external_id, start_date, end_date sur fundraisers).
-- =============================================================================

BEGIN;

-- 1. projects : restauration de l'ancien mécanisme « featured »
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS is_fundraising_featured BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS fundraising_display_order INT DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_projects_fundraising_featured
    ON projects(is_fundraising_featured)
    WHERE is_fundraising_featured = TRUE;

-- 2. fundraisers : suppression des colonnes d'association projet + période
DROP INDEX IF EXISTS idx_fundraisers_project;

ALTER TABLE fundraisers
    DROP COLUMN IF EXISTS project_external_id,
    DROP COLUMN IF EXISTS start_date,
    DROP COLUMN IF EXISTS end_date;

COMMIT;
