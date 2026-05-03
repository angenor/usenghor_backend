-- ============================================================================
-- Rollback migration 033 — FAQ
-- ============================================================================
-- Supprime les tables FAQ et leurs permissions associées.
-- Conserve la fonction `update_updated_at_column()` (partagée).
-- ============================================================================

BEGIN;

DROP TABLE IF EXISTS faq_entries;
DROP TABLE IF EXISTS faq_categories;

DELETE FROM role_permissions
WHERE permission_id IN (
    SELECT id FROM permissions WHERE code IN ('faq.view', 'faq.create', 'faq.edit', 'faq.delete')
);

DELETE FROM permissions WHERE code IN ('faq.view', 'faq.create', 'faq.edit', 'faq.delete');

COMMIT;
