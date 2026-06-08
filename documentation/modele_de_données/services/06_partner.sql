-- ============================================================================
-- ██████╗  █████╗ ██████╗ ████████╗███╗   ██╗███████╗██████╗
-- ██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝████╗  ██║██╔════╝██╔══██╗
-- ██████╔╝███████║██████╔╝   ██║   ██╔██╗ ██║█████╗  ██████╔╝
-- ██╔═══╝ ██╔══██║██╔══██╗   ██║   ██║╚██╗██║██╔══╝  ██╔══██╗
-- ██║     ██║  ██║██║  ██║   ██║   ██║ ╚████║███████╗██║  ██║
-- ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
-- SERVICE: PARTNER (Gestion des partenaires)
-- ============================================================================
-- Tables: partners
-- Dépendances externes: CORE (countries), MEDIA (logo_id)
-- Utilisé par: CAMPUS, ACADEMIC, CONTENT, PROJECT
-- ============================================================================

-- Types ENUM spécifiques à ce service
CREATE TYPE partner_type AS ENUM ('charter_operator', 'campus_partner', 'program_partner', 'project_partner', 'other');

CREATE TABLE partners (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    -- Traductions auto FR → EN/AR (convention additive, cf. migration 036).
    -- name reste en FR (raison sociale / nom propre, NON traduit).
    description_en TEXT,
    description_ar TEXT,
    -- Références INTER-SERVICE (pas de FK)
    logo_external_id UUID,    -- → MEDIA.media.id
    country_external_id UUID, -- → CORE.countries.id
    website VARCHAR(500),
    type partner_type NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(30),
    display_order INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_partners_type ON partners(type);

COMMENT ON TABLE partners IS '[PARTNER] Partenaires de l''université';
COMMENT ON COLUMN partners.logo_external_id IS 'Référence externe vers MEDIA.media.id';
COMMENT ON COLUMN partners.country_external_id IS 'Référence externe vers CORE.countries.id';

-- ============================================================================
-- DEMANDES DE PARTENARIAT (formulaire public "Devenir partenaire")
-- ============================================================================

CREATE TYPE partnership_request_type AS ENUM ('academic', 'institutional', 'business', 'other');
CREATE TYPE partnership_request_status AS ENUM ('pending', 'approved', 'rejected');

CREATE TABLE partnership_requests (
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

CREATE INDEX idx_partnership_requests_status ON partnership_requests(status);
CREATE INDEX idx_partnership_requests_email ON partnership_requests(email);

COMMENT ON TABLE partnership_requests IS '[PARTNER] Demandes de partenariat soumises via le formulaire public';
COMMENT ON COLUMN partnership_requests.reviewed_by_external_id IS 'Référence externe vers IDENTITY.users.id';
COMMENT ON COLUMN partnership_requests.partner_external_id IS 'Référence vers PARTNER.partners.id (créé lors de l''approbation)';

-- ============================================================================
-- FIN DU SERVICE PARTNER
-- ============================================================================
