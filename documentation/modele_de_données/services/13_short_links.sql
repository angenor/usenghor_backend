-- ============================================================================
-- SERVICE SHORT_LINKS - Réducteur de liens
-- ============================================================================
-- Gestion des liens courts (/r/{code}) avec redirection 302.
-- Codes générés séquentiellement en base 36 (alphabet 0-9a-z, max 4 caractères).
-- Capacité maximale : 1 679 616 liens (36^4).
-- ============================================================================

-- Séquence pour la génération des codes base 36
CREATE SEQUENCE IF NOT EXISTS short_link_counter_seq
    START WITH 0
    INCREMENT BY 1
    MINVALUE 0
    MAXVALUE 1679615
    NO CYCLE;

-- Table des liens courts
CREATE TABLE IF NOT EXISTS short_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(4) NOT NULL,
    target_url VARCHAR(2000) NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index unique sur le code court (lookup pour la redirection)
CREATE UNIQUE INDEX IF NOT EXISTS idx_short_links_code ON short_links(code);

-- Trigger pour updated_at
CREATE TRIGGER set_short_links_updated_at
    BEFORE UPDATE ON short_links
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Table des domaines autorisés (liste blanche)
CREATE TABLE IF NOT EXISTS allowed_domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index unique sur le domaine
CREATE UNIQUE INDEX IF NOT EXISTS idx_allowed_domains_domain ON allowed_domains(domain);

-- Commentaires
COMMENT ON TABLE short_links IS '[SHORT_LINKS] Liens courts avec redirection';
COMMENT ON COLUMN short_links.code IS 'Code court en base 36 (1-4 caractères, [0-9a-z])';
COMMENT ON COLUMN short_links.target_url IS 'URL de destination (interne ou domaine autorisé)';
COMMENT ON COLUMN short_links.created_by IS 'Référence externe vers IDENTITY.users.id';
COMMENT ON TABLE allowed_domains IS '[SHORT_LINKS] Liste blanche de domaines externes autorisés';
COMMENT ON SEQUENCE short_link_counter_seq IS 'Compteur séquentiel pour la génération de codes base 36 (max 1679615 = zzzz)';
