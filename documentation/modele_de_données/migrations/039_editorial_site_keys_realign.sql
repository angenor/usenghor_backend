-- =============================================================================
-- Migration 039 : Réalignement des clés éditoriales de la page Site / Campus
-- =============================================================================
-- Contexte :
--   La configuration du backoffice (/admin/editorial/valeurs → « Page Site /
--   Campus ») déclarait pour les libellés de statistiques des clés suffixées
--   « .label » alors que la page publique /siege lit les clés SANS suffixe
--   (qui sont aussi celles des traductions i18n de repli). Résultat : toute
--   valeur saisie dans l'admin était enregistrée sous une clé que le
--   front-office ne consultait jamais.
--
--   Le code a été aligné sur les clés lues par la page (sans « .label »).
--   Cette migration renomme les valeurs déjà saisies pour ne pas les perdre.
--
--   Elle supprime par ailleurs les clés de l'installation « Piscine », retirée
--   des données du site : aucune section d'administration ni aucun rendu public
--   n'y correspond plus.
--
-- Idempotente : rejouable sans effet de bord.
-- =============================================================================

BEGIN;

-- 1. Libellés de statistiques : « site.presentation.stats.X.label » → « ...X »
--    On ne renomme que si la clé cible est libre ; sinon la valeur suffixée est
--    un doublon obsolète et est supprimée.
UPDATE editorial_contents ec
SET key = regexp_replace(ec.key, '\.label$', '')
WHERE ec.key IN (
        'site.presentation.stats.surface.label',
        'site.presentation.stats.rooms.label',
        'site.presentation.stats.capacity.label',
        'site.presentation.stats.founded.label'
      )
  AND NOT EXISTS (
        SELECT 1 FROM editorial_contents t
        WHERE t.key = regexp_replace(ec.key, '\.label$', '')
      );

DELETE FROM editorial_contents
WHERE key IN (
        'site.presentation.stats.surface.label',
        'site.presentation.stats.rooms.label',
        'site.presentation.stats.capacity.label',
        'site.presentation.stats.founded.label'
      );

-- 2. Installation « Piscine » : clés orphelines (plus aucune section ni rendu)
DELETE FROM editorial_contents
WHERE key LIKE 'site.facility.pool.%';

COMMIT;
