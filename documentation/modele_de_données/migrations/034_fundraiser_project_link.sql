-- =============================================================================
-- Migration 034 : Association projet <-> levée de fonds + suppression du flag
--                 « fundraising featured »
-- =============================================================================
-- Contexte :
--   - Une « levée de fonds » (fundraisers) peut désormais être rattachée à un
--     projet (facultatif). Un projet peut avoir PLUSIEURS levées (historique
--     conservé) ; une levée appartient à au plus un projet.
--   - La période de la levée est portée par la levée elle-même (start_date /
--     end_date).
--   - L'ancien mécanisme de mise en avant (is_fundraising_featured /
--     fundraising_display_order sur projects) est supprimé : il est remplacé par
--     l'association projet <-> levée.
-- =============================================================================

BEGIN;

-- 1. fundraisers : colonnes d'association projet + période -------------------
ALTER TABLE fundraisers
    ADD COLUMN IF NOT EXISTS project_external_id UUID
        REFERENCES projects(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS start_date DATE,
    ADD COLUMN IF NOT EXISTS end_date DATE;

CREATE INDEX IF NOT EXISTS idx_fundraisers_project
    ON fundraisers(project_external_id)
    WHERE project_external_id IS NOT NULL;

COMMENT ON COLUMN fundraisers.project_external_id IS '[FUNDRAISING] Projet associé (facultatif) — un projet peut avoir plusieurs levées';
COMMENT ON COLUMN fundraisers.start_date IS '[FUNDRAISING] Début de la période de la levée';
COMMENT ON COLUMN fundraisers.end_date IS '[FUNDRAISING] Fin de la période de la levée';

-- 2. projects : suppression de l'ancien mécanisme « featured » ---------------
DROP INDEX IF EXISTS idx_projects_fundraising_featured;

ALTER TABLE projects
    DROP COLUMN IF EXISTS is_fundraising_featured,
    DROP COLUMN IF EXISTS fundraising_display_order;

COMMIT;
