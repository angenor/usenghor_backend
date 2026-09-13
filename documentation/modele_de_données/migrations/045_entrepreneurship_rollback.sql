-- =============================================================================
-- Rollback migration 045 : Socle du Pôle Entrepreneuriat et Innovation (PEI)
-- =============================================================================
-- Supprime uniquement ce que la migration 045 a créé : tables et types pei_*,
-- permissions entrepreneurship.* (et leurs attributions), clés éditoriales
-- entrepreneurship.* (l'historique suit par ON DELETE CASCADE).
-- ATTENTION : les dispositifs, cohortes et ressources saisis sont perdus.
-- =============================================================================

BEGIN;

DROP TABLE IF EXISTS pei_resources;
DROP TABLE IF EXISTS pei_cohorts;
DROP TABLE IF EXISTS pei_programs;

DROP TYPE IF EXISTS pei_resource_type;
DROP TYPE IF EXISTS pei_cohort_type;
DROP TYPE IF EXISTS pei_program_phase;

DELETE FROM role_permissions
WHERE permission_id IN (SELECT id FROM permissions WHERE code LIKE 'entrepreneurship.%');
DELETE FROM permissions WHERE code LIKE 'entrepreneurship.%';

DELETE FROM editorial_contents WHERE key LIKE 'entrepreneurship.%';

COMMIT;

\echo 'Rollback 045_entrepreneurship terminé'
