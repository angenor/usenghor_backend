-- =============================================================================
-- Rollback migration 046 : Portraits et partenaires du pôle PEI
-- =============================================================================
-- Supprime uniquement ce que la migration 046 a créé : tables pei_laureates,
-- pei_partners et leurs types. Les partenaires (table partners) sont intacts.
-- ATTENTION : les portraits et rattachements saisis sont perdus.
-- À jouer AVANT 045_entrepreneurship_rollback.sql (pei_laureates référence pei_cohorts).
-- =============================================================================

BEGIN;

DROP TABLE IF EXISTS pei_laureates;
DROP TABLE IF EXISTS pei_partners;

DROP TYPE IF EXISTS pei_laureate_type;
DROP TYPE IF EXISTS pei_partner_family;

COMMIT;

\echo 'Rollback 046_pei_laureates_partners terminé'
