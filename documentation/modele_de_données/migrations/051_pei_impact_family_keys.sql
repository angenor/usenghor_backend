-- =============================================================================
-- Migration 051 : Chiffres d'impact et descriptions des familles de partenaires
--                 du mini-site PEI
-- =============================================================================
-- Contexte :
--   Refonte de l'accueil du pôle (/entrepreneuriat) selon la maquette validée :
--   le bloc « impact » affiche trois chiffres (valeur + libellé) au-dessus du
--   texte d'impact, et chaque famille de partenaires (accueil et page
--   /entrepreneuriat/partenaires) affiche une phrase de description sous son
--   titre. Valeurs FR du cahier des charges, modifiables dans
--   Admin → Valeurs → Entrepreneuriat (sections « Citation et impact » et
--   « Partenaires »).
--
-- Dépend de : 045_entrepreneurship.sql (catégorie values, clé
--   entrepreneurship.impact.text)
--
-- Effets :
--   - 9 lignes dans editorial_contents (138 → 147 lignes entrepreneurship.%) ;
--   - entrepreneurship.impact.text reçoit le nouveau texte du cahier des
--     charges UNIQUEMENT s'il vaut encore exactement la valeur seedée par 045
--     (une saisie de l'équipe n'est jamais écrasée).
--   Aucune table, colonne ni type nouveau.
--
-- Rejouable : ON CONFLICT (key) DO NOTHING ; la mise à jour du texte ne touche
-- plus aucune ligne au second passage.
--
-- Rollback : 051_pei_impact_family_keys_rollback.sql
-- =============================================================================

BEGIN;

INSERT INTO editorial_contents (key, value, value_type, category_id, description)
SELECT v.key, v.value, v.value_type::editorial_value_type,
       (SELECT id FROM editorial_categories WHERE code = 'values'), v.description
FROM (VALUES
    -- Accueil du pôle : trois chiffres du bloc impact
    ('entrepreneurship.impact.stats.1.value',
     '100', 'text',
     'Bloc impact de l''accueil du pôle — chiffre 1 (valeur)'),
    ('entrepreneurship.impact.stats.1.label',
     'étudiants accompagnés personnellement', 'text',
     'Bloc impact de l''accueil du pôle — chiffre 1 (libellé)'),
    ('entrepreneurship.impact.stats.2.value',
     '12', 'text',
     'Bloc impact de l''accueil du pôle — chiffre 2 (valeur)'),
    ('entrepreneurship.impact.stats.2.label',
     'lauréats aux projets prometteurs', 'text',
     'Bloc impact de l''accueil du pôle — chiffre 2 (libellé)'),
    ('entrepreneurship.impact.stats.3.value',
     '500+', 'text',
     'Bloc impact de l''accueil du pôle — chiffre 3 (valeur)'),
    ('entrepreneurship.impact.stats.3.label',
     'étudiants et alumni sensibilisés', 'text',
     'Bloc impact de l''accueil du pôle — chiffre 3 (libellé)'),
    -- Familles de partenaires : description sous le titre de chaque famille
    ('entrepreneurship.partners.family.academic.description',
     'Universités du réseau Senghor, Campus France.', 'text',
     'Description de la famille « Académiques et institutionnels » (accueil du pôle et page « Nos partenaires »)'),
    ('entrepreneurship.partners.family.support.description',
     'Incubateurs, accélérateurs et Chambres de Commerce et d''Industrie (CCI) africaines et francophones, notamment le Centre d''entrepreneuriat de la Francophonie (CEF).', 'text',
     'Description de la famille « Organisations d''appui » (accueil du pôle et page « Nos partenaires »)'),
    ('entrepreneurship.partners.family.international.description',
     'Agence Universitaire de la Francophonie (AUF), Agence Française de Développement (AFD) et Organisation Internationale de la Francophonie (OIF).', 'text',
     'Description de la famille « Organisations internationales » (accueil du pôle et page « Nos partenaires »)')
) AS v(key, value, value_type, description)
ON CONFLICT (key) DO NOTHING;

-- Texte d'impact : nouveau texte seulement si la valeur seedée par 045 est intacte
UPDATE editorial_contents
SET value = 'Au-delà de l''accompagnement direct, nos actions de sensibilisation créent une dynamique de réseau durable et renforcent l''employabilité de nos diplômés par la voie de la création de valeur.',
    updated_at = NOW()
WHERE key = 'entrepreneurship.impact.text'
  AND value = 'L''impact est déjà tangible : 100 étudiants ont bénéficié d''un accompagnement personnalisé, menant à la distinction de 12 lauréats. Nos actions de sensibilisation ont touché plus de 500 étudiants et alumni, créant une dynamique de réseau durable.';

COMMIT;

\echo 'Migration 051_pei_impact_family_keys terminée'
