-- =============================================================================
-- Rollback migration 040 : statistiques de la page Site / Campus
-- =============================================================================
-- Restaure les deux saisies d'origine sous leurs clés initiales et retire le
-- chiffre-clé ainsi que le libellé créés par la migration.
-- =============================================================================

BEGIN;

DELETE FROM editorial_contents
WHERE key = 'stats_site_founded' AND value = '2025';

DELETE FROM editorial_contents
WHERE key = 'site.presentation.stats.founded' AND value = 'Ouvert en';

INSERT INTO editorial_contents (key, value, value_type, category_id)
SELECT 'site.presentation.stats.surface.label', '33500', 'text',
       (SELECT id FROM editorial_categories WHERE code = 'values')
ON CONFLICT (key) DO NOTHING;

INSERT INTO editorial_contents (key, value, value_type, category_id)
SELECT 'site.presentation.stats.founded.label', 'Ouvert en 2025', 'text',
       (SELECT id FROM editorial_categories WHERE code = 'values')
ON CONFLICT (key) DO NOTHING;

COMMIT;
