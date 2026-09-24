-- =============================================================================
-- Migration 052 : Rattachement appel ↔ service, fiche « École doctorale »
-- =============================================================================
-- Contexte :
--   La fiche publique d'un service (/a-propos/organisation/service/{slug})
--   gagne un onglet « Appels » alimenté par les appels à candidatures
--   rattachés au service. Le rattachement se saisit dans le backoffice des
--   appels (/admin/candidatures/appels), comme la formation ou le projet.
--
--   Cas de l'École doctorale : ses deux « formations » doctorales (édition
--   2025 et Cohorte 5) sont en réalité des textes d'appel. Le texte de la
--   Cohorte 5 (FR/EN/AR) devient la présentation du service ; les deux
--   programmes restent publiés au catalogue (/formations/doctorat) mais ne
--   sont plus rattachés au service, ce qui retire l'onglet « Formations » de
--   sa fiche. L'entrée « Se former › Doctorat » du menu pointe désormais vers
--   la fiche de l'École doctorale.
--
-- Effets :
--   1. `application_calls.service_external_id` (UUID, sans FK, convention
--      inter-service) + index `idx_application_calls_service`.
--   2. Sauvegarde des valeurs modifiées dans `migration_052_backup`.
--   3. `services.description_*` (École doctorale) ← `programs.description_*`
--      (Cohorte 5), uniquement si la description du service est vide.
--   4. `programs.service_external_id` → NULL pour les programmes doctoraux
--      rattachés à l'École doctorale.
--   5. `editorial_contents` `navbar.primary.training.children` : route de
--      l'entrée `doctorate` → /a-propos/organisation/service/ecole-doctorale.
--
--   Les étapes 3 à 5 ciblent des identifiants de production ; sans ces lignes
--   (base locale), elles ne modifient rien. Migration rejouable.
--
-- Rollback : 052_application_calls_service_ecole_doctorale_rollback.sql
-- =============================================================================

BEGIN;

-- 1. Colonne de rattachement ---------------------------------------------------
ALTER TABLE application_calls ADD COLUMN IF NOT EXISTS service_external_id UUID;
CREATE INDEX IF NOT EXISTS idx_application_calls_service
    ON application_calls(service_external_id);

COMMENT ON COLUMN application_calls.service_external_id IS
    '→ ORGANIZATION.services.id (onglet « Appels » de la fiche service)';

-- 2. Table de sauvegarde (rollback exact) -------------------------------------
CREATE TABLE IF NOT EXISTS migration_052_backup (
    kind    TEXT NOT NULL,  -- service_description | program_service | navbar_training
    row_key TEXT NOT NULL,
    payload JSONB,
    PRIMARY KEY (kind, row_key)
);

-- 3. Présentation de l'École doctorale ← texte de la Cohorte 5 -----------------
--    Service  bf766075-c7a8-4dc3-979b-c8cfa48df9d4 « École doctorale »
--    Programme 19e6d198-5f38-4489-b756-73ebd5993d17 « … - Cohorte 5 »
INSERT INTO migration_052_backup (kind, row_key, payload)
SELECT 'service_description', s.id::text, jsonb_build_object(
    'description_html',    s.description_html,
    'description_md',      s.description_md,
    'description_en_html', s.description_en_html,
    'description_en_md',   s.description_en_md,
    'description_ar_html', s.description_ar_html,
    'description_ar_md',   s.description_ar_md
)
FROM services s
JOIN programs p ON p.id = '19e6d198-5f38-4489-b756-73ebd5993d17'
WHERE s.id = 'bf766075-c7a8-4dc3-979b-c8cfa48df9d4'
  AND COALESCE(btrim(s.description_html), '') = ''
ON CONFLICT DO NOTHING;

UPDATE services s
SET description_html    = p.description_html,
    description_md      = p.description_md,
    description_en_html = p.description_en_html,
    description_en_md   = p.description_en_md,
    description_ar_html = p.description_ar_html,
    description_ar_md   = p.description_ar_md,
    updated_at          = NOW()
FROM programs p
WHERE s.id = 'bf766075-c7a8-4dc3-979b-c8cfa48df9d4'
  AND p.id = '19e6d198-5f38-4489-b756-73ebd5993d17'
  AND COALESCE(btrim(s.description_html), '') = '';

-- 4. Programmes doctoraux détachés de l'École doctorale -----------------------
INSERT INTO migration_052_backup (kind, row_key, payload)
SELECT 'program_service', p.id::text,
       jsonb_build_object('service_external_id', p.service_external_id)
FROM programs p
WHERE p.service_external_id = 'bf766075-c7a8-4dc3-979b-c8cfa48df9d4'
  AND p.type = 'doctorate'
ON CONFLICT DO NOTHING;

UPDATE programs
SET service_external_id = NULL,
    updated_at = NOW()
WHERE service_external_id = 'bf766075-c7a8-4dc3-979b-c8cfa48df9d4'
  AND type = 'doctorate';

-- 5. Menu « Se former › Doctorat » → fiche de l'École doctorale ---------------
INSERT INTO migration_052_backup (kind, row_key, payload)
SELECT 'navbar_training', ec.key, jsonb_build_object('value', ec.value)
FROM editorial_contents ec
WHERE ec.key = 'navbar.primary.training.children'
  AND ec.value IS NOT NULL
  AND ec.value ~ '^\s*\['
ON CONFLICT DO NOTHING;

UPDATE editorial_contents ec
SET value = (
        SELECT jsonb_agg(
                   CASE WHEN t.e ->> 'id' = 'doctorate'
                        THEN jsonb_set(t.e, '{route}', '"/a-propos/organisation/service/ecole-doctorale"')
                        ELSE t.e
                   END
                   ORDER BY t.ord
               )::text
        FROM jsonb_array_elements(ec.value::jsonb) WITH ORDINALITY AS t(e, ord)
    ),
    updated_at = NOW()
WHERE ec.key = 'navbar.primary.training.children'
  AND ec.value IS NOT NULL
  AND ec.value ~ '^\s*\['
  AND EXISTS (
        SELECT 1
        FROM jsonb_array_elements(ec.value::jsonb) AS x(e)
        WHERE x.e ->> 'id' = 'doctorate'
          AND x.e ->> 'route' IS DISTINCT FROM '/a-propos/organisation/service/ecole-doctorale'
  );

COMMIT;

-- Vérifications :
-- SELECT column_name FROM information_schema.columns
--  WHERE table_name = 'application_calls' AND column_name = 'service_external_id';
-- SELECT left(description_html, 120) FROM services WHERE id = 'bf766075-c7a8-4dc3-979b-c8cfa48df9d4';
-- SELECT id, title, service_external_id FROM programs WHERE type = 'doctorate';
-- SELECT e ->> 'route' FROM editorial_contents,
--        jsonb_array_elements(value::jsonb) e
--  WHERE key = 'navbar.primary.training.children' AND e ->> 'id' = 'doctorate';
