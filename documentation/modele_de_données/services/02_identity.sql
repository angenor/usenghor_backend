-- ============================================================================
-- ██╗██████╗ ███████╗███╗   ██╗████████╗██╗████████╗██╗   ██╗
-- ██║██╔══██╗██╔════╝████╗  ██║╚══██╔══╝██║╚══██╔══╝╚██╗ ██╔╝
-- ██║██║  ██║█████╗  ██╔██╗ ██║   ██║   ██║   ██║    ╚████╔╝
-- ██║██║  ██║██╔══╝  ██║╚██╗██║   ██║   ██║   ██║     ╚██╔╝
-- ██║██████╔╝███████╗██║ ╚████║   ██║   ██║   ██║      ██║
-- ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝   ╚═╝      ╚═╝
-- SERVICE: IDENTITY (Authentification & Utilisateurs)
-- ============================================================================
-- Tables: permissions, roles, role_permissions, users, user_roles, user_tokens, audit_logs
-- Dépendances externes: CORE (countries), MEDIA (photo_id), CAMPUS (campus_id)
-- ============================================================================

-- Permissions (actions possibles)
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name_fr VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rôles
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name_fr VARCHAR(100) NOT NULL,
    description TEXT,
    hierarchy_level INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Relation rôles <-> permissions
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Utilisateurs
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    salutation salutation,
    birth_date DATE,
    phone VARCHAR(30),
    phone_whatsapp VARCHAR(30),
    linkedin VARCHAR(255),
    facebook VARCHAR(255),
    biography TEXT,
    -- Références INTER-SERVICE (pas de FK)
    photo_external_id UUID,              -- → MEDIA.media.id
    nationality_external_id UUID,        -- → CORE.countries.id
    residence_country_external_id UUID,  -- → CORE.countries.id
    city VARCHAR(100),
    address TEXT,
    active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_name ON users(last_name, first_name);
CREATE INDEX idx_users_nationality ON users(nationality_external_id);

-- Relation utilisateurs <-> rôles
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    campus_external_id UUID,  -- → CAMPUS.campuses.id (Rattachement optionnel à un campus)
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_campus ON user_roles(campus_external_id);

-- Tokens de réinitialisation et vérification
CREATE TABLE user_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'email_verification', 'password_reset'
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_tokens_token ON user_tokens(token);

-- Audit et logs (peut aussi être un service séparé)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,  -- Pas de FK pour permettre la suppression d'utilisateurs
    action VARCHAR(50) NOT NULL, -- create, update, delete, login, logout
    table_name VARCHAR(100),
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name);
CREATE INDEX idx_audit_logs_date ON audit_logs(created_at);

COMMENT ON TABLE users IS '[IDENTITY] Utilisateurs inscrits sur la plateforme';
COMMENT ON TABLE roles IS '[IDENTITY] Rôles définissant les permissions des utilisateurs';
COMMENT ON TABLE permissions IS '[IDENTITY] Permissions atomiques attribuables aux rôles';
COMMENT ON TABLE audit_logs IS '[IDENTITY] Logs d''audit pour traçabilité';
COMMENT ON COLUMN users.photo_external_id IS 'Référence externe vers MEDIA.media.id';
COMMENT ON COLUMN users.nationality_external_id IS 'Référence externe vers CORE.countries.id';
COMMENT ON COLUMN user_roles.campus_external_id IS 'Référence externe vers CAMPUS.campuses.id';

-- ============================================================================
-- FIN DU SERVICE IDENTITY
-- ============================================================================
