-- ============================================================================
-- UNIVERSITÉ SENGHOR - SERVICE FUNDRAISING (Levées de fonds)
-- PostgreSQL 16+
-- ============================================================================
-- Tables pour la gestion des levées de fonds, contributeurs, manifestations
-- d'intérêt, sections éditoriales et médiathèque de campagne.
-- ============================================================================

-- ============================================================================
-- TYPES ENUM SPÉCIFIQUES AU SERVICE FUNDRAISING
-- ============================================================================

CREATE TYPE fundraiser_status AS ENUM ('draft', 'active', 'completed');
CREATE TYPE contributor_category AS ENUM ('state_organization', 'foundation_philanthropist', 'company');
CREATE TYPE interest_expression_status AS ENUM ('new', 'contacted');

-- ============================================================================
-- TABLES
-- ============================================================================

-- Levées de fonds
CREATE TABLE fundraisers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,

    -- Contenu enrichi trilingue (HTML pour affichage public + Markdown pour édition)
    description_html TEXT,
    description_md TEXT,
    description_en_html TEXT,
    description_en_md TEXT,
    description_ar_html TEXT,
    description_ar_md TEXT,

    -- Raison de la levée (contenu enrichi trilingue)
    reason_html TEXT,
    reason_md TEXT,
    reason_en_html TEXT,
    reason_en_md TEXT,
    reason_ar_html TEXT,
    reason_ar_md TEXT,

    -- Image de couverture (référence MEDIA)
    cover_image_external_id UUID,

    -- Objectif financier (EUR)
    goal_amount DECIMAL(15,2) NOT NULL,

    -- Statut
    status fundraiser_status DEFAULT 'draft' NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Contributeurs d'une levée de fonds
CREATE TABLE fundraiser_contributors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fundraiser_id UUID NOT NULL REFERENCES fundraisers(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    name_en VARCHAR(255),
    name_ar VARCHAR(255),

    category contributor_category NOT NULL,
    amount DECIMAL(15,2) NOT NULL DEFAULT 0,

    -- Consentement à l'affichage public du montant
    show_amount_publicly BOOLEAN DEFAULT FALSE NOT NULL,

    logo_external_id UUID,
    display_order INT DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Table de liaison levée de fonds ↔ actualités (N:N)
CREATE TABLE fundraiser_news (
    fundraiser_id UUID NOT NULL REFERENCES fundraisers(id) ON DELETE CASCADE,
    news_id UUID NOT NULL,
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    PRIMARY KEY (fundraiser_id, news_id)
);

-- Manifestations d'intérêt
CREATE TABLE fundraiser_interest_expressions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fundraiser_id UUID NOT NULL REFERENCES fundraisers(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    message TEXT,
    status interest_expression_status DEFAULT 'new' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT uq_interest_email_fundraiser UNIQUE (email, fundraiser_id)
);

-- Sections éditoriales de la page principale
CREATE TABLE fundraiser_editorial_sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(100) UNIQUE NOT NULL,
    title_fr VARCHAR(255) NOT NULL,
    title_en VARCHAR(255),
    title_ar VARCHAR(255),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Items structurés au sein d'une section éditoriale
CREATE TABLE fundraiser_editorial_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    section_id UUID NOT NULL REFERENCES fundraiser_editorial_sections(id) ON DELETE CASCADE,
    icon VARCHAR(100) NOT NULL,
    title_fr VARCHAR(255) NOT NULL,
    title_en VARCHAR(255),
    title_ar VARCHAR(255),
    description_fr TEXT NOT NULL,
    description_en TEXT,
    description_ar TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Table de jonction campagne ↔ médias
CREATE TABLE fundraiser_media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fundraiser_id UUID NOT NULL REFERENCES fundraisers(id) ON DELETE CASCADE,
    media_external_id UUID NOT NULL,
    caption_fr VARCHAR(500),
    caption_en VARCHAR(500),
    caption_ar VARCHAR(500),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT uq_fundraiser_media UNIQUE (fundraiser_id, media_external_id)
);

-- ============================================================================
-- INDEX
-- ============================================================================

CREATE INDEX idx_fundraisers_status ON fundraisers(status);
CREATE INDEX idx_fundraisers_slug ON fundraisers(slug);
CREATE INDEX idx_fundraiser_contributors_fundraiser_id ON fundraiser_contributors(fundraiser_id);
CREATE INDEX idx_fundraiser_contributors_category ON fundraiser_contributors(category);
CREATE INDEX idx_fundraiser_news_fundraiser_id ON fundraiser_news(fundraiser_id);
CREATE INDEX idx_interest_expressions_fundraiser_id ON fundraiser_interest_expressions(fundraiser_id);
CREATE INDEX idx_interest_expressions_status ON fundraiser_interest_expressions(status);
CREATE INDEX idx_editorial_items_section_id ON fundraiser_editorial_items(section_id);
CREATE INDEX idx_fundraiser_media_fundraiser_id ON fundraiser_media(fundraiser_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

CREATE TRIGGER update_fundraisers_updated_at
    BEFORE UPDATE ON fundraisers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fundraiser_contributors_updated_at
    BEFORE UPDATE ON fundraiser_contributors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_interest_expressions_updated_at
    BEFORE UPDATE ON fundraiser_interest_expressions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_editorial_sections_updated_at
    BEFORE UPDATE ON fundraiser_editorial_sections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_editorial_items_updated_at
    BEFORE UPDATE ON fundraiser_editorial_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- FIN DU FICHIER 13_fundraising.sql
-- ============================================================================
