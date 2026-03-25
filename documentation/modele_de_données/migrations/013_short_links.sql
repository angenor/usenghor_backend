-- ============================================================================
-- MIGRATION 013 : Réducteur de liens (short_links + allowed_domains)
-- ============================================================================
-- Usage local  : docker exec -i usenghor_postgres psql -U usenghor -d usenghor < usenghor_backend/documentation/modele_de_données/migrations/013_short_links.sql
-- Usage prod   : docker exec -i usenghor_db psql -U usenghor -d usenghor < usenghor_backend/documentation/modele_de_données/migrations/013_short_links.sql
-- ============================================================================

BEGIN;

-- Séquence pour la génération des codes base 36
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'short_link_counter_seq') THEN
        CREATE SEQUENCE short_link_counter_seq
            START WITH 0
            INCREMENT BY 1
            MINVALUE 0
            MAXVALUE 1679615
            NO CYCLE;
        RAISE NOTICE 'Séquence short_link_counter_seq créée';
    ELSE
        RAISE NOTICE 'Séquence short_link_counter_seq existe déjà';
    END IF;
END $$;

-- Table des liens courts
CREATE TABLE IF NOT EXISTS short_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(4) NOT NULL,
    target_url VARCHAR(2000) NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index unique sur le code
CREATE UNIQUE INDEX IF NOT EXISTS idx_short_links_code ON short_links(code);

-- Trigger updated_at
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'set_short_links_updated_at'
    ) THEN
        CREATE TRIGGER set_short_links_updated_at
            BEFORE UPDATE ON short_links
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        RAISE NOTICE 'Trigger set_short_links_updated_at créé';
    ELSE
        RAISE NOTICE 'Trigger set_short_links_updated_at existe déjà';
    END IF;
END $$;

-- Table des domaines autorisés
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

-- Permissions
INSERT INTO permissions (id, code, name_fr, description, category, created_at)
VALUES
    (uuid_generate_v4(), 'short_links.view', 'Voir les liens courts', 'Permet de voir la liste des liens courts', 'short_links', NOW()),
    (uuid_generate_v4(), 'short_links.create', 'Créer des liens courts', 'Permet de créer de nouveaux liens courts', 'short_links', NOW()),
    (uuid_generate_v4(), 'short_links.delete', 'Supprimer des liens courts', 'Permet de supprimer des liens courts', 'short_links', NOW())
ON CONFLICT (code) DO NOTHING;

-- Attribuer les permissions au rôle admin (si le rôle existe)
DO $$
DECLARE
    admin_role_id UUID;
    perm_id UUID;
BEGIN
    SELECT id INTO admin_role_id FROM roles WHERE code = 'admin' LIMIT 1;
    IF admin_role_id IS NOT NULL THEN
        FOR perm_id IN SELECT id FROM permissions WHERE code LIKE 'short_links.%' LOOP
            INSERT INTO role_permissions (role_id, permission_id)
            VALUES (admin_role_id, perm_id)
            ON CONFLICT DO NOTHING;
        END LOOP;
        RAISE NOTICE 'Permissions short_links attribuées au rôle admin';
    END IF;
END $$;

COMMIT;

\echo 'Migration 013_short_links terminée avec succès'
