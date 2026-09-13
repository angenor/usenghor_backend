-- ============================================================================
-- SERVICE: ENTREPRENEURSHIP (Pôle Entrepreneuriat et Innovation — PEI)
-- ============================================================================
-- Tables: pei_programs, pei_cohorts, pei_resources
-- Dépendances externes: IDENTITY (users), MEDIA (media — référence sans FK)
-- Spec: specs/021-pei-entrepreneurship-core/
-- Convention trilingue additive : champ (FR), champ_en, champ_ar ;
-- rich text : champ_html / champ_md + champ_en_html / champ_en_md / champ_ar_*
-- ============================================================================

CREATE TYPE pei_program_phase AS ENUM
    ('awareness', 'status', 'pre_incubation', 'incubation', 'funding', 'ecosystem');
CREATE TYPE pei_cohort_type   AS ENUM ('fse', 'see');
CREATE TYPE pei_resource_type AS ENUM ('document', 'link', 'video');

-- Dispositifs du parcours entrepreneurial
CREATE TABLE IF NOT EXISTS pei_programs (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code                    VARCHAR(60)  UNIQUE NOT NULL,
    sigle                   VARCHAR(30),
    title                   VARCHAR(200) NOT NULL,
    title_en                VARCHAR(200),
    title_ar                VARCHAR(200),
    phase                   pei_program_phase NOT NULL,
    tagline                 TEXT,
    tagline_en              TEXT,
    tagline_ar              TEXT,
    content_html            TEXT,
    content_md              TEXT,
    content_en_html         TEXT,
    content_en_md           TEXT,
    content_ar_html         TEXT,
    content_ar_md           TEXT,
    highlight               VARCHAR(120),
    highlight_en            VARCHAR(120),
    highlight_ar            VARCHAR(120),
    color                   VARCHAR(20)  NOT NULL DEFAULT 'blue',
    cover_image_external_id UUID,                      -- → MEDIA.media.id (sans FK)
    display_order           INTEGER      NOT NULL DEFAULT 0,
    active                  BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by              UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by              UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_pei_programs_code  CHECK (code ~ '^[a-z0-9][a-z0-9-]*$'),
    CONSTRAINT chk_pei_programs_title CHECK (LENGTH(title) >= 3),
    CONSTRAINT chk_pei_programs_color CHECK (color IN ('blue', 'blue_dark', 'red', 'amber', 'teal'))
);

CREATE INDEX IF NOT EXISTS idx_pei_programs_active_order ON pei_programs (active, display_order);

-- Cohortes (FSE / SEE)
CREATE TABLE IF NOT EXISTS pei_cohorts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code            VARCHAR(60)  UNIQUE NOT NULL,
    label           VARCHAR(200) NOT NULL,
    label_en        VARCHAR(200),
    label_ar        VARCHAR(200),
    year            INTEGER      NOT NULL,
    type            pei_cohort_type NOT NULL,
    focus           TEXT,
    focus_en        TEXT,
    focus_ar        TEXT,
    summary_html    TEXT,
    summary_md      TEXT,
    summary_en_html TEXT,
    summary_en_md   TEXT,
    summary_ar_html TEXT,
    summary_ar_md   TEXT,
    display_order   INTEGER      NOT NULL DEFAULT 0,
    active          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_pei_cohorts_code CHECK (code ~ '^[a-z0-9][a-z0-9-]*$'),
    CONSTRAINT chk_pei_cohorts_year CHECK (year BETWEEN 2000 AND 2100)
);

CREATE INDEX IF NOT EXISTS idx_pei_cohorts_active_order ON pei_cohorts (active, display_order);
CREATE INDEX IF NOT EXISTS idx_pei_cohorts_type_year   ON pei_cohorts (type, year DESC);

-- Boîte à outils (documents, liens, vidéos)
CREATE TABLE IF NOT EXISTS pei_resources (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title             VARCHAR(200) NOT NULL,
    title_en          VARCHAR(200),
    title_ar          VARCHAR(200),
    description       TEXT,
    description_en    TEXT,
    description_ar    TEXT,
    type              pei_resource_type NOT NULL,
    media_external_id UUID,                          -- → MEDIA.media.id (sans FK), type = document
    url               VARCHAR(500),                  -- type = link | video
    category          VARCHAR(120),
    category_en       VARCHAR(120),
    category_ar       VARCHAR(120),
    display_order     INTEGER      NOT NULL DEFAULT 0,
    is_published      BOOLEAN      NOT NULL DEFAULT FALSE,
    published_at      TIMESTAMPTZ,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by        UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by        UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_pei_resources_source CHECK (
        (type = 'document' AND media_external_id IS NOT NULL)
        OR (type IN ('link', 'video') AND url IS NOT NULL AND LENGTH(url) > 0)
    )
);

CREATE INDEX IF NOT EXISTS idx_pei_resources_published_order ON pei_resources (is_published, display_order);

COMMENT ON TABLE pei_programs  IS '[PEI] Dispositifs du parcours entrepreneurial (OSER, SEE, MTI, Senghor''Innov, FSE).';
COMMENT ON TABLE pei_cohorts   IS '[PEI] Cohortes de lauréats FSE / étudiants-entrepreneurs SEE (lauréats en feature 022).';
COMMENT ON TABLE pei_resources IS '[PEI] Boîte à outils : documents de la médiathèque, liens, vidéos.';
COMMENT ON COLUMN pei_programs.color IS 'Couleur nommée de la charte : blue | blue_dark | red | amber | teal.';

-- Les triggers `update_*_updated_at` sont créés automatiquement par 99_functions.sql.
-- Permissions et données initiales : 99_data_init.sql (base neuve) / migration 045 (bases existantes).

-- ============================================================================
-- FIN DU SERVICE ENTREPRENEURSHIP
-- ============================================================================
