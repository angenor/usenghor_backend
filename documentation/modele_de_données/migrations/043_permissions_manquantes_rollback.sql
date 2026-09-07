-- =============================================================================
-- Rollback de la migration 043 : Permissions manquantes
-- =============================================================================
-- Supprime les 22 permissions ajoutées. Les lignes `role_permissions`
-- associées sont supprimées en cascade (FK ON DELETE CASCADE).
-- =============================================================================

BEGIN;

DELETE FROM permissions WHERE code IN (
    'media.view', 'media.create', 'media.edit', 'media.delete',
    'dashboard.view',
    'editorial.create', 'editorial.delete',
    'applications.create', 'applications.edit', 'applications.delete',
    'newsletter.edit', 'newsletter.delete',
    'organization.view', 'organization.edit',
    'project.view', 'project.create', 'project.edit', 'project.delete',
    'fundraisers.view', 'fundraisers.create', 'fundraisers.edit', 'fundraisers.delete'
);

COMMIT;

\echo 'Rollback 043_permissions_manquantes terminé'
