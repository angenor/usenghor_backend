-- =============================================================================
-- Migration 041 : Ordre d'affichage des partenaires d'une formation
-- =============================================================================
-- Contexte :
--   La table de liaison `program_partners` ne portait aucune colonne d'ordre.
--   Les partenaires affichés sur la page publique d'une formation
--   (/formations/{type}/{slug}) apparaissaient donc dans l'ordre non
--   déterministe renvoyé par PostgreSQL, sans possibilité de le maîtriser
--   depuis le backoffice.
--
--   Cette migration ajoute `display_order`, en suivant la convention du projet
--   (cf. `event_media_library`, `news_media_library`, `program_semesters`…),
--   ce qui permet le réordonnancement par glisser-déposer dans l'admin.
--
-- Idempotente : réexécutable sans effet de bord.
-- =============================================================================

BEGIN;

ALTER TABLE program_partners
    ADD COLUMN IF NOT EXISTS display_order INT DEFAULT 0;

-- Index de tri (lecture publique : partenaires d'une formation, ordonnés)
CREATE INDEX IF NOT EXISTS idx_program_partners_program_order
    ON program_partners (program_id, display_order);

-- Initialisation : ordre alphabétique des partenaires existants par formation,
-- afin de partir d'un état lisible plutôt que de tout laisser à 0.
WITH ordered AS (
    SELECT pp.program_id,
           pp.partner_external_id,
           ROW_NUMBER() OVER (
               PARTITION BY pp.program_id
               ORDER BY p.name NULLS LAST, pp.partner_external_id
           ) - 1 AS position
    FROM program_partners pp
    LEFT JOIN partners p ON p.id = pp.partner_external_id
)
UPDATE program_partners pp
SET display_order = ordered.position
FROM ordered
WHERE pp.program_id = ordered.program_id
  AND pp.partner_external_id = ordered.partner_external_id
  AND COALESCE(pp.display_order, 0) = 0;

COMMIT;
