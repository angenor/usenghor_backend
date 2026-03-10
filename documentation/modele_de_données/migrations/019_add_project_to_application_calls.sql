-- Migration 019: Ajouter project_external_id aux appels à candidature
-- Permet d'associer un appel à candidature à un projet institutionnel

ALTER TABLE application_calls ADD COLUMN project_external_id UUID;
CREATE INDEX idx_application_calls_project ON application_calls(project_external_id);
COMMENT ON COLUMN application_calls.project_external_id IS 'Référence externe vers PROJECT.projects.id';
