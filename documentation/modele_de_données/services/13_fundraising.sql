-- ============================================================================
-- UNIVERSITÉ SENGHOR - SERVICE FUNDRAISING (Levées de fonds)
-- PostgreSQL 15+
-- ============================================================================
-- Tables pour la gestion des levées de fonds, contributeurs et associations
-- avec les actualités.
-- ============================================================================

-- ============================================================================
-- TYPES ENUM SPÉCIFIQUES AU SERVICE FUNDRAISING
-- ============================================================================

-- Statut d'une levée de fonds
CREATE TYPE fundraiser_status AS ENUM ('draft', 'active', 'completed');

-- Catégorie de contributeur
CREATE TYPE contributor_category AS ENUM ('state_organization', 'foundation_philanthropist', 'company');

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

    -- Image de couverture (référence MEDIA)
    cover_image_external_id UUID,  -- → MEDIA.media.id

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

    -- Nom trilingue
    name VARCHAR(255) NOT NULL,
    name_en VARCHAR(255),
    name_ar VARCHAR(255),

    -- Catégorie
    category contributor_category NOT NULL,

    -- Montant de la contribution (EUR)
    amount DECIMAL(15,2) NOT NULL DEFAULT 0,

    -- Logo (référence MEDIA, optionnel)
    logo_external_id UUID,  -- → MEDIA.media.id

    -- Ordre d'affichage
    display_order INT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Table de liaison levée de fonds ↔ actualités (N:N)
CREATE TABLE fundraiser_news (
    fundraiser_id UUID NOT NULL REFERENCES fundraisers(id) ON DELETE CASCADE,
    news_id UUID NOT NULL,  -- Référence CONTENT.news.id (external_id, pas de FK)
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    PRIMARY KEY (fundraiser_id, news_id)
);

-- ============================================================================
-- INDEX
-- ============================================================================

CREATE INDEX idx_fundraisers_status ON fundraisers(status);
CREATE INDEX idx_fundraisers_slug ON fundraisers(slug);
CREATE INDEX idx_fundraiser_contributors_fundraiser_id ON fundraiser_contributors(fundraiser_id);
CREATE INDEX idx_fundraiser_contributors_category ON fundraiser_contributors(category);
CREATE INDEX idx_fundraiser_news_fundraiser_id ON fundraiser_news(fundraiser_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Mise à jour automatique du updated_at
CREATE TRIGGER update_fundraisers_updated_at
    BEFORE UPDATE ON fundraisers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fundraiser_contributors_updated_at
    BEFORE UPDATE ON fundraiser_contributors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- FIN DU FICHIER 13_fundraising.sql
-- ============================================================================
