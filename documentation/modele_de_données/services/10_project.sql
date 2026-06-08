-- ============================================================================
-- ██████╗ ██████╗  ██████╗      ██╗███████╗ ██████╗████████╗
-- ██╔══██╗██╔══██╗██╔═══██╗     ██║██╔════╝██╔════╝╚══██╔══╝
-- ██████╔╝██████╔╝██║   ██║     ██║█████╗  ██║        ██║
-- ██╔═══╝ ██╔══██╗██║   ██║██   ██║██╔══╝  ██║        ██║
-- ██║     ██║  ██║╚██████╔╝╚█████╔╝███████╗╚██████╗   ██║
-- ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚════╝ ╚══════╝ ╚═════╝   ╚═╝
-- SERVICE: PROJECT (Gestion des projets institutionnels)
-- ============================================================================
-- Tables: project_categories, projects, project_countries, project_category_links,
--         project_partners, project_calls, project_media_library
-- Dépendances externes: CORE (countries), ORGANIZATION (sectors),
--                       IDENTITY (users), MEDIA (media, albums), PARTNER (partners)
-- Note: Utilise project_status défini dans 04_organization.sql
-- ============================================================================

-- Types ENUM: call_type et call_status sont définis dans 08_application.sql

-- Catégories de projets
CREATE TABLE project_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    -- Traductions auto FR → EN/AR (convention additive, cf. migration 036)
    name_en TEXT,
    name_ar TEXT,
    description_en TEXT,
    description_ar TEXT,
    icon VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    summary_html TEXT,
    summary_md TEXT,
    description_html TEXT,
    description_md TEXT,
    -- Traductions auto FR → EN/AR (convention additive, cf. migration 036)
    title_en TEXT,
    title_ar TEXT,
    summary_en_html TEXT,
    summary_en_md TEXT,
    summary_ar_html TEXT,
    summary_ar_md TEXT,
    description_en_html TEXT,
    description_en_md TEXT,
    description_ar_html TEXT,
    description_ar_md TEXT,
    -- Références INTER-SERVICE (pas de FK)
    cover_image_external_id UUID,  -- → MEDIA.media.id
    sector_external_id UUID,        -- → ORGANIZATION.sectors.id
    manager_external_id UUID,      -- → IDENTITY.users.id
    album_external_id UUID,        -- → MEDIA.albums.id
    start_date DATE,
    end_date DATE,
    budget DECIMAL(15, 2),
    currency VARCHAR(10) DEFAULT 'EUR',
    beneficiaries JSONB,
    status project_status DEFAULT 'planned',
    publication_status publication_status DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_slug ON projects(slug);
CREATE INDEX idx_projects_sector ON projects(sector_external_id);

-- Pays concernés par un projet
CREATE TABLE project_countries (
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    country_external_id UUID NOT NULL,  -- → CORE.countries.id
    PRIMARY KEY (project_id, country_external_id)
);

-- Catégories d'un projet
CREATE TABLE project_category_links (
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    category_id UUID REFERENCES project_categories(id) ON DELETE CASCADE,
    PRIMARY KEY (project_id, category_id)
);

-- Partenaires d'un projet
CREATE TABLE project_partners (
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    partner_external_id UUID NOT NULL,  -- → PARTNER.partners.id
    partner_role VARCHAR(255),
    PRIMARY KEY (project_id, partner_external_id)
);

-- Appels liés à un projet (différent des appels à candidature principaux)
CREATE TABLE project_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description_html TEXT,
    description_md TEXT,
    cover_image_external_id UUID,  -- → MEDIA.media.id
    status call_status DEFAULT 'upcoming',
    conditions_html TEXT,
    conditions_md TEXT,
    -- Traductions auto FR → EN/AR (convention additive, cf. migration 036)
    title_en TEXT,
    title_ar TEXT,
    description_en_html TEXT,
    description_en_md TEXT,
    description_ar_html TEXT,
    description_ar_md TEXT,
    conditions_en_html TEXT,
    conditions_en_md TEXT,
    conditions_ar_html TEXT,
    conditions_ar_md TEXT,
    type call_type,
    deadline TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Médiathèque d'un projet (plusieurs albums possibles)
CREATE TABLE project_media_library (
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    album_external_id UUID NOT NULL,  -- → MEDIA.albums.id
    PRIMARY KEY (project_id, album_external_id)
);

COMMENT ON TABLE projects IS '[PROJECT] Projets institutionnels de l''université';
COMMENT ON TABLE project_categories IS '[PROJECT] Catégories de projets';
COMMENT ON COLUMN projects.sector_external_id IS 'Référence externe vers ORGANIZATION.sectors.id';
COMMENT ON COLUMN projects.manager_external_id IS 'Référence externe vers IDENTITY.users.id';
COMMENT ON COLUMN project_partners.partner_external_id IS 'Référence externe vers PARTNER.partners.id';

-- ============================================================================
-- FIN DU SERVICE PROJECT
-- ============================================================================
