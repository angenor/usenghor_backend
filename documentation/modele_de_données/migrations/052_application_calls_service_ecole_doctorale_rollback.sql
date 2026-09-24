-- =============================================================================
-- Rollback 052 : Rattachement appel ↔ service, fiche « École doctorale »
-- =============================================================================
-- Restaure les valeurs sauvegardées dans `migration_052_backup` (menu,
-- rattachement des programmes doctoraux, présentation de l'École doctorale),
-- puis supprime la colonne `application_calls.service_external_id`.
--
-- ⚠ Les rattachements appel ↔ service saisis depuis la migration sont perdus,
--   et une présentation de l'École doctorale retouchée depuis est remplacée par
--   sa valeur d'avant migration.
-- ⚠ À exécuter AVANT tout rollback de numéro inférieur (051, 050, …).
-- =============================================================================

BEGIN;

-- Menu « Se former »
UPDATE editorial_contents ec
SET value = b.payload ->> 'value',
    updated_at = NOW()
FROM migration_052_backup b
WHERE b.kind = 'navbar_training'
  AND ec.key = b.row_key;

-- Rattachement des programmes doctoraux
UPDATE programs p
SET service_external_id = (b.payload ->> 'service_external_id')::uuid,
    updated_at = NOW()
FROM migration_052_backup b
WHERE b.kind = 'program_service'
  AND p.id = b.row_key::uuid;

-- Présentation de l'École doctorale
UPDATE services s
SET description_html    = b.payload ->> 'description_html',
    description_md      = b.payload ->> 'description_md',
    description_en_html = b.payload ->> 'description_en_html',
    description_en_md   = b.payload ->> 'description_en_md',
    description_ar_html = b.payload ->> 'description_ar_html',
    description_ar_md   = b.payload ->> 'description_ar_md',
    updated_at          = NOW()
FROM migration_052_backup b
WHERE b.kind = 'service_description'
  AND s.id = b.row_key::uuid;

DROP INDEX IF EXISTS idx_application_calls_service;
ALTER TABLE application_calls DROP COLUMN IF EXISTS service_external_id;

DROP TABLE IF EXISTS migration_052_backup;

COMMIT;
