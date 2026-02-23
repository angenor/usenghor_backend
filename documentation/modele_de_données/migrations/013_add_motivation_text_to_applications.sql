-- Migration 013 : Ajout du champ motivation_text à la table applications
-- Utilisé pour les candidatures spontanées (enseignants, etc.)

ALTER TABLE applications ADD COLUMN IF NOT EXISTS motivation_text TEXT;
COMMENT ON COLUMN applications.motivation_text IS 'Lettre de motivation (candidatures spontanées)';
