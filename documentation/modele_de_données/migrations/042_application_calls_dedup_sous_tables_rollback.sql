-- =============================================================================
-- Rollback de la migration 042 : Dédoublonnage des sous-tables des appels
-- =============================================================================
-- Réinsère les lignes archivées dans les tables `*_dedup_backup`, puis
-- supprime ces tables d'archivage.
--
-- Note : la ré-association des candidatures (`application_documents.
-- required_document_id`) vers le document conservé n'est PAS annulée — le
-- document conservé est strictement équivalent (même appel, même contenu).
-- =============================================================================

BEGIN;

INSERT INTO call_eligibility_criteria
SELECT * FROM call_eligibility_criteria_dedup_backup
ON CONFLICT (id) DO NOTHING;

INSERT INTO call_coverage
SELECT * FROM call_coverage_dedup_backup
ON CONFLICT (id) DO NOTHING;

INSERT INTO call_required_documents
SELECT * FROM call_required_documents_dedup_backup
ON CONFLICT (id) DO NOTHING;

INSERT INTO call_schedule
SELECT * FROM call_schedule_dedup_backup
ON CONFLICT (id) DO NOTHING;

DROP TABLE IF EXISTS call_eligibility_criteria_dedup_backup;
DROP TABLE IF EXISTS call_coverage_dedup_backup;
DROP TABLE IF EXISTS call_required_documents_dedup_backup;
DROP TABLE IF EXISTS call_schedule_dedup_backup;

COMMIT;
