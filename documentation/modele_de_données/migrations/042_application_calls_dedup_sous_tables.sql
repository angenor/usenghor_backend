-- =============================================================================
-- Migration 042 : Dédoublonnage des sous-tables des appels à candidature
-- =============================================================================
-- Contexte :
--   La sauvegarde d'un appel dans le backoffice reposait sur un cycle
--   « supprimer toutes les sous-entités, puis les recréer » en N requêtes
--   HTTP distinctes (critères d'éligibilité, prises en charge, documents
--   requis, calendrier). Chaque création déclenchant une traduction auto
--   FR → EN/AR (appel réseau lent), la moindre erreur en cours de route
--   (timeout nginx, 503 de rate limiting, nouvel essai de l'utilisateur)
--   laissait des lignes en double : l'ancienne non supprimée + la nouvelle,
--   ou deux créations successives. Ces doublons apparaissaient ensuite sur
--   le site public.
--
--   Le code a été remplacé par un endpoint atomique et idempotent
--   (PUT /api/admin/application-calls/{id}/details). Cette migration nettoie
--   les doublons déjà présents en base.
--
-- Règle de dédoublonnage :
--   Deux lignes sont des doublons si elles portent le même `call_id` et le
--   même contenu FR (et les mêmes attributs métier). On conserve UNE ligne
--   par groupe (la plus petite `display_order`, puis le plus petit `id`),
--   les autres sont archivées dans des tables `*_dedup_backup` avant
--   suppression, ce qui rend l'opération réversible (cf. rollback).
--
--   Pour `call_required_documents`, les candidatures qui référencent un
--   doublon (`application_documents.required_document_id`) sont d'abord
--   ré-associées à la ligne conservée.
--
-- Idempotente : réexécutable sans effet de bord.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Tables d'archivage (mêmes colonnes que les tables d'origine)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS call_eligibility_criteria_dedup_backup
    (LIKE call_eligibility_criteria INCLUDING DEFAULTS, PRIMARY KEY (id));
CREATE TABLE IF NOT EXISTS call_coverage_dedup_backup
    (LIKE call_coverage INCLUDING DEFAULTS, PRIMARY KEY (id));
CREATE TABLE IF NOT EXISTS call_required_documents_dedup_backup
    (LIKE call_required_documents INCLUDING DEFAULTS, PRIMARY KEY (id));
CREATE TABLE IF NOT EXISTS call_schedule_dedup_backup
    (LIKE call_schedule INCLUDING DEFAULTS, PRIMARY KEY (id));

-- -----------------------------------------------------------------------------
-- 1) Critères d'éligibilité
-- -----------------------------------------------------------------------------
WITH ranked AS (
    SELECT id,
           ROW_NUMBER() OVER (
               PARTITION BY call_id, criterion, is_mandatory
               ORDER BY display_order, id::text
           ) AS rn
    FROM call_eligibility_criteria
),
dups AS (SELECT id FROM ranked WHERE rn > 1),
archived AS (
    INSERT INTO call_eligibility_criteria_dedup_backup
    SELECT c.* FROM call_eligibility_criteria c JOIN dups USING (id)
    ON CONFLICT (id) DO NOTHING
)
DELETE FROM call_eligibility_criteria WHERE id IN (SELECT id FROM dups);

-- -----------------------------------------------------------------------------
-- 2) Prises en charge
-- -----------------------------------------------------------------------------
WITH ranked AS (
    SELECT id,
           ROW_NUMBER() OVER (
               PARTITION BY call_id, item, COALESCE(description, '')
               ORDER BY display_order, id::text
           ) AS rn
    FROM call_coverage
),
dups AS (SELECT id FROM ranked WHERE rn > 1),
archived AS (
    INSERT INTO call_coverage_dedup_backup
    SELECT c.* FROM call_coverage c JOIN dups USING (id)
    ON CONFLICT (id) DO NOTHING
)
DELETE FROM call_coverage WHERE id IN (SELECT id FROM dups);

-- -----------------------------------------------------------------------------
-- 3) Documents requis (avec ré-association des candidatures)
-- -----------------------------------------------------------------------------
CREATE TEMP TABLE _doc_dups ON COMMIT DROP AS
WITH ranked AS (
    SELECT id,
           FIRST_VALUE(id) OVER (
               PARTITION BY call_id, document_name, COALESCE(description, ''),
                            is_mandatory, COALESCE(accepted_formats, ''),
                            COALESCE(max_size_mb, -1)
               ORDER BY display_order, id::text
           ) AS keep_id,
           ROW_NUMBER() OVER (
               PARTITION BY call_id, document_name, COALESCE(description, ''),
                            is_mandatory, COALESCE(accepted_formats, ''),
                            COALESCE(max_size_mb, -1)
               ORDER BY display_order, id::text
           ) AS rn
    FROM call_required_documents
)
SELECT id, keep_id FROM ranked WHERE rn > 1;

-- Les documents déposés par les candidats pointent vers la ligne conservée.
UPDATE application_documents ad
SET required_document_id = d.keep_id
FROM _doc_dups d
WHERE ad.required_document_id = d.id;

INSERT INTO call_required_documents_dedup_backup
SELECT c.* FROM call_required_documents c JOIN _doc_dups d USING (id)
ON CONFLICT (id) DO NOTHING;

DELETE FROM call_required_documents WHERE id IN (SELECT id FROM _doc_dups);

-- -----------------------------------------------------------------------------
-- 4) Calendrier
-- -----------------------------------------------------------------------------
WITH ranked AS (
    SELECT id,
           ROW_NUMBER() OVER (
               PARTITION BY call_id, step, start_date, end_date,
                            COALESCE(description, '')
               ORDER BY display_order, id::text
           ) AS rn
    FROM call_schedule
),
dups AS (SELECT id FROM ranked WHERE rn > 1),
archived AS (
    INSERT INTO call_schedule_dedup_backup
    SELECT c.* FROM call_schedule c JOIN dups USING (id)
    ON CONFLICT (id) DO NOTHING
)
DELETE FROM call_schedule WHERE id IN (SELECT id FROM dups);

-- -----------------------------------------------------------------------------
-- 5) Renumérotation de l'ordre d'affichage (1..n, sans trous)
-- -----------------------------------------------------------------------------
WITH o AS (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY call_id ORDER BY display_order, id::text) AS pos
    FROM call_eligibility_criteria
)
UPDATE call_eligibility_criteria c SET display_order = o.pos FROM o WHERE c.id = o.id AND c.display_order <> o.pos;

WITH o AS (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY call_id ORDER BY display_order, id::text) AS pos
    FROM call_coverage
)
UPDATE call_coverage c SET display_order = o.pos FROM o WHERE c.id = o.id AND c.display_order <> o.pos;

WITH o AS (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY call_id ORDER BY display_order, id::text) AS pos
    FROM call_required_documents
)
UPDATE call_required_documents c SET display_order = o.pos FROM o WHERE c.id = o.id AND c.display_order <> o.pos;

WITH o AS (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY call_id ORDER BY display_order, id::text) AS pos
    FROM call_schedule
)
UPDATE call_schedule c SET display_order = o.pos FROM o WHERE c.id = o.id AND c.display_order <> o.pos;

COMMIT;

-- Bilan
SELECT 'call_eligibility_criteria' AS table_name, COUNT(*) AS doublons_archives FROM call_eligibility_criteria_dedup_backup
UNION ALL SELECT 'call_coverage', COUNT(*) FROM call_coverage_dedup_backup
UNION ALL SELECT 'call_required_documents', COUNT(*) FROM call_required_documents_dedup_backup
UNION ALL SELECT 'call_schedule', COUNT(*) FROM call_schedule_dedup_backup;
