-- ============================================================================
--  ██████╗ ██████╗  ██████╗  █████╗ ███╗   ██╗██╗███████╗ █████╗ ████████╗██╗ ██████╗ ███╗   ██╗
-- ██╔═══██╗██╔══██╗██╔════╝ ██╔══██╗████╗  ██║██║╚══███╔╝██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║
-- ██║   ██║██████╔╝██║  ███╗███████║██╔██╗ ██║██║  ███╔╝ ███████║   ██║   ██║██║   ██║██╔██╗ ██║
-- ██║   ██║██╔══██╗██║   ██║██╔══██║██║╚██╗██║██║ ███╔╝  ██╔══██║   ██║   ██║██║   ██║██║╚██╗██║
-- ╚██████╔╝██║  ██║╚██████╔╝██║  ██║██║ ╚████║██║███████╗██║  ██║   ██║   ██║╚██████╔╝██║ ╚████║
--  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
-- SERVICE: ORGANIZATION (Structure organisationnelle)
-- ============================================================================
-- Tables: sectors, services, service_objectives, service_achievements,
--         service_projects, service_media_library
-- Dépendances externes: IDENTITY (head_id), MEDIA (icon_id, cover_image_id, album_id)
-- ============================================================================

-- Types ENUM spécifiques à ce service
CREATE TYPE project_status AS ENUM ('ongoing', 'completed', 'suspended', 'planned');

-- Secteurs
CREATE TABLE sectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description_html TEXT,
    description_md TEXT,
    mission_html TEXT,
    mission_md TEXT,
    -- Références INTER-SERVICE (pas de FK)
    icon_external_id UUID,        -- → MEDIA.media.id
    cover_image_external_id UUID, -- → MEDIA.media.id
    head_external_id UUID,        -- → IDENTITY.users.id
    display_order INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sectors_code ON sectors(code);

-- Services de secteur
CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sector_id UUID REFERENCES sectors(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    sigle VARCHAR(50),
    color VARCHAR(7),
    description_html TEXT,
    description_md TEXT,
    mission_html TEXT,
    mission_md TEXT,
    -- Références INTER-SERVICE (pas de FK)
    head_external_id UUID,   -- → IDENTITY.users.id
    album_external_id UUID,  -- → MEDIA.albums.id
    email VARCHAR(255),
    phone VARCHAR(30),
    display_order INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_services_sector ON services(sector_id);

-- Objectifs d'un service
CREATE TABLE service_objectives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description_html TEXT,
    description_md TEXT,
    display_order INT DEFAULT 0
);

-- Réalisations d'un service
CREATE TABLE service_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description_html TEXT,
    description_md TEXT,
    type VARCHAR(100),
    cover_image_external_id UUID,  -- → MEDIA.media.id
    achievement_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Projets internes d'un service (différent des projets institutionnels)
CREATE TABLE service_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description_html TEXT,
    description_md TEXT,
    cover_image_external_id UUID,  -- → MEDIA.media.id
    progress INT DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    status project_status DEFAULT 'planned',
    start_date DATE,
    expected_end_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Médiathèque d'un service (plusieurs albums possibles)
CREATE TABLE service_media_library (
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    album_external_id UUID NOT NULL,  -- → MEDIA.albums.id
    PRIMARY KEY (service_id, album_external_id)
);

-- Équipe d'un service
CREATE TABLE service_team (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    user_external_id UUID NOT NULL,  -- → IDENTITY.users.id
    position VARCHAR(255) NOT NULL,
    display_order INT DEFAULT 0,
    start_date DATE,
    end_date DATE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_service_team_service ON service_team(service_id);
CREATE INDEX idx_service_team_user ON service_team(user_external_id);

COMMENT ON TABLE sectors IS '[ORGANIZATION] Secteurs de l''université';
COMMENT ON TABLE services IS '[ORGANIZATION] Services rattachés aux secteurs';
COMMENT ON TABLE service_team IS '[ORGANIZATION] Équipe d''un service';
COMMENT ON COLUMN sectors.head_external_id IS 'Référence externe vers IDENTITY.users.id';
COMMENT ON COLUMN services.album_external_id IS 'Référence externe vers MEDIA.albums.id';
COMMENT ON COLUMN service_team.user_external_id IS 'Référence externe vers IDENTITY.users.id';

-- ============================================================================
-- FIN DU SERVICE ORGANIZATION
-- ============================================================================
