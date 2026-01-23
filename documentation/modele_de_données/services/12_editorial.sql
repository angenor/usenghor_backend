-- ============================================================================
-- ███████╗██████╗ ██╗████████╗ ██████╗ ██████╗ ██╗ █████╗ ██╗
-- ██╔════╝██╔══██╗██║╚══██╔══╝██╔═══██╗██╔══██╗██║██╔══██╗██║
-- █████╗  ██║  ██║██║   ██║   ██║   ██║██████╔╝██║███████║██║
-- ██╔══╝  ██║  ██║██║   ██║   ██║   ██║██╔══██╗██║██╔══██║██║
-- ███████╗██████╔╝██║   ██║   ╚██████╔╝██║  ██║██║██║  ██║███████╗
-- ╚══════╝╚═════╝ ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝
-- SERVICE: EDITORIAL (Contenus de configuration)
-- ============================================================================
-- Tables: editorial_categories, editorial_contents, editorial_contents_history
-- Dépendances externes: IDENTITY (users)
-- ============================================================================

-- Types ENUM spécifiques à ce service
CREATE TYPE editorial_value_type AS ENUM ('text', 'number', 'json', 'html', 'markdown');

-- Catégories de contenus éditoriaux
CREATE TABLE editorial_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Contenus éditoriaux de configuration
CREATE TABLE editorial_contents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    value_type editorial_value_type DEFAULT 'text',
    category_id UUID REFERENCES editorial_categories(id) ON DELETE SET NULL,
    year INT,
    description TEXT,
    admin_editable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_editorial_contents_key ON editorial_contents(key);
CREATE INDEX idx_editorial_contents_category ON editorial_contents(category_id);

-- Historique des modifications de contenus éditoriaux
CREATE TABLE editorial_contents_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID REFERENCES editorial_contents(id) ON DELETE CASCADE,
    old_value TEXT,
    new_value TEXT,
    modified_by_external_id UUID,  -- → IDENTITY.users.id
    modified_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE editorial_categories IS '[EDITORIAL] Catégories de contenus éditoriaux';
COMMENT ON TABLE editorial_contents IS '[EDITORIAL] Contenus de configuration dynamiques (statistiques, valeurs, etc.)';
COMMENT ON COLUMN editorial_contents_history.modified_by_external_id IS 'Référence externe vers IDENTITY.users.id';

-- ============================================================================
-- FIN DU SERVICE EDITORIAL
-- ============================================================================
