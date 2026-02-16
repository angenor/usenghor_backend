-- Migration 010 : Associations many-to-many news <-> campuses et news <-> services
-- Remplace les colonnes simples campus_external_id/service_external_id par des tables de liaison
-- Pattern identique à news_tags

BEGIN;

-- 0. Supprimer la vue dépendante (utilise SELECT * sur news)
DROP VIEW IF EXISTS v_published_news;

-- 1. Créer la table de liaison news <-> campuses
CREATE TABLE IF NOT EXISTS news_campuses (
    news_id UUID REFERENCES news(id) ON DELETE CASCADE,
    campus_external_id UUID NOT NULL,  -- → CAMPUS.campuses.id (inter-service, pas de FK)
    PRIMARY KEY (news_id, campus_external_id)
);

COMMENT ON TABLE news_campuses IS '[CONTENT] Liaison N:N actualités <-> campus';

-- 2. Créer la table de liaison news <-> services
CREATE TABLE IF NOT EXISTS news_services (
    news_id UUID REFERENCES news(id) ON DELETE CASCADE,
    service_external_id UUID NOT NULL,  -- → ORGANIZATION.services.id (inter-service, pas de FK)
    PRIMARY KEY (news_id, service_external_id)
);

COMMENT ON TABLE news_services IS '[CONTENT] Liaison N:N actualités <-> services';

-- 3. Migrer les données existantes
INSERT INTO news_campuses (news_id, campus_external_id)
SELECT id, campus_external_id FROM news
WHERE campus_external_id IS NOT NULL
ON CONFLICT DO NOTHING;

INSERT INTO news_services (news_id, service_external_id)
SELECT id, service_external_id FROM news
WHERE service_external_id IS NOT NULL
ON CONFLICT DO NOTHING;

-- 4. Supprimer les anciennes colonnes et index
DROP INDEX IF EXISTS idx_news_campus;
ALTER TABLE news DROP COLUMN IF EXISTS campus_external_id;
ALTER TABLE news DROP COLUMN IF EXISTS service_external_id;

-- 5. Recréer la vue sans les colonnes supprimées
CREATE VIEW v_published_news AS
SELECT *
FROM news
WHERE status = 'published'
AND (visible_from IS NULL OR visible_from <= NOW())
ORDER BY published_at DESC;

COMMIT;
