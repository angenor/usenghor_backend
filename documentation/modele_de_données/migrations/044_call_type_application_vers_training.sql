-- =============================================================================
-- Migration 044 : Type d'appel « Candidature » → « Formation »
-- =============================================================================
-- Contexte :
--   Le type d'appel `application` (« Candidature ») fait doublon avec le type
--   `training` (« Formation ») : tous les appels à candidature de l'Université
--   concernent en pratique une formation. Le type `application` est retiré des
--   filtres du site public et des formulaires du backoffice (option masquée).
--
--   La valeur `application` est conservée dans l'ENUM `call_type` (un
--   `DROP VALUE` n'existe pas en PostgreSQL et le retrait serait lourd pour un
--   gain nul) ; elle est simplement dépréciée : plus aucune ligne ne doit la
--   porter après cette migration.
--
-- Effets :
--   1. Sauvegarde des identifiants des lignes concernées dans
--      `migration_044_call_type_backup` (permet un rollback exact).
--   2. `application_calls.type` : `application` → `training`.
--   3. `project_calls.type`     : `application` → `training`.
--
-- Rollback : 044_call_type_application_vers_training_rollback.sql
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS migration_044_call_type_backup (
    table_name TEXT NOT NULL,
    row_id     UUID NOT NULL,
    PRIMARY KEY (table_name, row_id)
);

INSERT INTO migration_044_call_type_backup (table_name, row_id)
SELECT 'application_calls', id FROM application_calls WHERE type = 'application'
ON CONFLICT DO NOTHING;

INSERT INTO migration_044_call_type_backup (table_name, row_id)
SELECT 'project_calls', id FROM project_calls WHERE type = 'application'
ON CONFLICT DO NOTHING;

UPDATE application_calls
SET type = 'training', updated_at = NOW()
WHERE type = 'application';

UPDATE project_calls
SET type = 'training', updated_at = NOW()
WHERE type = 'application';

COMMIT;

-- Vérification (doit retourner 0 ligne pour les deux tables) :
-- SELECT 'application_calls' AS t, count(*) FROM application_calls WHERE type = 'application'
-- UNION ALL
-- SELECT 'project_calls', count(*) FROM project_calls WHERE type = 'application';
