-- =============================================================================
-- Migration 053 : Mini-site PEI sans tiret cadratin
-- =============================================================================
-- Contexte :
--   Le mini-site public « Entrepreneuriat » (/entrepreneuriat/*) ne doit plus
--   afficher de tiret cadratin (U+2014), jugé typique d'un texte généré
--   automatiquement. Les textes seedés qui en contenaient sont reformulés avec
--   la ponctuation française usuelle (deux-points précédé d'une espace).
--
-- Dépend de : 045_entrepreneurship.sql (cohortes FSE), 049_pei_see_page.sql
--   (clé entrepreneurship.see.closed.title)
--
-- Effets :
--   1. pei_cohorts.focus des cohortes fse-1, fse-2, fse-3 : « X — Y » devient
--      « X : Y », UNIQUEMENT si la valeur est encore exactement celle seedée
--      par 045 (une saisie de l'équipe n'est jamais écrasée).
--   2. editorial_contents entrepreneurship.see.closed.title : « Appel clos —
--      prochaine session » devient « Appel clos : prochaine session à venir »,
--      sous la même condition d'égalité avec la valeur seedée par 049.
--   3. pei_cohorts.focus_en / focus_ar de ces trois cohortes, remplis par la
--      traduction automatique (« Traduire les champs manquants ») et donc
--      absents du SQL : le tiret (et les espaces qui l'entourent) devient
--      « : » (anglais « X: Y », arabe « X: Y »). Uniquement si le focus FR vaut
--      encore le texte seedé (avant ou après l'étape 1), signe que la
--      traduction n'a pas été retouchée à la main. Les valeurs d'origine sont
--      sauvegardées dans `migration_053_backup` pour un rollback exact.
--   Aucune table métier, colonne ni type nouveau. Les descriptions d'aide de
--   l'admin (editorial_contents.description) ne sont pas publiques et restent
--   inchangées.
--
-- Rejouable : après un premier passage, aucune valeur ne correspond plus aux
-- conditions (texte seedé d'origine, présence du tiret).
--
-- Rollback : 053_pei_sans_tiret_cadratin_rollback.sql
-- =============================================================================

BEGIN;

-- Table de sauvegarde des traductions automatiques modifiées -----------------
CREATE TABLE IF NOT EXISTS migration_053_backup (
    table_name  TEXT NOT NULL,
    row_key     TEXT NOT NULL,
    column_name TEXT NOT NULL,
    old_value   TEXT,
    new_value   TEXT,
    PRIMARY KEY (table_name, row_key, column_name)
);

-- Textes seedés : ancien → nouveau -------------------------------------------
CREATE TEMP TABLE tmp_053_cohort_focus (code TEXT PRIMARY KEY, old_value TEXT, new_value TEXT) ON COMMIT DROP;
INSERT INTO tmp_053_cohort_focus (code, old_value, new_value) VALUES
    ('fse-1',
     'Preuve de concept — projets en amorçage',
     'Preuve de concept : projets en amorçage'),
    ('fse-2',
     'Dimension intrapreneuriale — projets à fort impact social et technologique',
     'Dimension intrapreneuriale : projets à fort impact social et technologique'),
    ('fse-3',
     'Innovation et passage à l''échelle — projets incubés via Senghor''Innov',
     'Innovation et passage à l''échelle : projets incubés via Senghor''Innov');

-- 3. Traductions automatiques EN / AR des focus (sauvegarde puis correction) --
INSERT INTO migration_053_backup (table_name, row_key, column_name, old_value, new_value)
SELECT 'pei_cohorts', c.code, 'focus_en', c.focus_en,
       regexp_replace(c.focus_en, '\s*—\s*', ': ', 'g')
FROM pei_cohorts c
JOIN tmp_053_cohort_focus t ON t.code = c.code
WHERE c.focus IN (t.old_value, t.new_value)
  AND c.focus_en LIKE '%—%'
ON CONFLICT (table_name, row_key, column_name) DO NOTHING;

INSERT INTO migration_053_backup (table_name, row_key, column_name, old_value, new_value)
SELECT 'pei_cohorts', c.code, 'focus_ar', c.focus_ar,
       regexp_replace(c.focus_ar, '\s*—\s*', ': ', 'g')
FROM pei_cohorts c
JOIN tmp_053_cohort_focus t ON t.code = c.code
WHERE c.focus IN (t.old_value, t.new_value)
  AND c.focus_ar LIKE '%—%'
ON CONFLICT (table_name, row_key, column_name) DO NOTHING;

UPDATE pei_cohorts c
SET focus_en = b.new_value,
    updated_at = NOW()
FROM migration_053_backup b
WHERE b.table_name = 'pei_cohorts'
  AND b.column_name = 'focus_en'
  AND b.row_key = c.code
  AND c.focus_en = b.old_value;

UPDATE pei_cohorts c
SET focus_ar = b.new_value,
    updated_at = NOW()
FROM migration_053_backup b
WHERE b.table_name = 'pei_cohorts'
  AND b.column_name = 'focus_ar'
  AND b.row_key = c.code
  AND c.focus_ar = b.old_value;

-- 1. Focus FR des cohortes FSE (valeur seedée intacte uniquement) ------------
UPDATE pei_cohorts c
SET focus = t.new_value,
    updated_at = NOW()
FROM tmp_053_cohort_focus t
WHERE c.code = t.code
  AND c.focus = t.old_value;

-- 2. Titre « appel clos » de la page statut étudiant-entrepreneur ------------
UPDATE editorial_contents
SET value = 'Appel clos : prochaine session à venir',
    updated_at = NOW()
WHERE key = 'entrepreneurship.see.closed.title'
  AND value = 'Appel clos — prochaine session';

COMMIT;

\echo 'Migration 053_pei_sans_tiret_cadratin terminée'
