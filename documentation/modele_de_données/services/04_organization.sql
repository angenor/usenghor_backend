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
    -- Traductions auto FR → EN/AR (convention additive, migration 037 ; TEXT car
    -- une traduction n'a aucune garantie de longueur). FR = colonnes ci-dessus.
    name_en TEXT,
    name_ar TEXT,
    description_en_html TEXT,
    description_en_md TEXT,
    description_ar_html TEXT,
    description_ar_md TEXT,
    mission_en_html TEXT,
    mission_en_md TEXT,
    mission_ar_html TEXT,
    mission_ar_md TEXT,
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
    sigle VARCHAR(50),  -- acronyme : NON traduit
    color VARCHAR(7),
    description_html TEXT,
    description_md TEXT,
    mission_html TEXT,
    mission_md TEXT,
    -- Traductions auto FR → EN/AR (convention additive, migration 037). sigle = FR.
    name_en TEXT,
    name_ar TEXT,
    description_en_html TEXT,
    description_en_md TEXT,
    description_ar_html TEXT,
    description_ar_md TEXT,
    mission_en_html TEXT,
    mission_en_md TEXT,
    mission_ar_html TEXT,
    mission_ar_md TEXT,
    -- Références INTER-SERVICE (pas de FK)
    head_external_id UUID,   -- → IDENTITY.users.id
    album_external_id UUID,  -- → MEDIA.albums.id
    -- Niveau « pôle » (migration 050) : un seul niveau, même secteur que le parent (trigger)
    parent_id UUID REFERENCES services(id) ON DELETE SET NULL,
    landing_path VARCHAR(255),  -- page dédiée interne sans préfixe de langue, ex. /entrepreneuriat
    email VARCHAR(255),
    phone VARCHAR(30),
    display_order INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_services_sector ON services(sector_id);

ALTER TABLE services ADD CONSTRAINT services_parent_not_self CHECK (parent_id IS NULL OR parent_id <> id);
ALTER TABLE services ADD CONSTRAINT services_landing_path_format
    CHECK (landing_path IS NULL OR (landing_path ~ '^/' AND landing_path !~ '^//' AND landing_path !~ '\s'));
CREATE INDEX idx_services_parent ON services(parent_id) WHERE parent_id IS NOT NULL;

-- Hiérarchie des pôles : parent existant et de premier niveau, service sans pôles
-- pour être rattaché, même secteur, pas de changement de secteur d'un parent (050)
CREATE OR REPLACE FUNCTION services_check_hierarchy() RETURNS TRIGGER AS $$
DECLARE
    parent_row RECORD;
    n_children INTEGER;
BEGIN
    SELECT count(*) INTO n_children FROM services WHERE parent_id = NEW.id AND id <> NEW.id;

    IF NEW.parent_id IS NOT NULL THEN
        SELECT id, parent_id, sector_id INTO parent_row FROM services WHERE id = NEW.parent_id;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Service parent introuvable' USING ERRCODE = 'check_violation';
        END IF;
        IF parent_row.parent_id IS NOT NULL THEN
            RAISE EXCEPTION 'Le service parent est lui-même un pôle (un seul niveau)' USING ERRCODE = 'check_violation';
        END IF;
        IF n_children > 0 THEN
            RAISE EXCEPTION 'Ce service a % pôle(s) : il ne peut pas être rattaché', n_children USING ERRCODE = 'check_violation';
        END IF;
        IF parent_row.sector_id IS DISTINCT FROM NEW.sector_id THEN
            RAISE EXCEPTION 'Le service parent doit appartenir au même secteur' USING ERRCODE = 'check_violation';
        END IF;
    END IF;

    IF TG_OP = 'UPDATE' AND n_children > 0 AND NEW.sector_id IS DISTINCT FROM OLD.sector_id THEN
        RAISE EXCEPTION 'Déplacez ou détachez d''abord ses % pôle(s)', n_children USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER services_check_hierarchy
    BEFORE INSERT OR UPDATE OF parent_id, sector_id ON services
    FOR EACH ROW EXECUTE FUNCTION services_check_hierarchy();

-- Objectifs d'un service
CREATE TABLE service_objectives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description_html TEXT,
    description_md TEXT,
    -- Traductions auto FR → EN/AR (convention additive, migration 037).
    title_en TEXT,
    title_ar TEXT,
    description_en_html TEXT,
    description_en_md TEXT,
    description_ar_html TEXT,
    description_ar_md TEXT,
    display_order INT DEFAULT 0
);

-- Réalisations d'un service
CREATE TABLE service_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description_html TEXT,
    description_md TEXT,
    -- Traductions auto FR → EN/AR (convention additive, migration 037). type = FR.
    title_en TEXT,
    title_ar TEXT,
    description_en_html TEXT,
    description_en_md TEXT,
    description_ar_html TEXT,
    description_ar_md TEXT,
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
    -- Traductions auto FR → EN/AR (convention additive, migration 037). status = enum FR.
    title_en TEXT,
    title_ar TEXT,
    description_en_html TEXT,
    description_en_md TEXT,
    description_ar_html TEXT,
    description_ar_md TEXT,
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
