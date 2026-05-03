-- ============================================================================
-- Migration 033 — FAQ : catégories + entrées trilingues managées en backoffice
-- ============================================================================
-- Spec: specs/019-faq-backoffice/
-- Idempotente : peut être exécutée plusieurs fois sans effet de bord.
-- Source de vérité : services/15_faq.sql.
-- ============================================================================

BEGIN;

-- 1. Tables
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

-- 2. Triggers updated_at (idempotents)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_faq_categories_updated_at') THEN
        CREATE TRIGGER update_faq_categories_updated_at
            BEFORE UPDATE ON faq_categories
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_faq_entries_updated_at') THEN
        CREATE TRIGGER update_faq_entries_updated_at
            BEFORE UPDATE ON faq_entries
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END$$;

-- 3. Seed catégorie par défaut
INSERT INTO faq_categories (code, label_fr, label_en, label_ar, display_order, is_active)
VALUES ('general', 'Général', 'General', 'عام', 0, TRUE)
ON CONFLICT (code) DO NOTHING;

-- 4. Seed permissions
INSERT INTO permissions (code, name_fr, category) VALUES
    ('faq.view',   'Voir la FAQ',                'faq'),
    ('faq.create', 'Créer des questions FAQ',    'faq'),
    ('faq.edit',   'Modifier des questions FAQ', 'faq'),
    ('faq.delete', 'Supprimer des questions FAQ','faq')
ON CONFLICT (code) DO NOTHING;

-- 5. Attribution des permissions au super_admin (uniquement celles manquantes)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.code = 'super_admin'
  AND p.code IN ('faq.view', 'faq.create', 'faq.edit', 'faq.delete')
ON CONFLICT DO NOTHING;

COMMIT;
