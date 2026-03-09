-- ============================================================================
--  █████╗  ██████╗ █████╗ ██████╗ ███████╗███╗   ███╗██╗ ██████╗
-- ██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝████╗ ████║██║██╔════╝
-- ███████║██║     ███████║██║  ██║█████╗  ██╔████╔██║██║██║
-- ██╔══██║██║     ██╔══██║██║  ██║██╔══╝  ██║╚██╔╝██║██║██║
-- ██║  ██║╚██████╗██║  ██║██████╔╝███████╗██║ ╚═╝ ██║██║╚██████╗
-- ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝ ╚═════╝
-- SERVICE: ACADEMIC (Formations et programmes)
-- ============================================================================
-- Tables: program_fields, programs, program_campuses, program_partners,
--         program_semesters, program_courses, program_career_opportunities, program_skills
-- Dépendances externes: ORGANIZATION (sector_id), IDENTITY (coordinator_id),
--                       MEDIA (cover_image_id), CAMPUS (campus_id), PARTNER (partner_id)
-- ============================================================================

-- Types ENUM spécifiques à ce service
CREATE TYPE program_type AS ENUM ('master', 'doctorate', 'university_diploma', 'certificate');

-- Champs disciplinaires (pour les certificats)
CREATE TABLE program_fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_program_fields_slug ON program_fields(slug);

CREATE TABLE programs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(30) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255),
    slug VARCHAR(255) UNIQUE NOT NULL,
    description_html TEXT,
    description_md TEXT,
    teaching_methods_html TEXT,
    teaching_methods_md TEXT,
    objectives JSONB,
    target_audience JSONB,
    format_html TEXT,
    format_md TEXT,
    evaluation_methods_html TEXT,
    evaluation_methods_md TEXT,
    -- Références INTER-SERVICE (pas de FK)
    cover_image_external_id UUID,  -- → MEDIA.media.id
    sector_external_id UUID,        -- → ORGANIZATION.sectors.id
    coordinator_external_id UUID,  -- → IDENTITY.users.id
    field_id UUID REFERENCES program_fields(id) ON DELETE SET NULL,  -- Champ disciplinaire (certificats)
    type program_type NOT NULL,
    duration_months INT,
    credits INT,
    degree_awarded VARCHAR(255),
    required_degree TEXT,
    status publication_status DEFAULT 'draft',
    is_featured BOOLEAN DEFAULT FALSE,
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_programs_type ON programs(type);
CREATE INDEX idx_programs_slug ON programs(slug);
CREATE INDEX idx_programs_sector ON programs(sector_external_id);
CREATE INDEX idx_programs_field ON programs(field_id);
CREATE INDEX idx_programs_featured ON programs(is_featured) WHERE is_featured = TRUE;

-- Campus où se déroule une formation
CREATE TABLE program_campuses (
    program_id UUID REFERENCES programs(id) ON DELETE CASCADE,
    campus_external_id UUID NOT NULL,  -- → CAMPUS.campuses.id
    PRIMARY KEY (program_id, campus_external_id)
);

-- Partenaires d'une formation
CREATE TABLE program_partners (
    program_id UUID REFERENCES programs(id) ON DELETE CASCADE,
    partner_external_id UUID NOT NULL,  -- → PARTNER.partners.id
    partnership_type VARCHAR(100),
    PRIMARY KEY (program_id, partner_external_id)
);

-- Programme de formation (semestres)
CREATE TABLE program_semesters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_id UUID REFERENCES programs(id) ON DELETE CASCADE,
    number INT NOT NULL,
    title VARCHAR(255),
    credits INT DEFAULT 1,
    display_order INT DEFAULT 0,
    UNIQUE (program_id, number)
);

-- Unités d'enseignement (UE) d'un semestre
CREATE TABLE program_courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    semester_id UUID REFERENCES program_semesters(id) ON DELETE CASCADE,
    code VARCHAR(20),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    credits INT,
    lecture_hours INT DEFAULT 0,
    tutorial_hours INT DEFAULT 0,
    practical_hours INT DEFAULT 0,
    coefficient DECIMAL(4, 2),
    display_order INT DEFAULT 0
);

-- Débouchés d'une formation
CREATE TABLE program_career_opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_id UUID REFERENCES programs(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    display_order INT DEFAULT 0
);

-- Compétences visées par une formation
CREATE TABLE program_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_id UUID REFERENCES programs(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    display_order INT DEFAULT 0
);

COMMENT ON TABLE program_fields IS '[ACADEMIC] Champs disciplinaires pour les certificats';
COMMENT ON TABLE programs IS '[ACADEMIC] Formations proposées par l''Université Senghor';
COMMENT ON COLUMN programs.field_id IS 'Champ disciplinaire (uniquement pour les certificats)';
COMMENT ON COLUMN programs.sector_external_id IS 'Référence externe vers ORGANIZATION.sectors.id';
COMMENT ON COLUMN programs.coordinator_external_id IS 'Référence externe vers IDENTITY.users.id';
COMMENT ON COLUMN programs.is_featured IS 'Formation mise à la une sur la page d''accueil';
COMMENT ON COLUMN program_campuses.campus_external_id IS 'Référence externe vers CAMPUS.campuses.id';
COMMENT ON COLUMN program_partners.partner_external_id IS 'Référence externe vers PARTNER.partners.id';

-- Médiathèque des programmes (albums associés)
CREATE TABLE program_media_library (
    program_id UUID REFERENCES programs(id) ON DELETE CASCADE,
    album_external_id UUID NOT NULL,  -- → MEDIA.albums.id
    PRIMARY KEY (program_id, album_external_id)
);

COMMENT ON TABLE program_media_library IS '[ACADEMIC] Albums de la médiathèque associés à un programme';

-- ============================================================================
-- FIN DU SERVICE ACADEMIC
-- ============================================================================
