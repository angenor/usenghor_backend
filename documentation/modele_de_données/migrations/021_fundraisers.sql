-- ============================================================================
-- Migration 021: Création des tables de levées de fonds
-- Date: 2026-03-17
-- Feature: 004-fundraising-page
-- ============================================================================

BEGIN;

-- Types ENUM
CREATE TYPE fundraiser_status AS ENUM ('draft', 'active', 'completed');
CREATE TYPE contributor_category AS ENUM ('state_organization', 'foundation_philanthropist', 'company');

-- Table principale
CREATE TABLE fundraisers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description_html TEXT,
    description_md TEXT,
    description_en_html TEXT,
    description_en_md TEXT,
    description_ar_html TEXT,
    description_ar_md TEXT,
    cover_image_external_id UUID,
    goal_amount DECIMAL(15,2) NOT NULL,
    status fundraiser_status DEFAULT 'draft' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Contributeurs
CREATE TABLE fundraiser_contributors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fundraiser_id UUID NOT NULL REFERENCES fundraisers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    name_en VARCHAR(255),
    name_ar VARCHAR(255),
    category contributor_category NOT NULL,
    amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    logo_external_id UUID,
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Association actualités
CREATE TABLE fundraiser_news (
    fundraiser_id UUID NOT NULL REFERENCES fundraisers(id) ON DELETE CASCADE,
    news_id UUID NOT NULL,
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    PRIMARY KEY (fundraiser_id, news_id)
);

-- Index
CREATE INDEX idx_fundraisers_status ON fundraisers(status);
CREATE INDEX idx_fundraisers_slug ON fundraisers(slug);
CREATE INDEX idx_fundraiser_contributors_fundraiser_id ON fundraiser_contributors(fundraiser_id);
CREATE INDEX idx_fundraiser_contributors_category ON fundraiser_contributors(category);
CREATE INDEX idx_fundraiser_news_fundraiser_id ON fundraiser_news(fundraiser_id);

-- Triggers updated_at
CREATE TRIGGER update_fundraisers_updated_at
    BEFORE UPDATE ON fundraisers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fundraiser_contributors_updated_at
    BEFORE UPDATE ON fundraiser_contributors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
