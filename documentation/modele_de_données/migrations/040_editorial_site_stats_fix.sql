-- =============================================================================
-- Migration 040 : Correction des statistiques de la page Site / Campus (prod)
-- =============================================================================
-- Contexte :
--   La migration 039 a rendu fonctionnels les libellés de statistiques de la
--   page /siege. En production, deux valeurs avaient été saisies dans les
--   champs « Label Surface » et « Label Fondation » alors qu'il s'agit de
--   VALEURS et non de libellés :
--
--     site.presentation.stats.surface.label = « 33500 »
--     site.presentation.stats.founded.label = « Ouvert en 2025 »
--
--   Ces saisies n'étaient jusqu'ici jamais affichées (c'est le bug corrigé).
--   Les renommer telles quelles ferait apparaître « 33500 » comme libellé sous
--   le chiffre 33500, et « Ouvert en 2025 » sous l'année 1990.
--
--   Cette migration les replace donc au bon endroit :
--     - Surface   : la valeur 33500 est DÉJÀ le chiffre-clé stats_site_surface.
--                   L'entrée libellé est simplement supprimée ; le libellé
--                   revient à sa traduction « Surface totale ».
--     - Fondation : la valeur 2025 devient le chiffre-clé stats_site_founded
--                   (éditable dans /admin/editorial/chiffres-cles) et le
--                   libellé devient « Ouvert en » → rendu « 2025 / Ouvert en ».
--
--   Ces deux contenus restent modifiables depuis le backoffice.
--
-- À exécuter APRÈS la migration 039. Idempotente.
-- =============================================================================

BEGIN;

-- 1. Supprimer les libellés mal saisis (039 a pu les renommer sans le suffixe)
DELETE FROM editorial_contents
WHERE key IN (
        'site.presentation.stats.surface.label',
        'site.presentation.stats.founded.label'
      )
   OR (key = 'site.presentation.stats.surface' AND value = '33500')
   OR (key = 'site.presentation.stats.founded' AND value = 'Ouvert en 2025');

-- 2. Chiffre-clé « Année de fondation » : la valeur extraite de la saisie
INSERT INTO editorial_contents (key, value, value_type, description)
VALUES ('stats_site_founded', '2025', 'number', 'Année de création de l''université')
ON CONFLICT (key) DO NOTHING;

-- 3. Libellé associé, dans la catégorie éditoriale des valeurs de page
INSERT INTO editorial_contents (key, value, value_type, category_id, description)
SELECT 'site.presentation.stats.founded', 'Ouvert en', 'text',
       (SELECT id FROM editorial_categories WHERE code = 'values'),
       'Libellé de la statistique année de fondation (page Site / Campus)'
ON CONFLICT (key) DO NOTHING;

COMMIT;
