-- =============================================================================
-- Rollback 048 : Clés éditoriales des pages alumni, partenaires, ressources
--                et actualités du mini-site PEI
-- =============================================================================
-- Indépendant de 046 et 047. Le rollback 045 (suppression de entrepreneurship.%)
-- couvre aussi ces clés : ce script n'est utile que si 045 reste en place.
-- =============================================================================

BEGIN;

DELETE FROM editorial_contents
WHERE key IN (
    'entrepreneurship.alumni.hero.badge',
    'entrepreneurship.alumni.hero.title',
    'entrepreneurship.alumni.hero.subtitle',
    'entrepreneurship.alumni.hero.image',
    'entrepreneurship.alumni.stats.1.value',
    'entrepreneurship.alumni.stats.1.label',
    'entrepreneurship.alumni.stats.2.value',
    'entrepreneurship.alumni.stats.2.label',
    'entrepreneurship.alumni.stats.3.value',
    'entrepreneurship.alumni.stats.3.label',
    'entrepreneurship.alumni.fse.badge',
    'entrepreneurship.alumni.fse.title',
    'entrepreneurship.alumni.see.badge',
    'entrepreneurship.alumni.see.title',
    'entrepreneurship.partners.hero.badge',
    'entrepreneurship.partners.hero.title',
    'entrepreneurship.partners.hero.subtitle',
    'entrepreneurship.partners.hero.image',
    'entrepreneurship.resources.hero.badge',
    'entrepreneurship.resources.hero.title',
    'entrepreneurship.resources.hero.subtitle',
    'entrepreneurship.resources.hero.image',
    'entrepreneurship.news.hero.badge',
    'entrepreneurship.news.hero.title',
    'entrepreneurship.news.hero.subtitle',
    'entrepreneurship.news.hero.image'
);

COMMIT;

\echo 'Rollback 048_pei_public_pages_keys terminé'
