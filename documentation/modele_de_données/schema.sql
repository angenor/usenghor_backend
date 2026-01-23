-- ============================================================================
-- UNIVERSITÉ SENGHOR - SCHÉMA DE BASE DE DONNÉES
-- PostgreSQL 15+
-- ============================================================================

-- ============================================================================
-- EXTENSIONS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TYPES ÉNUMÉRÉS
-- ============================================================================

-- Civilités
CREATE TYPE salutation AS ENUM ('Mr', 'Mrs', 'Dr', 'Pr');

-- Types de formation
CREATE TYPE program_type AS ENUM ('master', 'doctorate', 'university_diploma', 'certificate');

-- Statuts génériques
CREATE TYPE publication_status AS ENUM ('draft', 'published', 'archived');

-- Statuts de candidature
CREATE TYPE application_status AS ENUM ('open', 'closed', 'under_review');

-- Types d'appel à candidature
CREATE TYPE call_type AS ENUM ('application', 'scholarship', 'project', 'recruitment', 'training');

-- Statuts d'appel
CREATE TYPE call_status AS ENUM ('ongoing', 'closed', 'upcoming');

-- Types d'événement
CREATE TYPE event_type AS ENUM ('conference', 'workshop', 'ceremony', 'seminar', 'symposium', 'other');

-- Statuts d'actualité
CREATE TYPE news_highlight_status AS ENUM ('standard', 'featured', 'headline');

-- Types de partenaire
CREATE TYPE partner_type AS ENUM ('charter_operator', 'campus_partner', 'program_partner', 'project_partner', 'other');

-- Situations familiales
CREATE TYPE marital_status AS ENUM ('single', 'married', 'divorced', 'widowed', 'other');

-- Situations professionnelles
CREATE TYPE employment_status AS ENUM ('student', 'teacher', 'civil_servant', 'private_employee', 'ngo_employee', 'unemployed', 'other');

-- Durées d'expérience
CREATE TYPE experience_duration AS ENUM ('less_than_1_year', 'between_1_3_years', 'between_3_5_years', 'between_5_10_years', 'more_than_10_years');

-- Types de média
CREATE TYPE media_type AS ENUM ('image', 'video', 'document', 'audio');

-- Statuts de candidature soumise
CREATE TYPE submitted_application_status AS ENUM ('submitted', 'under_review', 'accepted', 'rejected', 'waitlisted', 'incomplete');

-- Types de contenu éditorial
CREATE TYPE editorial_value_type AS ENUM ('text', 'number', 'json', 'html', 'markdown');

-- Statuts de projet
CREATE TYPE project_status AS ENUM ('ongoing', 'completed', 'suspended', 'planned');

-- ============================================================================
-- TABLES DE RÉFÉRENCE
-- ============================================================================

-- Pays
CREATE TABLE countries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    iso_code CHAR(2) UNIQUE NOT NULL,
    iso_code3 CHAR(3) UNIQUE,
    name_fr VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    name_ar VARCHAR(100),
    phone_code VARCHAR(10),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_countries_iso_code ON countries(iso_code);
CREATE INDEX idx_countries_name_fr ON countries(name_fr);

-- ============================================================================
-- MÉDIAS ET FICHIERS
-- ============================================================================

-- Table centralisée des médias
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type media_type NOT NULL,
    url VARCHAR(500) NOT NULL,
    is_external_url BOOLEAN DEFAULT FALSE,
    size_bytes BIGINT,
    mime_type VARCHAR(100),
    width INT,
    height INT,
    duration_seconds INT,
    alt_text VARCHAR(255),
    credits VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_media_type ON media(type);

-- Albums (regroupement de médias)
CREATE TABLE albums (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status publication_status DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Relation albums <-> médias
CREATE TABLE album_media (
    album_id UUID REFERENCES albums(id) ON DELETE CASCADE,
    media_id UUID REFERENCES media(id) ON DELETE CASCADE,
    display_order INT DEFAULT 0,
    PRIMARY KEY (album_id, media_id)
);

-- ============================================================================
-- UTILISATEURS ET AUTHENTIFICATION
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
    photo_id UUID REFERENCES media(id) ON DELETE SET NULL,
    nationality_id UUID REFERENCES countries(id),
    residence_country_id UUID REFERENCES countries(id),
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

-- Relation utilisateurs <-> rôles
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    campus_id UUID, -- Rattachement optionnel à un campus (FK ajoutée après création de la table campus)
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

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

-- ============================================================================
-- STRUCTURE ORGANISATIONNELLE
-- ============================================================================

-- Départements / Directions
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    mission TEXT,
    icon_id UUID REFERENCES media(id) ON DELETE SET NULL,
    cover_image_id UUID REFERENCES media(id) ON DELETE SET NULL,
    head_id UUID REFERENCES users(id) ON DELETE SET NULL,
    display_order INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Services de département
CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id UUID REFERENCES departments(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    mission TEXT,
    head_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255),
    phone VARCHAR(30),
    album_id UUID REFERENCES albums(id) ON DELETE SET NULL,
    display_order INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Objectifs d'un service
CREATE TABLE service_objectives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    display_order INT DEFAULT 0
);

-- Réalisations d'un service
CREATE TABLE service_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(100),
    cover_image_id UUID REFERENCES media(id) ON DELETE SET NULL,
    achievement_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Projets internes d'un service
CREATE TABLE service_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    cover_image_id UUID REFERENCES media(id) ON DELETE SET NULL,
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
    album_id UUID REFERENCES albums(id) ON DELETE CASCADE,
    PRIMARY KEY (service_id, album_id)
);

-- ============================================================================
-- PARTENAIRES
-- ============================================================================

CREATE TABLE partners (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    logo_id UUID REFERENCES media(id) ON DELETE SET NULL,
    website VARCHAR(500),
    type partner_type NOT NULL,
    country_id UUID REFERENCES countries(id),
    email VARCHAR(255),
    phone VARCHAR(30),
    display_order INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_partners_type ON partners(type);

-- ============================================================================
-- CAMPUS
-- ============================================================================

CREATE TABLE campuses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cover_image_id UUID REFERENCES media(id) ON DELETE SET NULL,
    email VARCHAR(255),
    phone VARCHAR(30),
    country_id UUID REFERENCES countries(id),
    city VARCHAR(100),
    address TEXT,
    postal_code VARCHAR(20),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_headquarters BOOLEAN DEFAULT FALSE,
    head_id UUID REFERENCES users(id) ON DELETE SET NULL,
    album_id UUID REFERENCES albums(id) ON DELETE SET NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_campuses_country ON campuses(country_id);

-- Ajout de la contrainte FK pour user_roles.campus_id
ALTER TABLE user_roles
ADD CONSTRAINT fk_user_roles_campus
FOREIGN KEY (campus_id) REFERENCES campuses(id) ON DELETE SET NULL;

-- Relation campus <-> partenaires
CREATE TABLE campus_partners (
    campus_id UUID REFERENCES campuses(id) ON DELETE CASCADE,
    partner_id UUID REFERENCES partners(id) ON DELETE CASCADE,
    start_date DATE,
    end_date DATE,
    PRIMARY KEY (campus_id, partner_id)
);

-- Équipe d'un campus
CREATE TABLE campus_team (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campus_id UUID REFERENCES campuses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    position VARCHAR(255) NOT NULL,
    display_order INT DEFAULT 0,
    start_date DATE,
    end_date DATE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Médiathèque d'un campus (plusieurs albums possibles)
CREATE TABLE campus_media_library (
    campus_id UUID REFERENCES campuses(id) ON DELETE CASCADE,
    album_id UUID REFERENCES albums(id) ON DELETE CASCADE,
    PRIMARY KEY (campus_id, album_id)
);

-- ============================================================================
-- FORMATIONS
-- ============================================================================

CREATE TABLE programs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(30) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255),
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    teaching_methods TEXT,
    cover_image_id UUID REFERENCES media(id) ON DELETE SET NULL,
    type program_type NOT NULL,
    duration_months INT,
    credits INT,
    degree_awarded VARCHAR(255),
    required_degree TEXT,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    coordinator_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status publication_status DEFAULT 'draft',
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_programs_type ON programs(type);
CREATE INDEX idx_programs_slug ON programs(slug);
CREATE INDEX idx_programs_department ON programs(department_id);

-- Campus où se déroule une formation
CREATE TABLE program_campuses (
    program_id UUID REFERENCES programs(id) ON DELETE CASCADE,
    campus_id UUID REFERENCES campuses(id) ON DELETE CASCADE,
    PRIMARY KEY (program_id, campus_id)
);

-- Partenaires d'une formation
CREATE TABLE program_partners (
    program_id UUID REFERENCES programs(id) ON DELETE CASCADE,
    partner_id UUID REFERENCES partners(id) ON DELETE CASCADE,
    partnership_type VARCHAR(100),
    PRIMARY KEY (program_id, partner_id)
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

-- ============================================================================
-- APPELS À CANDIDATURE
-- ============================================================================

CREATE TABLE application_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    cover_image_id UUID REFERENCES media(id) ON DELETE SET NULL,
    type call_type NOT NULL,
    status call_status DEFAULT 'upcoming',
    opening_date DATE,
    deadline TIMESTAMPTZ,
    program_id UUID REFERENCES programs(id) ON DELETE SET NULL,
    campus_id UUID REFERENCES campuses(id) ON DELETE SET NULL,
    program_start_date DATE,
    program_end_date DATE,
    target_audience TEXT,
    registration_fee DECIMAL(10, 2),
    currency VARCHAR(10) DEFAULT 'EUR',
    external_form_url VARCHAR(500),
    use_internal_form BOOLEAN DEFAULT TRUE,
    publication_status publication_status DEFAULT 'draft',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_application_calls_type ON application_calls(type);
CREATE INDEX idx_application_calls_status ON application_calls(status);
CREATE INDEX idx_application_calls_deadline ON application_calls(deadline);
CREATE INDEX idx_application_calls_slug ON application_calls(slug);

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

-- ============================================================================
-- CANDIDATURES SOUMISES
-- ============================================================================

-- Candidatures formation
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_number VARCHAR(50) UNIQUE NOT NULL,
    call_id UUID REFERENCES application_calls(id) ON DELETE SET NULL,
    program_id UUID REFERENCES programs(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Informations personnelles (peuvent différer du profil utilisateur)
    salutation salutation,
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    birth_date DATE,
    birth_city VARCHAR(100),
    birth_country_id UUID REFERENCES countries(id),
    nationality_id UUID REFERENCES countries(id),
    marital_status marital_status,
    employment_status employment_status,
    employment_status_other VARCHAR(255),

    -- Coordonnées
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country_id UUID REFERENCES countries(id),
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
    employer_country_id UUID REFERENCES countries(id),
    employer_phone VARCHAR(30),
    employer_email VARCHAR(255),
    experience_duration experience_duration,

    -- Formation académique
    highest_degree_level VARCHAR(100),
    highest_degree_title VARCHAR(255),
    degree_date DATE,
    degree_location VARCHAR(255),

    -- Statut
    status submitted_application_status DEFAULT 'submitted',
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    reviewer_id UUID REFERENCES users(id),
    review_notes TEXT,
    review_score DECIMAL(5, 2),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_applications_reference ON applications(reference_number);
CREATE INDEX idx_applications_call ON applications(call_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_user ON applications(user_id);

-- Diplômes du candidat
CREATE TABLE application_degrees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    year INT,
    institution VARCHAR(255),
    city VARCHAR(100),
    country_id UUID REFERENCES countries(id),
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
    media_id UUID REFERENCES media(id) ON DELETE SET NULL,
    is_valid BOOLEAN,
    validation_comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- ÉVÉNEMENTS
-- ============================================================================

CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    content TEXT, -- Contenu riche
    cover_image_id UUID REFERENCES media(id) ON DELETE SET NULL,
    type event_type NOT NULL,
    type_other VARCHAR(100), -- Si type = 'other'
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ,
    venue VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    country_id UUID REFERENCES countries(id),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_online BOOLEAN DEFAULT FALSE,
    video_conference_link VARCHAR(500),
    registration_required BOOLEAN DEFAULT FALSE,
    registration_link VARCHAR(500),
    max_attendees INT,
    campus_id UUID REFERENCES campuses(id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    project_id UUID, -- FK ajoutée après création de la table projects
    organizer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    album_id UUID REFERENCES albums(id) ON DELETE SET NULL,
    status publication_status DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_date ON events(start_date);
CREATE INDEX idx_events_project ON events(project_id);
CREATE INDEX idx_events_type ON events(type);
CREATE INDEX idx_events_slug ON events(slug);

-- Partenaires d'un événement
CREATE TABLE event_partners (
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    partner_id UUID REFERENCES partners(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, partner_id)
);

-- Inscriptions à un événement
CREATE TABLE event_registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
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

-- Médiathèque d'un événement (plusieurs albums possibles)
CREATE TABLE event_media_library (
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    album_id UUID REFERENCES albums(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, album_id)
);

-- ============================================================================
-- ACTUALITÉS
-- ============================================================================

CREATE TABLE news (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    summary TEXT,
    content TEXT, -- Contenu riche (HTML/Markdown)
    cover_image_id UUID REFERENCES media(id) ON DELETE SET NULL,
    video_url VARCHAR(500),
    highlight_status news_highlight_status DEFAULT 'standard',
    status publication_status DEFAULT 'draft',
    published_at TIMESTAMPTZ,
    visible_from TIMESTAMPTZ,
    campus_id UUID REFERENCES campuses(id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    service_id UUID REFERENCES services(id) ON DELETE SET NULL,
    event_id UUID REFERENCES events(id) ON DELETE SET NULL,
    project_id UUID, -- FK ajoutée après création de la table projects
    author_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_news_published_at ON news(published_at);
CREATE INDEX idx_news_status ON news(status, highlight_status);
CREATE INDEX idx_news_slug ON news(slug);
CREATE INDEX idx_news_project ON news(project_id);

-- Photos d'une actualité
CREATE TABLE news_media (
    news_id UUID REFERENCES news(id) ON DELETE CASCADE,
    media_id UUID REFERENCES media(id) ON DELETE CASCADE,
    display_order INT DEFAULT 0,
    PRIMARY KEY (news_id, media_id)
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

CREATE TABLE news_tags (
    news_id UUID REFERENCES news(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (news_id, tag_id)
);

-- ============================================================================
-- PROJETS
-- ============================================================================

-- Catégories de projets
CREATE TABLE project_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    summary TEXT,
    description TEXT,
    cover_image_id UUID REFERENCES media(id) ON DELETE SET NULL,
    start_date DATE,
    end_date DATE,
    budget DECIMAL(15, 2),
    currency VARCHAR(10) DEFAULT 'EUR',
    beneficiaries TEXT,
    status project_status DEFAULT 'planned',
    publication_status publication_status DEFAULT 'draft',
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    album_id UUID REFERENCES albums(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_slug ON projects(slug);

-- Pays concernés par un projet
CREATE TABLE project_countries (
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    country_id UUID REFERENCES countries(id) ON DELETE CASCADE,
    PRIMARY KEY (project_id, country_id)
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
    partner_id UUID REFERENCES partners(id) ON DELETE CASCADE,
    partner_role VARCHAR(255),
    PRIMARY KEY (project_id, partner_id)
);

-- Appels liés à un projet
CREATE TABLE project_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status call_status DEFAULT 'upcoming',
    conditions TEXT,
    type call_type,
    deadline TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Médiathèque d'un projet (plusieurs albums possibles)
CREATE TABLE project_media_library (
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    album_id UUID REFERENCES albums(id) ON DELETE CASCADE,
    PRIMARY KEY (project_id, album_id)
);

-- Ajout des FK vers projects pour events et news
ALTER TABLE events
ADD CONSTRAINT fk_events_project
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL;

ALTER TABLE news
ADD CONSTRAINT fk_news_project
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL;

-- ============================================================================
-- CONTENUS ÉDITORIAUX ET CONFIGURATION
-- ============================================================================

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
    modified_by UUID REFERENCES users(id),
    modified_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- NEWSLETTER
-- ============================================================================

-- Abonnés à la newsletter
CREATE TABLE newsletter_subscribers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    last_name VARCHAR(100),
    first_name VARCHAR(100),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    active BOOLEAN DEFAULT TRUE,
    unsubscribe_token VARCHAR(255) UNIQUE,
    source VARCHAR(100), -- d'où vient l'inscription
    subscribed_at TIMESTAMPTZ DEFAULT NOW(),
    unsubscribed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_newsletter_subscribers_email ON newsletter_subscribers(email);

-- Campagnes de newsletter
CREATE TABLE newsletter_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    html_content TEXT,
    text_content TEXT,
    status VARCHAR(50) DEFAULT 'draft', -- draft, scheduled, sent
    scheduled_send_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    recipient_count INT DEFAULT 0,
    open_count INT DEFAULT 0,
    click_count INT DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Historique d'envoi par destinataire
CREATE TABLE newsletter_sends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES newsletter_campaigns(id) ON DELETE CASCADE,
    subscriber_id UUID REFERENCES newsletter_subscribers(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'sent', -- sent, opened, clicked, error
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE INDEX idx_newsletter_sends_campaign ON newsletter_sends(campaign_id);

-- ============================================================================
-- AUDIT ET LOGS
-- ============================================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
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

-- ============================================================================
-- FONCTIONS ET TRIGGERS
-- ============================================================================

-- Fonction pour mettre à jour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Application du trigger sur toutes les tables avec updated_at
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT table_name
        FROM information_schema.columns
        WHERE column_name = 'updated_at'
        AND table_schema = 'public'
    LOOP
        EXECUTE format('
            CREATE TRIGGER update_%I_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', t, t);
    END LOOP;
END;
$$ language 'plpgsql';

-- Fonction pour générer un numéro de dossier de candidature
CREATE OR REPLACE FUNCTION generate_application_reference()
RETURNS TRIGGER AS $$
BEGIN
    NEW.reference_number = 'APP-' || TO_CHAR(NOW(), 'YYYY') || '-' || LPAD(NEXTVAL('seq_application_reference')::TEXT, 6, '0');
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Séquence pour les numéros de dossier
CREATE SEQUENCE IF NOT EXISTS seq_application_reference START 1;

-- Trigger pour générer le numéro de dossier
CREATE TRIGGER trigger_generate_application_reference
BEFORE INSERT ON applications
FOR EACH ROW
WHEN (NEW.reference_number IS NULL)
EXECUTE FUNCTION generate_application_reference();

-- ============================================================================
-- DONNÉES INITIALES
-- ============================================================================

-- Rôles par défaut
INSERT INTO roles (code, name_fr, description, hierarchy_level) VALUES
('super_admin', 'Super Administrateur', 'Accès complet à toutes les fonctionnalités', 100),
('admin', 'Administrateur', 'Administration générale de la plateforme', 80),
('campus_admin', 'Administrateur Campus', 'Administration d''un campus spécifique', 60),
('editor', 'Éditeur', 'Création et modification de contenus', 40),
('moderator', 'Modérateur', 'Modération des contenus et candidatures', 30),
('user', 'Utilisateur', 'Utilisateur standard inscrit', 10);

-- Catégories de contenus éditoriaux
INSERT INTO editorial_categories (code, name, description) VALUES
('statistics', 'Statistiques', 'Chiffres clés et statistiques'),
('values', 'Valeurs', 'Valeurs de l''université'),
('strategy', 'Stratégie', 'Éléments stratégiques'),
('contact', 'Contact', 'Informations de contact'),
('social_media', 'Réseaux sociaux', 'Liens vers les réseaux sociaux'),
('legal', 'Mentions légales', 'Contenus juridiques');

-- Permissions de base
INSERT INTO permissions (code, name_fr, category) VALUES
-- Gestion des utilisateurs
('users.view', 'Voir les utilisateurs', 'users'),
('users.create', 'Créer des utilisateurs', 'users'),
('users.edit', 'Modifier les utilisateurs', 'users'),
('users.delete', 'Supprimer des utilisateurs', 'users'),
('users.roles', 'Gérer les rôles des utilisateurs', 'users'),
-- Gestion des formations
('programs.view', 'Voir les formations', 'programs'),
('programs.create', 'Créer des formations', 'programs'),
('programs.edit', 'Modifier les formations', 'programs'),
('programs.delete', 'Supprimer des formations', 'programs'),
-- Gestion des candidatures
('applications.view', 'Voir les candidatures', 'applications'),
('applications.evaluate', 'Évaluer les candidatures', 'applications'),
('applications.export', 'Exporter les candidatures', 'applications'),
-- Gestion des événements
('events.view', 'Voir les événements', 'events'),
('events.create', 'Créer des événements', 'events'),
('events.edit', 'Modifier les événements', 'events'),
('events.delete', 'Supprimer des événements', 'events'),
-- Gestion des actualités
('news.view', 'Voir les actualités', 'news'),
('news.create', 'Créer des actualités', 'news'),
('news.edit', 'Modifier les actualités', 'news'),
('news.delete', 'Supprimer des actualités', 'news'),
-- Gestion des campus
('campuses.view', 'Voir les campus', 'campuses'),
('campuses.create', 'Créer des campus', 'campuses'),
('campuses.edit', 'Modifier les campus', 'campuses'),
('campuses.delete', 'Supprimer des campus', 'campuses'),
-- Gestion des partenaires
('partners.view', 'Voir les partenaires', 'partners'),
('partners.create', 'Créer des partenaires', 'partners'),
('partners.edit', 'Modifier les partenaires', 'partners'),
('partners.delete', 'Supprimer des partenaires', 'partners'),
-- Gestion des contenus éditoriaux
('editorial.view', 'Voir les contenus éditoriaux', 'editorial'),
('editorial.edit', 'Modifier les contenus éditoriaux', 'editorial'),
-- Gestion de la newsletter
('newsletter.view', 'Voir les newsletters', 'newsletter'),
('newsletter.create', 'Créer des newsletters', 'newsletter'),
('newsletter.send', 'Envoyer des newsletters', 'newsletter'),
-- Administration
('admin.settings', 'Gérer les paramètres', 'admin'),
('admin.audit', 'Voir les logs d''audit', 'admin');

-- Attribution de toutes les permissions au super_admin
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.code = 'super_admin';

-- ============================================================================
-- VUES UTILES
-- ============================================================================

-- Vue des formations avec leurs campus
CREATE VIEW v_programs_campuses AS
SELECT
    p.*,
    d.name as department_name,
    ARRAY_AGG(DISTINCT c.name) FILTER (WHERE c.id IS NOT NULL) as campus_names,
    ARRAY_AGG(DISTINCT c.id) FILTER (WHERE c.id IS NOT NULL) as campus_ids
FROM programs p
LEFT JOIN departments d ON p.department_id = d.id
LEFT JOIN program_campuses pc ON p.id = pc.program_id
LEFT JOIN campuses c ON pc.campus_id = c.id
GROUP BY p.id, d.name;

-- Vue des événements à venir
CREATE VIEW v_upcoming_events AS
SELECT
    e.*,
    c.name as campus_name,
    co.name_fr as country_name
FROM events e
LEFT JOIN campuses c ON e.campus_id = c.id
LEFT JOIN countries co ON e.country_id = co.id
WHERE e.status = 'published'
AND e.start_date >= NOW()
ORDER BY e.start_date ASC;

-- Vue des actualités publiées
CREATE VIEW v_published_news AS
SELECT
    n.*,
    u.last_name as author_last_name,
    u.first_name as author_first_name,
    c.name as campus_name,
    d.name as department_name
FROM news n
LEFT JOIN users u ON n.author_id = u.id
LEFT JOIN campuses c ON n.campus_id = c.id
LEFT JOIN departments d ON n.department_id = d.id
WHERE n.status = 'published'
AND (n.visible_from IS NULL OR n.visible_from <= NOW())
ORDER BY n.published_at DESC;

-- Vue statistiques des candidatures par appel
CREATE VIEW v_application_statistics AS
SELECT
    ac.id as call_id,
    ac.title as call_title,
    COUNT(a.id) as total_applications,
    COUNT(CASE WHEN a.status = 'submitted' THEN 1 END) as submitted,
    COUNT(CASE WHEN a.status = 'under_review' THEN 1 END) as under_review,
    COUNT(CASE WHEN a.status = 'accepted' THEN 1 END) as accepted,
    COUNT(CASE WHEN a.status = 'rejected' THEN 1 END) as rejected,
    COUNT(CASE WHEN a.status = 'waitlisted' THEN 1 END) as waitlisted
FROM application_calls ac
LEFT JOIN applications a ON ac.id = a.call_id
GROUP BY ac.id, ac.title;

-- ============================================================================
-- COMMENTAIRES POUR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE users IS 'Utilisateurs inscrits sur la plateforme';
COMMENT ON TABLE roles IS 'Rôles définissant les permissions des utilisateurs';
COMMENT ON TABLE programs IS 'Formations proposées par l''Université Senghor';
COMMENT ON TABLE application_calls IS 'Appels à candidature (formations, bourses, projets, recrutements)';
COMMENT ON TABLE applications IS 'Candidatures soumises par les utilisateurs';
COMMENT ON TABLE events IS 'Événements organisés par l''université';
COMMENT ON TABLE news IS 'Articles d''actualité et news';
COMMENT ON TABLE campuses IS 'Campus de l''université (siège et externalisés)';
COMMENT ON TABLE partners IS 'Partenaires de l''université';
COMMENT ON TABLE projects IS 'Projets de l''université';
COMMENT ON TABLE editorial_contents IS 'Contenus de configuration dynamiques (statistiques, valeurs, etc.)';
COMMENT ON TABLE newsletter_subscribers IS 'Abonnés à la newsletter';
COMMENT ON TABLE media IS 'Fichiers médias centralisés (images, vidéos, documents)';
