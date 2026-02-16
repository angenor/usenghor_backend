-- Migration 010: Ajouter sigle et couleur aux services
-- Date: 2026-02-16

ALTER TABLE services ADD COLUMN IF NOT EXISTS sigle VARCHAR(50);
ALTER TABLE services ADD COLUMN IF NOT EXISTS color VARCHAR(7);

COMMENT ON COLUMN services.sigle IS 'Sigle / abréviation du service';
COMMENT ON COLUMN services.color IS 'Couleur du service (format hex, ex: #FF0000)';
