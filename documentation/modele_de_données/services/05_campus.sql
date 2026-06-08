-- ============================================================================
--  ██████╗ █████╗ ███╗   ███╗██████╗ ██╗   ██╗███████╗
-- ██╔════╝██╔══██╗████╗ ████║██╔══██╗██║   ██║██╔════╝
-- ██║     ███████║██╔████╔██║██████╔╝██║   ██║███████╗
-- ██║     ██╔══██║██║╚██╔╝██║██╔═══╝ ██║   ██║╚════██║
-- ╚██████╗██║  ██║██║ ╚═╝ ██║██║     ╚██████╔╝███████║
--  ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝      ╚═════╝ ╚══════╝
-- SERVICE: CAMPUS (Gestion des campus)
-- ============================================================================
-- Tables: campuses, campus_partners, campus_team, campus_media_library
-- Dépendances externes: CORE (countries), IDENTITY (head_id, user_id),
--                       MEDIA (cover_image_id, album_id), PARTNER (partner_id)
-- ============================================================================

-- Campus
CREATE TABLE campuses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,             -- legacy (TEXT brut) : reste en FR, NON traduit
    description_html TEXT,
    description_md TEXT,
    -- Traductions auto FR → EN/AR (convention additive, migration 037). On traduit
    -- la paire rich description_html/_md (pas la colonne legacy `description`).
    -- city/address restent en FR.
    name_en TEXT,
    name_ar TEXT,
    description_en_html TEXT,
    description_en_md TEXT,
    description_ar_html TEXT,
    description_ar_md TEXT,
    -- Références INTER-SERVICE (pas de FK)
    cover_image_external_id UUID, -- → MEDIA.media.id
    country_external_id UUID,     -- → CORE.countries.id
    head_external_id UUID,        -- → IDENTITY.users.id
    album_external_id UUID,       -- → MEDIA.albums.id
    email VARCHAR(255),
    phone VARCHAR(30),
    city VARCHAR(100),
    address TEXT,
    postal_code VARCHAR(20),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_headquarters BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_campuses_country ON campuses(country_external_id);
CREATE INDEX idx_campuses_code ON campuses(code);

-- Relation campus <-> partenaires
CREATE TABLE campus_partners (
    campus_id UUID REFERENCES campuses(id) ON DELETE CASCADE,
    partner_external_id UUID NOT NULL,  -- → PARTNER.partners.id
    start_date DATE,
    end_date DATE,
    PRIMARY KEY (campus_id, partner_external_id)
);

-- Équipe d'un campus
CREATE TABLE campus_team (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campus_id UUID REFERENCES campuses(id) ON DELETE CASCADE,
    user_external_id UUID NOT NULL,  -- → IDENTITY.users.id
    position VARCHAR(255) NOT NULL,
    display_order INT DEFAULT 0,
    start_date DATE,
    end_date DATE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_campus_team_user ON campus_team(user_external_id);

-- Médiathèque d'un campus (plusieurs albums possibles)
CREATE TABLE campus_media_library (
    campus_id UUID REFERENCES campuses(id) ON DELETE CASCADE,
    album_external_id UUID NOT NULL,  -- → MEDIA.albums.id
    PRIMARY KEY (campus_id, album_external_id)
);

COMMENT ON TABLE campuses IS '[CAMPUS] Campus de l''université (siège et externalisés)';
COMMENT ON COLUMN campuses.country_external_id IS 'Référence externe vers CORE.countries.id';
COMMENT ON COLUMN campuses.head_external_id IS 'Référence externe vers IDENTITY.users.id';
COMMENT ON COLUMN campus_partners.partner_external_id IS 'Référence externe vers PARTNER.partners.id';
COMMENT ON COLUMN campus_team.user_external_id IS 'Référence externe vers IDENTITY.users.id';

-- ============================================================================
-- FIN DU SERVICE CAMPUS
-- ============================================================================
