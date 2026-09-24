-- =============================================================================
-- Rollback 051 : Chiffres d'impact et descriptions des familles de partenaires
--                du mini-site PEI
-- =============================================================================
-- Supprime les 9 clés ajoutées par 051 et restaure le texte d'impact seedé par
-- 045 UNIQUEMENT si entrepreneurship.impact.text vaut encore exactement le texte
-- posé par 051 (une saisie de l'équipe n'est jamais écrasée).
-- Le rollback 045 (suppression de entrepreneurship.%) couvre aussi ces clés :
-- ce script n'est utile que si 045 reste en place. Rejouable.
-- =============================================================================

BEGIN;

DELETE FROM editorial_contents
WHERE key IN (
    'entrepreneurship.impact.stats.1.value',
    'entrepreneurship.impact.stats.1.label',
    'entrepreneurship.impact.stats.2.value',
    'entrepreneurship.impact.stats.2.label',
    'entrepreneurship.impact.stats.3.value',
    'entrepreneurship.impact.stats.3.label',
    'entrepreneurship.partners.family.academic.description',
    'entrepreneurship.partners.family.support.description',
    'entrepreneurship.partners.family.international.description'
);

UPDATE editorial_contents
SET value = 'L''impact est déjà tangible : 100 étudiants ont bénéficié d''un accompagnement personnalisé, menant à la distinction de 12 lauréats. Nos actions de sensibilisation ont touché plus de 500 étudiants et alumni, créant une dynamique de réseau durable.',
    updated_at = NOW()
WHERE key = 'entrepreneurship.impact.text'
  AND value = 'Au-delà de l''accompagnement direct, nos actions de sensibilisation créent une dynamique de réseau durable et renforcent l''employabilité de nos diplômés par la voie de la création de valeur.';

COMMIT;

\echo 'Rollback 051_pei_impact_family_keys terminé'
