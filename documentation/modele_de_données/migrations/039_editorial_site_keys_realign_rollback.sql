-- =============================================================================
-- Rollback migration 039 : clés éditoriales de la page Site / Campus
-- =============================================================================
-- Restaure le suffixe « .label » sur les libellés de statistiques.
-- Les clés « site.facility.pool.* » supprimées ne sont pas restaurables
-- (aucune section d'administration ni rendu public ne les utilisait).
-- =============================================================================

BEGIN;

UPDATE editorial_contents ec
SET key = ec.key || '.label'
WHERE ec.key IN (
        'site.presentation.stats.surface',
        'site.presentation.stats.rooms',
        'site.presentation.stats.capacity',
        'site.presentation.stats.founded'
      )
  AND NOT EXISTS (
        SELECT 1 FROM editorial_contents t WHERE t.key = ec.key || '.label'
      );

COMMIT;
