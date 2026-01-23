-- ============================================================================
-- ███╗   ██╗███████╗██╗    ██╗███████╗██╗     ███████╗████████╗████████╗███████╗██████╗
-- ████╗  ██║██╔════╝██║    ██║██╔════╝██║     ██╔════╝╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗
-- ██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗██║     █████╗     ██║      ██║   █████╗  ██████╔╝
-- ██║╚██╗██║██╔══╝  ██║███╗██║╚════██║██║     ██╔══╝     ██║      ██║   ██╔══╝  ██╔══██╗
-- ██║ ╚████║███████╗╚███╔███╔╝███████║███████╗███████╗   ██║      ██║   ███████╗██║  ██║
-- ╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝╚══════╝╚══════╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝
-- SERVICE: NEWSLETTER (Gestion newsletter)
-- ============================================================================
-- Tables: newsletter_subscribers, newsletter_campaigns, newsletter_sends
-- Dépendances externes: IDENTITY (users)
-- ============================================================================

-- Abonnés à la newsletter
CREATE TABLE newsletter_subscribers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    last_name VARCHAR(100),
    first_name VARCHAR(100),
    user_external_id UUID,  -- → IDENTITY.users.id
    active BOOLEAN DEFAULT TRUE,
    unsubscribe_token VARCHAR(255) UNIQUE,
    source VARCHAR(100), -- d'où vient l'inscription
    subscribed_at TIMESTAMPTZ DEFAULT NOW(),
    unsubscribed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_newsletter_subscribers_email ON newsletter_subscribers(email);
CREATE INDEX idx_newsletter_subscribers_user ON newsletter_subscribers(user_external_id);

-- Campagnes de newsletter
CREATE TABLE newsletter_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    html_content TEXT,
    text_content TEXT,
    status VARCHAR(50) DEFAULT 'draft', -- draft, scheduled, sent
    scheduled_send_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    recipient_count INT DEFAULT 0,
    open_count INT DEFAULT 0,
    click_count INT DEFAULT 0,
    created_by_external_id UUID,  -- → IDENTITY.users.id
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Historique d'envoi par destinataire
CREATE TABLE newsletter_sends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES newsletter_campaigns(id) ON DELETE CASCADE,
    subscriber_id UUID REFERENCES newsletter_subscribers(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'sent', -- sent, opened, clicked, error
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE INDEX idx_newsletter_sends_campaign ON newsletter_sends(campaign_id);

COMMENT ON TABLE newsletter_subscribers IS '[NEWSLETTER] Abonnés à la newsletter';
COMMENT ON TABLE newsletter_campaigns IS '[NEWSLETTER] Campagnes de newsletter';
COMMENT ON COLUMN newsletter_subscribers.user_external_id IS 'Référence externe vers IDENTITY.users.id';

-- ============================================================================
-- FIN DU SERVICE NEWSLETTER
-- ============================================================================
