-- ============================================================================
--  █████╗ ██████╗ ██████╗ ██╗     ██╗ ██████╗ █████╗ ████████╗██╗ ██████╗ ███╗   ██╗
-- ██╔══██╗██╔══██╗██╔══██╗██║     ██║██╔════╝██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║
-- ███████║██████╔╝██████╔╝██║     ██║██║     ███████║   ██║   ██║██║   ██║██╔██╗ ██║
-- ██╔══██║██╔═══╝ ██╔═══╝ ██║     ██║██║     ██╔══██║   ██║   ██║██║   ██║██║╚██╗██║
-- ██║  ██║██║     ██║     ███████╗██║╚██████╗██║  ██║   ██║   ██║╚██████╔╝██║ ╚████║
-- ╚═╝  ╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
-- SERVICE: APPLICATION (Appels à candidature et candidatures)
-- ============================================================================
-- Tables: application_calls, call_eligibility_criteria, call_coverage,
--         call_required_documents, call_schedule, application_call_media_library,
--         applications, application_degrees, application_documents
-- Dépendances externes: ACADEMIC (program_id), CAMPUS (campus_id),
--                       IDENTITY (user_id, reviewer_id), MEDIA (cover_image_id),
--                       CORE (countries), PROJECT (project_id)
-- ============================================================================

-- Types ENUM spécifiques à ce service
CREATE TYPE call_type AS ENUM ('application', 'scholarship', 'project', 'recruitment', 'training');
CREATE TYPE call_status AS ENUM ('ongoing', 'closed', 'upcoming');
CREATE TYPE submitted_application_status AS ENUM ('submitted', 'under_review', 'accepted', 'rejected', 'waitlisted', 'incomplete');
CREATE TYPE marital_status AS ENUM ('single', 'married', 'divorced', 'widowed', 'other');
CREATE TYPE employment_status AS ENUM ('student', 'teacher', 'civil_servant', 'private_employee', 'ngo_employee', 'unemployed', 'other');
CREATE TYPE experience_duration AS ENUM ('less_than_1_year', 'between_1_3_years', 'between_3_5_years', 'between_5_10_years', 'more_than_10_years');

-- Appels à candidature
CREATE TABLE application_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description_html TEXT,
    description_md TEXT,
    -- Références INTER-SERVICE (pas de FK)
    cover_image_external_id UUID,  -- → MEDIA.media.id
    program_external_id UUID,      -- → ACADEMIC.programs.id
    campus_external_id UUID,       -- → CAMPUS.campuses.id
    country_external_id UUID,      -- → CORE.countries.id (pays du lieu de formation/exercice)
    project_external_id UUID,      -- → PROJECT.projects.id
    created_by_external_id UUID,   -- → IDENTITY.users.id
    location_address TEXT,         -- Adresse exacte du lieu de formation/exercice
    type call_type NOT NULL,
    status call_status DEFAULT 'upcoming',
    opening_date DATE,
    deadline TIMESTAMPTZ,
    program_start_date DATE,
    program_end_date DATE,
    target_audience_html TEXT,
    target_audience_md TEXT,
    registration_fee DECIMAL(10, 2),
    currency VARCHAR(10) DEFAULT 'EUR',
    external_form_url VARCHAR(500),
    use_internal_form BOOLEAN DEFAULT TRUE,
    publication_status publication_status DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_application_calls_type ON application_calls(type);
CREATE INDEX idx_application_calls_status ON application_calls(status);
CREATE INDEX idx_application_calls_deadline ON application_calls(deadline);
CREATE INDEX idx_application_calls_slug ON application_calls(slug);
CREATE INDEX idx_application_calls_program ON application_calls(program_external_id);
CREATE INDEX idx_application_calls_country ON application_calls(country_external_id);
CREATE INDEX idx_application_calls_project ON application_calls(project_external_id);

-- Critères d'éligibilité d'un appel
CREATE TABLE call_eligibility_criteria (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID REFERENCES application_calls(id) ON DELETE CASCADE,
    criterion TEXT NOT NULL,
    is_mandatory BOOLEAN DEFAULT TRUE,
    display_order INT DEFAULT 0
);

-- Prises en charge d'un appel
CREATE TABLE call_coverage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID REFERENCES application_calls(id) ON DELETE CASCADE,
    item VARCHAR(255) NOT NULL,
    description TEXT,
    display_order INT DEFAULT 0
);

-- Documents requis pour un appel
CREATE TABLE call_required_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID REFERENCES application_calls(id) ON DELETE CASCADE,
    document_name VARCHAR(255) NOT NULL,
    description TEXT,
    is_mandatory BOOLEAN DEFAULT TRUE,
    accepted_formats VARCHAR(100), -- ex: 'pdf,doc,docx'
    max_size_mb INT,
    display_order INT DEFAULT 0
);

-- Calendrier récapitulatif d'un appel
CREATE TABLE call_schedule (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID REFERENCES application_calls(id) ON DELETE CASCADE,
    step VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    description TEXT,
    display_order INT DEFAULT 0
);

-- Médiathèque d'un appel à candidature (plusieurs albums possibles)
CREATE TABLE application_call_media_library (
    call_id UUID REFERENCES application_calls(id) ON DELETE CASCADE,
    album_external_id UUID NOT NULL,  -- → MEDIA.albums.id
    PRIMARY KEY (call_id, album_external_id)
);

-- Candidatures soumises
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_number VARCHAR(50) UNIQUE NOT NULL,
    call_id UUID REFERENCES application_calls(id) ON DELETE SET NULL,
    -- Références INTER-SERVICE (pas de FK)
    program_external_id UUID,     -- → ACADEMIC.programs.id
    user_external_id UUID,        -- → IDENTITY.users.id
    reviewer_external_id UUID,    -- → IDENTITY.users.id

    -- Informations personnelles (peuvent différer du profil utilisateur)
    salutation salutation,
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    birth_date DATE,
    birth_city VARCHAR(100),
    -- Références pays INTER-SERVICE
    birth_country_external_id UUID,     -- → CORE.countries.id
    nationality_external_id UUID,       -- → CORE.countries.id
    country_external_id UUID,           -- → CORE.countries.id
    employer_country_external_id UUID,  -- → CORE.countries.id
    marital_status marital_status,
    employment_status employment_status,
    employment_status_other VARCHAR(255),

    -- Coordonnées
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    phone VARCHAR(30),
    phone_whatsapp VARCHAR(30),
    email VARCHAR(255) NOT NULL,

    -- Informations professionnelles
    has_work_experience BOOLEAN DEFAULT FALSE,
    current_job VARCHAR(255),
    job_title VARCHAR(255),
    employer_name VARCHAR(255),
    employer_address TEXT,
    employer_city VARCHAR(100),
    employer_phone VARCHAR(30),
    employer_email VARCHAR(255),
    experience_duration experience_duration,

    -- Formation académique
    highest_degree_level VARCHAR(100),
    highest_degree_title VARCHAR(255),
    degree_date DATE,
    degree_location VARCHAR(255),

    -- Motivation (candidatures spontanées)
    motivation_text TEXT,

    -- Statut
    status submitted_application_status DEFAULT 'submitted',
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,
    review_score DECIMAL(5, 2),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_applications_reference ON applications(reference_number);
CREATE INDEX idx_applications_call ON applications(call_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_user ON applications(user_external_id);

-- Diplômes du candidat
CREATE TABLE application_degrees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    year INT,
    institution VARCHAR(255),
    city VARCHAR(100),
    country_external_id UUID,  -- → CORE.countries.id
    specialization VARCHAR(255),
    honors VARCHAR(50),
    display_order INT DEFAULT 0
);

-- Documents soumis par le candidat
CREATE TABLE application_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    required_document_id UUID REFERENCES call_required_documents(id) ON DELETE SET NULL,
    document_name VARCHAR(255) NOT NULL,
    media_external_id UUID,  -- → MEDIA.media.id
    is_valid BOOLEAN,
    validation_comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE application_calls IS '[APPLICATION] Appels à candidature (formations, bourses, projets, recrutements)';
COMMENT ON TABLE applications IS '[APPLICATION] Candidatures soumises par les utilisateurs';
COMMENT ON COLUMN application_calls.program_external_id IS 'Référence externe vers ACADEMIC.programs.id';
COMMENT ON COLUMN applications.user_external_id IS 'Référence externe vers IDENTITY.users.id';

-- ============================================================================
-- FIN DU SERVICE APPLICATION
-- ============================================================================
