-- =============================================================================
-- Migration 048 : Clés éditoriales des pages alumni, partenaires, ressources
--                 et actualités du mini-site PEI
-- =============================================================================
-- Contexte :
--   Feature 024-pei-public-alumni-resources-news. Les pages publiques
--   /entrepreneuriat/{alumni,partenaires,ressources,actualites} affichent un
--   hero propre (badge, titre, sous-titre, image) ; la page alumni affiche en
--   plus un bandeau de trois chiffres et un titre de section par onglet.
--   Modifiables dans Admin → Valeurs → Entrepreneuriat.
--
-- Dépend de : 045_entrepreneurship.sql (catégorie values, clés entrepreneurship.*)
--
-- Effets : 26 lignes dans editorial_contents (48 → 74 lignes entrepreneurship.%).
--   Aucune table, colonne ni type nouveau.
--
-- Rejouable : ON CONFLICT (key) DO NOTHING ; une valeur modifiée par un
-- éditeur n'est jamais écrasée.
--
-- Rollback : 048_pei_public_pages_keys_rollback.sql
-- =============================================================================

BEGIN;

INSERT INTO editorial_contents (key, value, value_type, category_id, description)
SELECT v.key, v.value, v.value_type::editorial_value_type,
       (SELECT id FROM editorial_categories WHERE code = 'values'), v.description
FROM (VALUES
    -- Page « Nos alumni » : hero, bandeau de chiffres, titres de section
    ('entrepreneurship.alumni.hero.badge',
     'Portraits et témoignages', 'text',
     'Badge du hero de la page « Nos alumni » du mini-site PEI'),
    ('entrepreneurship.alumni.hero.title',
     'Nos alumni et lauréats', 'text',
     'Titre du hero de la page « Nos alumni »'),
    ('entrepreneurship.alumni.hero.subtitle',
     'Ils sont passés de l''idée au projet, puis du projet à l''entreprise. Découvrez les lauréats du Fonds de Soutien à l''Entrepreneuriat et les étudiants-entrepreneurs de Senghor.', 'text',
     'Sous-titre du hero de la page « Nos alumni »'),
    ('entrepreneurship.alumni.hero.image',
     '', 'text',
     'Image de fond du hero de la page « Nos alumni » (identifiant de média ; vide = hero à motif)'),
    ('entrepreneurship.alumni.stats.1.value',
     '15', 'text',
     'Bandeau alumni — chiffre 1 (valeur)'),
    ('entrepreneurship.alumni.stats.1.label',
     'projets financés depuis 2023', 'text',
     'Bandeau alumni — chiffre 1 (libellé)'),
    ('entrepreneurship.alumni.stats.2.value',
     '5 000 €', 'text',
     'Bandeau alumni — chiffre 2 (valeur)'),
    ('entrepreneurship.alumni.stats.2.label',
     'de subvention d''amorçage maximum', 'text',
     'Bandeau alumni — chiffre 2 (libellé)'),
    ('entrepreneurship.alumni.stats.3.value',
     '3', 'text',
     'Bandeau alumni — chiffre 3 (valeur)'),
    ('entrepreneurship.alumni.stats.3.label',
     'cohortes, dont les alumni sont mentors', 'text',
     'Bandeau alumni — chiffre 3 (libellé)'),
    ('entrepreneurship.alumni.fse.badge',
     'Lauréats FSE', 'text',
     'Badge de la section des lauréats FSE'),
    ('entrepreneurship.alumni.fse.title',
     'Portraits de lauréats et témoignages', 'text',
     'Titre de la section des lauréats FSE'),
    ('entrepreneurship.alumni.see.badge',
     'Étudiants entrepreneurs', 'text',
     'Badge de la section des étudiants-entrepreneurs'),
    ('entrepreneurship.alumni.see.title',
     'Portraits d''étudiants-entrepreneurs', 'text',
     'Titre de la section des étudiants-entrepreneurs'),
    -- Page « Nos partenaires » : hero
    ('entrepreneurship.partners.hero.badge',
     'Nos partenaires', 'text',
     'Badge du hero de la page « Nos partenaires » du mini-site PEI'),
    ('entrepreneurship.partners.hero.title',
     'Un écosystème d''appui', 'text',
     'Titre du hero de la page « Nos partenaires »'),
    ('entrepreneurship.partners.hero.subtitle',
     'Institutions académiques, organisations d''appui et organisations internationales : les partenaires qui accompagnent le Pôle Entrepreneuriat et Innovation.', 'text',
     'Sous-titre du hero de la page « Nos partenaires »'),
    ('entrepreneurship.partners.hero.image',
     '', 'text',
     'Image de fond du hero de la page « Nos partenaires » (identifiant de média ; vide = hero à motif)'),
    -- Page « Nos ressources » : hero
    ('entrepreneurship.resources.hero.badge',
     'Nos ressources', 'text',
     'Badge du hero de la page « Nos ressources » du mini-site PEI'),
    ('entrepreneurship.resources.hero.title',
     'Médiathèque et boîte à outils', 'text',
     'Titre du hero de la page « Nos ressources »'),
    ('entrepreneurship.resources.hero.subtitle',
     'Revivez les temps forts du pôle en images et retrouvez guides, formulaires et liens utiles pour structurer votre projet.', 'text',
     'Sous-titre du hero de la page « Nos ressources »'),
    ('entrepreneurship.resources.hero.image',
     '', 'text',
     'Image de fond du hero de la page « Nos ressources » (identifiant de média ; vide = hero à motif)'),
    -- Page « Actualités » : hero
    ('entrepreneurship.news.hero.badge',
     'Actualités', 'text',
     'Badge du hero de la page « Actualités » du mini-site PEI'),
    ('entrepreneurship.news.hero.title',
     'La vie du pôle', 'text',
     'Titre du hero de la page « Actualités »'),
    ('entrepreneurship.news.hero.subtitle',
     'Actualités, événements et temps forts du Pôle Entrepreneuriat et Innovation.', 'text',
     'Sous-titre du hero de la page « Actualités »'),
    ('entrepreneurship.news.hero.image',
     '', 'text',
     'Image de fond du hero de la page « Actualités » (identifiant de média ; vide = hero à motif)')
) AS v(key, value, value_type, description)
ON CONFLICT (key) DO NOTHING;

COMMIT;

\echo 'Migration 048_pei_public_pages_keys terminée'
