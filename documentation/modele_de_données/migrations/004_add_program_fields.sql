-- Migration 004: Ajout des champs disciplinaires pour les certificats
-- Date: 2026-02-08
-- Description: Crée la table program_fields et ajoute field_id dans programs

BEGIN;

-- 1) Créer la table program_fields
CREATE TABLE IF NOT EXISTS program_fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_program_fields_slug ON program_fields(slug);

COMMENT ON TABLE program_fields IS '[ACADEMIC] Champs disciplinaires pour les certificats';

-- 2) Ajouter field_id dans programs (nullable, uniquement pour les certificats)
ALTER TABLE programs
    ADD COLUMN IF NOT EXISTS field_id UUID REFERENCES program_fields(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_programs_field ON programs(field_id);

COMMENT ON COLUMN programs.field_id IS 'Champ disciplinaire (uniquement pour les certificats)';

-- 3) Trigger updated_at pour program_fields
CREATE OR REPLACE TRIGGER set_updated_at_program_fields
    BEFORE UPDATE ON program_fields
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
