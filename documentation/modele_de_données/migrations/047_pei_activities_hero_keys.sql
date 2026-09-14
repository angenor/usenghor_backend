-- =============================================================================
-- Migration 047 : Clés éditoriales du hero de la page « Nos activités » (PEI)
-- =============================================================================
-- Contexte :
--   Feature 023-pei-public-home-activities. La page publique
--   /entrepreneuriat/activites affiche un hero propre (badge, titre,
--   sous-titre, image) modifiable dans Admin → Valeurs → Entrepreneuriat,
--   section « Nos activités ».
--
-- Dépend de : 045_entrepreneurship.sql (catégorie values, clés entrepreneurship.*)
--
-- Effets : 4 lignes dans editorial_contents (44 → 48 clés entrepreneurship.*).
--   Aucune table, colonne ni type nouveau.
--
-- Rejouable : ON CONFLICT (key) DO NOTHING ; une valeur modifiée par un
-- éditeur n'est jamais écrasée.
--
-- Rollback : 047_pei_activities_hero_keys_rollback.sql
-- =============================================================================

BEGIN;

INSERT INTO editorial_contents (key, value, value_type, category_id, description)
SELECT v.key, v.value, v.value_type::editorial_value_type,
       (SELECT id FROM editorial_categories WHERE code = 'values'), v.description
FROM (VALUES
    ('entrepreneurship.activities.hero.badge',
     'Nos activités', 'text',
     'Badge du hero de la page « Nos activités » du mini-site PEI'),
    ('entrepreneurship.activities.hero.title',
     'Un parcours, de l''idée à l''entreprise', 'text',
     'Titre du hero de la page « Nos activités »'),
    ('entrepreneurship.activities.hero.subtitle',
     'Le PEI a structuré son intervention autour d''un parcours de croissance complet, conçu pour transformer une simple intuition en une entreprise viable et structurée.', 'text',
     'Sous-titre du hero de la page « Nos activités »'),
    ('entrepreneurship.activities.hero.image',
     '', 'text',
     'Image de fond du hero de la page « Nos activités » (identifiant de média ; vide = hero à motif)')
) AS v(key, value, value_type, description)
ON CONFLICT (key) DO NOTHING;

COMMIT;

\echo 'Migration 047_pei_activities_hero_keys terminée'
