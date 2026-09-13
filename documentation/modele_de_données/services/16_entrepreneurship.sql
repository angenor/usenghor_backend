-- ============================================================================
-- SERVICE: ENTREPRENEURSHIP (Pôle Entrepreneuriat et Innovation — PEI)
-- ============================================================================
-- Tables: pei_programs, pei_cohorts, pei_resources, pei_laureates, pei_partners
-- Dépendances externes: IDENTITY (users), MEDIA (media — référence sans FK),
--                       PARTNER (partners — FK avec cascade, pei_partners)
-- Spec: specs/021-pei-entrepreneurship-core/, specs/022-pei-laureates-partners/
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

CREATE TYPE pei_laureate_type  AS ENUM ('fse_laureate', 'student_entrepreneur');
CREATE TYPE pei_partner_family AS ENUM ('academic', 'support', 'international');

-- Portraits : lauréats du FSE et étudiants-entrepreneurs (spec 022)
CREATE TABLE IF NOT EXISTS pei_laureates (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cohort_id           UUID NOT NULL REFERENCES pei_cohorts(id) ON DELETE RESTRICT,
    type                pei_laureate_type NOT NULL,
    full_name           VARCHAR(200) NOT NULL,
    project_name        VARCHAR(200) NOT NULL,
    department_label    VARCHAR(200),
    department_label_en VARCHAR(200),
    department_label_ar VARCHAR(200),
    quote               TEXT,
    quote_en            TEXT,
    quote_ar            TEXT,
    photo_external_id   UUID,                          -- → MEDIA.media.id (sans FK)
    website_url         VARCHAR(500),
    linkedin_url        VARCHAR(500),
    instagram_url       VARCHAR(500),
    facebook_url        VARCHAR(500),
    video_url           VARCHAR(500),
    grant_amount        NUMERIC(10,2),                 -- euros
    is_featured         BOOLEAN      NOT NULL DEFAULT FALSE,
    is_published        BOOLEAN      NOT NULL DEFAULT FALSE,
    published_at        TIMESTAMPTZ,
    display_order       INTEGER      NOT NULL DEFAULT 0,   -- relatif à la cohorte
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by          UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_pei_laureates_full_name    CHECK (char_length(full_name) >= 2),
    CONSTRAINT chk_pei_laureates_project_name CHECK (char_length(project_name) >= 2),
    CONSTRAINT chk_pei_laureates_quote_len    CHECK (
        (quote    IS NULL OR char_length(quote)    <= 600) AND
        (quote_en IS NULL OR char_length(quote_en) <= 600) AND
        (quote_ar IS NULL OR char_length(quote_ar) <= 600)),
    CONSTRAINT chk_pei_laureates_grant        CHECK (grant_amount IS NULL OR grant_amount >= 0)
);

CREATE INDEX IF NOT EXISTS idx_pei_laureates_cohort_order   ON pei_laureates (cohort_id, display_order);
CREATE INDEX IF NOT EXISTS idx_pei_laureates_published_type ON pei_laureates (is_published, type);

-- Partenaires du pôle : rattachement + famille (les partenaires vivent dans partners)
CREATE TABLE IF NOT EXISTS pei_partners (
    partner_id     UUID PRIMARY KEY REFERENCES partners(id) ON DELETE CASCADE,
    family         pei_partner_family NOT NULL,
    display_order  INTEGER     NOT NULL DEFAULT 0,       -- relatif à la famille
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by     UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by     UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pei_partners_family_order ON pei_partners (family, display_order);

COMMENT ON TABLE pei_programs  IS '[PEI] Dispositifs du parcours entrepreneurial (OSER, SEE, MTI, Senghor''Innov, FSE).';
COMMENT ON TABLE pei_cohorts   IS '[PEI] Cohortes de lauréats FSE / étudiants-entrepreneurs SEE.';
COMMENT ON TABLE pei_resources IS '[PEI] Boîte à outils : documents de la médiathèque, liens, vidéos.';
COMMENT ON TABLE pei_laureates IS '[PEI] Portraits de lauréats FSE et d''étudiants-entrepreneurs (ordre relatif à la cohorte).';
COMMENT ON TABLE pei_partners  IS '[PEI] Rattachement d''un partenaire (table partners) à une famille du pôle (ordre relatif à la famille).';
COMMENT ON COLUMN pei_programs.color IS 'Couleur nommée de la charte : blue | blue_dark | red | amber | teal.';

-- Les triggers `update_*_updated_at` sont créés automatiquement par 99_functions.sql.
-- Permissions et données initiales : 99_data_init.sql (base neuve) / migration 045 (bases existantes).

-- ============================================================================
-- FIN DU SERVICE ENTREPRENEURSHIP
-- ============================================================================
