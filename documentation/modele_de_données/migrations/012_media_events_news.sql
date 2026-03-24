-- Migration 012: Association médiathèque ↔ événements/actualités
-- Ajouter display_order à event_media_library et créer news_media_library

-- 1. Ajouter display_order à event_media_library
ALTER TABLE event_media_library
ADD COLUMN IF NOT EXISTS display_order INT DEFAULT 0;

-- 2. Créer news_media_library
CREATE TABLE IF NOT EXISTS news_media_library (
    news_id UUID REFERENCES news(id) ON DELETE CASCADE,
    album_external_id UUID NOT NULL,
    display_order INT DEFAULT 0,
    PRIMARY KEY (news_id, album_external_id)
);
