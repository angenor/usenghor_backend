-- =============================================================================
-- Rollback 053 : Mini-site PEI sans tiret cadratin
-- =============================================================================
-- Restaure les textes seedés d'origine (avec tiret cadratin) UNIQUEMENT si la
-- valeur vaut encore exactement le texte posé par 053 (une saisie de l'équipe
-- n'est jamais écrasée) :
--   - pei_cohorts.focus des cohortes fse-1, fse-2, fse-3 ;
--   - editorial_contents entrepreneurship.see.closed.title ;
--   - pei_cohorts.focus_en / focus_ar sauvegardés dans `migration_053_backup`
--     (traductions automatiques), puis suppression de cette table.
-- ⚠ À exécuter AVANT tout rollback de numéro inférieur (052, 051, …).
-- Rejouable.
-- =============================================================================

BEGIN;

-- Focus FR des cohortes FSE
UPDATE pei_cohorts c
SET focus = t.old_value,
    updated_at = NOW()
FROM (VALUES
    ('fse-1',
     'Preuve de concept — projets en amorçage',
     'Preuve de concept : projets en amorçage'),
    ('fse-2',
     'Dimension intrapreneuriale — projets à fort impact social et technologique',
     'Dimension intrapreneuriale : projets à fort impact social et technologique'),
    ('fse-3',
     'Innovation et passage à l''échelle — projets incubés via Senghor''Innov',
     'Innovation et passage à l''échelle : projets incubés via Senghor''Innov')
) AS t(code, old_value, new_value)
WHERE c.code = t.code
  AND c.focus = t.new_value;

-- Titre « appel clos »
UPDATE editorial_contents
SET value = 'Appel clos — prochaine session',
    updated_at = NOW()
WHERE key = 'entrepreneurship.see.closed.title'
  AND value = 'Appel clos : prochaine session à venir';

-- Traductions automatiques EN / AR (si la table de sauvegarde existe encore)
DO $$
BEGIN
    IF to_regclass('public.migration_053_backup') IS NOT NULL THEN
        UPDATE pei_cohorts c
        SET focus_en = b.old_value,
            updated_at = NOW()
        FROM migration_053_backup b
        WHERE b.table_name = 'pei_cohorts'
          AND b.column_name = 'focus_en'
          AND b.row_key = c.code
          AND c.focus_en = b.new_value;

        UPDATE pei_cohorts c
        SET focus_ar = b.old_value,
            updated_at = NOW()
        FROM migration_053_backup b
        WHERE b.table_name = 'pei_cohorts'
          AND b.column_name = 'focus_ar'
          AND b.row_key = c.code
          AND c.focus_ar = b.new_value;
    END IF;
END $$;

DROP TABLE IF EXISTS migration_053_backup;

COMMIT;

\echo 'Rollback 053_pei_sans_tiret_cadratin terminé'
