-- ============================================================================
-- ███████╗ █████╗  ██████╗
-- ██╔════╝██╔══██╗██╔═══██╗
-- █████╗  ███████║██║   ██║
-- ██╔══╝  ██╔══██║██║▄▄ ██║
-- ██║     ██║  ██║╚██████╔╝
-- ╚═╝     ╚═╝  ╚═╝ ╚══▀▀═╝
-- SERVICE: FAQ (Questions/Réponses publiques)
-- ============================================================================
-- Tables: faq_categories, faq_entries
-- Dépendances externes: IDENTITY (users)
-- Spec: specs/019-faq-backoffice/
-- ============================================================================

-- Catégories de la FAQ (trilingues, ordonnables, désactivables)
CREATE TABLE IF NOT EXISTS faq_categories (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code            VARCHAR(60)  UNIQUE NOT NULL,
    label_fr        VARCHAR(120) NOT NULL,
    label_en        VARCHAR(120),
    label_ar        VARCHAR(120),
    description_fr  TEXT,
    description_en  TEXT,
    description_ar  TEXT,
    display_order   INTEGER      NOT NULL DEFAULT 0,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_faq_categories_code CHECK (code ~ '^[a-z0-9_-]+$')
);

CREATE INDEX IF NOT EXISTS idx_faq_categories_active_order
    ON faq_categories (is_active, display_order);

-- Entrées de la FAQ (question + réponse riche par langue, double colonne *_md/_html)
CREATE TABLE IF NOT EXISTS faq_entries (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id      UUID NOT NULL REFERENCES faq_categories(id) ON DELETE RESTRICT,
    slug             VARCHAR(160) UNIQUE NOT NULL,
    question_fr      VARCHAR(300) NOT NULL,
    question_en      VARCHAR(300),
    question_ar      VARCHAR(300),
    answer_fr_md     TEXT NOT NULL,
    answer_fr_html   TEXT NOT NULL,
    answer_en_md     TEXT,
    answer_en_html   TEXT,
    answer_ar_md     TEXT,
    answer_ar_html   TEXT,
    is_published     BOOLEAN     NOT NULL DEFAULT FALSE,
    published_at     TIMESTAMPTZ,
    display_order    INTEGER     NOT NULL DEFAULT 0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by       UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by       UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_faq_entries_slug CHECK (
        slug ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]$' OR slug ~ '^[a-z0-9]$'
    ),
    CONSTRAINT chk_faq_entries_question_fr_min CHECK (LENGTH(question_fr) >= 3)
);

CREATE INDEX IF NOT EXISTS idx_faq_entries_category_order
    ON faq_entries (category_id, display_order);

CREATE INDEX IF NOT EXISTS idx_faq_entries_published
    ON faq_entries (is_published) WHERE is_published = TRUE;

COMMENT ON TABLE faq_categories IS '[FAQ] Catégories de la FAQ publique (trilingues, ordonnables).';
COMMENT ON TABLE faq_entries IS '[FAQ] Entrées (question + réponse riche en FR/EN/AR) ordonnables au sein d''une catégorie.';
COMMENT ON COLUMN faq_entries.slug IS 'Slug stable pour ancres URL (#slug). Auto-généré depuis question_fr, éditable.';
COMMENT ON COLUMN faq_entries.published_at IS 'Première date de publication. Conservé même après dépublication.';

-- Les triggers `update_*_updated_at` sont créés automatiquement par 99_functions.sql
-- via le DO $$ qui parcourt toutes les tables avec une colonne updated_at.

-- ============================================================================
-- FIN DU SERVICE FAQ
-- ============================================================================
