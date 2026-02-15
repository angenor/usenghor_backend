-- Migration 009: Ajouter campus_external_id et service_external_id aux programmes
-- Permet d'associer directement un campus et un service a un programme (comme pour les actualites)

ALTER TABLE programs ADD COLUMN IF NOT EXISTS campus_external_id UUID;
ALTER TABLE programs ADD COLUMN IF NOT EXISTS service_external_id UUID;

COMMENT ON COLUMN programs.campus_external_id IS 'Référence au campus associé (CAMPUS.campuses.id)';
COMMENT ON COLUMN programs.service_external_id IS 'Référence au service associé (ORGANIZATION.services.id)';
