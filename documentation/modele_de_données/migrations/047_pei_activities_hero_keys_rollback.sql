-- =============================================================================
-- Rollback 047 : Clés éditoriales du hero de la page « Nos activités » (PEI)
-- =============================================================================
-- Indépendant de 046. Le rollback 045 (suppression de entrepreneurship.%)
-- couvre aussi ces clés : ce script n'est utile que si 045 reste en place.
-- =============================================================================

BEGIN;

DELETE FROM editorial_contents
WHERE key IN (
    'entrepreneurship.activities.hero.badge',
    'entrepreneurship.activities.hero.title',
    'entrepreneurship.activities.hero.subtitle',
    'entrepreneurship.activities.hero.image'
);

COMMIT;

\echo 'Rollback 047_pei_activities_hero_keys terminé'
