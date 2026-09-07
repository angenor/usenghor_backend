-- =============================================================================
-- Rollback de la migration 044 : Type d'appel « Candidature » → « Formation »
-- =============================================================================
-- Restaure le type `application` sur les seules lignes qui le portaient avant
-- la migration (identifiants conservés dans `migration_044_call_type_backup`),
-- puis supprime la table de sauvegarde.
-- =============================================================================

BEGIN;

UPDATE application_calls ac
SET type = 'application', updated_at = NOW()
FROM migration_044_call_type_backup b
WHERE b.table_name = 'application_calls' AND b.row_id = ac.id;

UPDATE project_calls pc
SET type = 'application', updated_at = NOW()
FROM migration_044_call_type_backup b
WHERE b.table_name = 'project_calls' AND b.row_id = pc.id;

DROP TABLE IF EXISTS migration_044_call_type_backup;

COMMIT;
