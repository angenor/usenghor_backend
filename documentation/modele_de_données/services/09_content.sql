-- ============================================================================
--  ██████╗ ██████╗ ███╗   ██╗████████╗███████╗███╗   ██╗████████╗
-- ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝████╗  ██║╚══██╔══╝
-- ██║     ██║   ██║██╔██╗ ██║   ██║   █████╗  ██╔██╗ ██║   ██║
-- ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██║╚██╗██║   ██║
-- ╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████╗██║ ╚████║   ██║
--  ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝   ╚═╝
-- SERVICE: CONTENT (Actualités & Événements)
-- ============================================================================
-- Tables: events, event_partners, event_registrations, event_media_library,
--         news, news_media, tags, news_tags
-- Dépendances externes: CORE (countries), IDENTITY (users), MEDIA (media, albums),
--                       CAMPUS (campuses), ORGANIZATION (departments, services),
--                       PARTNER (partners), PROJECT (projects)
-- ============================================================================

-- Types ENUM spécifiques à ce service
CREATE TYPE event_type AS ENUM ('conference', 'workshop', 'ceremony', 'seminar', 'symposium', 'other');
CREATE TYPE news_highlight_status AS ENUM ('standard', 'featured', 'headline');

-- Événements
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    content TEXT, -- Contenu riche
    -- Références INTER-SERVICE (pas de FK)
    cover_image_external_id UUID,  -- → MEDIA.media.id
    country_external_id UUID,      -- → CORE.countries.id
    campus_external_id UUID,       -- → CAMPUS.campuses.id
    department_external_id UUID,   -- → ORGANIZATION.departments.id
    project_external_id UUID,      -- → PROJECT.projects.id
    organizer_external_id UUID,    -- → IDENTITY.users.id
    album_external_id UUID,        -- → MEDIA.albums.id
    type event_type NOT NULL,
    type_other VARCHAR(100), -- Si type = 'other'
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ,
    venue VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_online BOOLEAN DEFAULT FALSE,
    video_conference_link VARCHAR(500),
    registration_required BOOLEAN DEFAULT FALSE,
    registration_link VARCHAR(500),
    max_attendees INT,
    status publication_status DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_date ON events(start_date);
CREATE INDEX idx_events_project ON events(project_external_id);
CREATE INDEX idx_events_type ON events(type);
CREATE INDEX idx_events_slug ON events(slug);
CREATE INDEX idx_events_campus ON events(campus_external_id);
CREATE INDEX idx_events_department ON events(department_external_id);

-- Partenaires d'un événement
CREATE TABLE event_partners (
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    partner_external_id UUID NOT NULL,  -- → PARTNER.partners.id
    PRIMARY KEY (event_id, partner_external_id)
);

-- Inscriptions à un événement
CREATE TABLE event_registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    user_external_id UUID,  -- → IDENTITY.users.id
    -- Pour les non-inscrits
    last_name VARCHAR(100),
    first_name VARCHAR(100),
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(30),
    organization VARCHAR(255),
    status VARCHAR(50) DEFAULT 'registered', -- registered, confirmed, cancelled, attended
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (event_id, email)
);

CREATE INDEX idx_event_registrations_user ON event_registrations(user_external_id);

-- Médiathèque d'un événement (plusieurs albums possibles)
CREATE TABLE event_media_library (
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    album_external_id UUID NOT NULL,  -- → MEDIA.albums.id
    PRIMARY KEY (event_id, album_external_id)
);

-- Tags/catégories pour actualités
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    icon VARCHAR(50),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Actualités
CREATE TABLE news (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    summary TEXT,
    content TEXT, -- Contenu riche (HTML/Markdown)
    video_url VARCHAR(500),
    -- Références INTER-SERVICE (pas de FK)
    cover_image_external_id UUID,  -- → MEDIA.media.id
    campus_external_id UUID,       -- → CAMPUS.campuses.id
    department_external_id UUID,   -- → ORGANIZATION.departments.id
    service_external_id UUID,      -- → ORGANIZATION.services.id
    event_external_id UUID,        -- → CONTENT.events.id (même service, peut être FK si souhaité)
    project_external_id UUID,      -- → PROJECT.projects.id
    author_external_id UUID,       -- → IDENTITY.users.id
    highlight_status news_highlight_status DEFAULT 'standard',
    status publication_status DEFAULT 'draft',
    published_at TIMESTAMPTZ,
    visible_from TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_news_published_at ON news(published_at);
CREATE INDEX idx_news_status ON news(status, highlight_status);
CREATE INDEX idx_news_slug ON news(slug);
CREATE INDEX idx_news_project ON news(project_external_id);
CREATE INDEX idx_news_campus ON news(campus_external_id);

-- Photos d'une actualité
CREATE TABLE news_media (
    news_id UUID REFERENCES news(id) ON DELETE CASCADE,
    media_external_id UUID NOT NULL,  -- → MEDIA.media.id
    display_order INT DEFAULT 0,
    PRIMARY KEY (news_id, media_external_id)
);

-- Relation actualités <-> tags
CREATE TABLE news_tags (
    news_id UUID REFERENCES news(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (news_id, tag_id)
);

COMMENT ON TABLE events IS '[CONTENT] Événements organisés par l''université';
COMMENT ON TABLE news IS '[CONTENT] Articles d''actualité et news';
COMMENT ON TABLE tags IS '[CONTENT] Tags/catégories pour les actualités';
COMMENT ON COLUMN events.project_external_id IS 'Référence externe vers PROJECT.projects.id';
COMMENT ON COLUMN news.author_external_id IS 'Référence externe vers IDENTITY.users.id';

-- ============================================================================
-- FIN DU SERVICE CONTENT
-- ============================================================================
