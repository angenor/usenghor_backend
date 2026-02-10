-- Migration 006: Demandes de partenariat
-- Date: 2026-02-10
-- Description: Ajoute la table partnership_requests pour les demandes de partenariat
--              soumises via le formulaire public "Devenir partenaire".

BEGIN;

-- 1) Types ENUM (DO block pour gérer le cas où ils existent déjà)
DO $$ BEGIN
    CREATE TYPE partnership_request_type AS ENUM ('academic', 'institutional', 'business', 'other');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE partnership_request_status AS ENUM ('pending', 'approved', 'rejected');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 2) Table partnership_requests
CREATE TABLE IF NOT EXISTS partnership_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    organization VARCHAR(255) NOT NULL,
    type partnership_request_type NOT NULL,
    message TEXT,
    status partnership_request_status NOT NULL DEFAULT 'pending',
    rejection_reason TEXT,
    reviewed_by_external_id UUID,  -- → IDENTITY.users.id
    reviewed_at TIMESTAMPTZ,
    partner_external_id UUID,      -- → PARTNER.partners.id
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_partnership_requests_status ON partnership_requests(status);
CREATE INDEX IF NOT EXISTS idx_partnership_requests_email ON partnership_requests(email);

COMMENT ON TABLE partnership_requests IS '[PARTNER] Demandes de partenariat soumises via le formulaire public';
COMMENT ON COLUMN partnership_requests.reviewed_by_external_id IS 'Référence externe vers IDENTITY.users.id';
COMMENT ON COLUMN partnership_requests.partner_external_id IS 'Référence vers PARTNER.partners.id (créé lors de l''approbation)';

COMMIT;
