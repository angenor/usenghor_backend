-- ============================================================================
-- SERVICE SURVEY - Campagnes de sondages et formulaires
-- ============================================================================
-- Tables : survey_campaigns, survey_responses, survey_associations
-- Enum   : survey_campaign_status
-- ============================================================================

-- Type ENUM pour le statut des campagnes
CREATE TYPE survey_campaign_status AS ENUM ('draft', 'active', 'paused', 'closed');

-- ============================================================================
-- TABLE : survey_campaigns
-- ============================================================================
CREATE TABLE survey_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(100) NOT NULL UNIQUE,
    title_fr VARCHAR(255) NOT NULL,
    title_en VARCHAR(255),
    title_ar VARCHAR(255),
    description_fr TEXT,
    description_en TEXT,
    description_ar TEXT,
    survey_json JSONB NOT NULL DEFAULT '{}',
    status survey_campaign_status NOT NULL DEFAULT 'draft',
    confirmation_email_enabled BOOLEAN NOT NULL DEFAULT false,
    closes_at TIMESTAMPTZ,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_survey_campaigns_created_by ON survey_campaigns(created_by);
CREATE INDEX idx_survey_campaigns_status ON survey_campaigns(status);
CREATE INDEX idx_survey_campaigns_slug ON survey_campaigns(slug);

-- ============================================================================
-- TABLE : survey_responses
-- ============================================================================
CREATE TABLE survey_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES survey_campaigns(id) ON DELETE CASCADE,
    response_data JSONB NOT NULL,
    ip_address INET,
    session_id VARCHAR(64),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_survey_responses_campaign_id ON survey_responses(campaign_id);
CREATE INDEX idx_survey_responses_ip_address ON survey_responses(ip_address);
ALTER TABLE survey_responses ADD CONSTRAINT uq_survey_responses_session UNIQUE (campaign_id, session_id);

-- ============================================================================
-- TABLE : survey_associations
-- ============================================================================
CREATE TABLE survey_associations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES survey_campaigns(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE survey_associations ADD CONSTRAINT uq_survey_associations UNIQUE (campaign_id, entity_type, entity_id);
CREATE INDEX idx_survey_associations_entity ON survey_associations(entity_type, entity_id);

-- ============================================================================
-- VUE : v_survey_campaigns_with_stats
-- ============================================================================
CREATE OR REPLACE VIEW v_survey_campaigns_with_stats AS
SELECT
    sc.*,
    COUNT(sr.id) AS response_count,
    MAX(sr.submitted_at) AS last_response_at
FROM survey_campaigns sc
LEFT JOIN survey_responses sr ON sr.campaign_id = sc.id
GROUP BY sc.id;

-- ============================================================================
-- PERMISSION : survey.manage
-- ============================================================================
INSERT INTO permissions (id, code, name_fr, description, category)
VALUES (
    uuid_generate_v4(),
    'survey.manage',
    'Gérer les campagnes de sondage',
    'Créer, modifier, supprimer et consulter les campagnes de sondage et leurs réponses',
    'survey'
) ON CONFLICT (code) DO NOTHING;

-- Trigger updated_at
CREATE TRIGGER set_updated_at_survey_campaigns
    BEFORE UPDATE ON survey_campaigns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
