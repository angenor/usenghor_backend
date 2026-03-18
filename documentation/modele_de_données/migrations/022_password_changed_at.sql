-- Migration 022: Ajout de password_changed_at pour l'invalidation des sessions JWT
-- après réinitialisation de mot de passe

ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ;

COMMENT ON COLUMN users.password_changed_at IS 'Timestamp du dernier changement de mot de passe. Comparé au iat du JWT pour invalider les sessions antérieures.';
