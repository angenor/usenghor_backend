-- Migration 007: Association actualités-programmes et médiathèque des programmes
-- Date: 2026-02-10
-- Description: Ajoute program_external_id à la table news pour permettre
--              l'association d'actualités à un programme de formation.
--              Crée la table program_media_library pour la
--              médiathèque des programmes (albums associés).

BEGIN;

-- 1) Ajouter program_external_id à la table news
-- Référence externe vers ACADEMIC.programs.id (pas de FK, pattern inter-service)
ALTER TABLE news
    ADD COLUMN IF NOT EXISTS program_external_id UUID;

COMMENT ON COLUMN news.program_external_id IS 'Référence externe vers ACADEMIC.programs.id';

CREATE INDEX IF NOT EXISTS idx_news_program ON news(program_external_id);

-- 2) Créer la table de jonction pour la médiathèque des programmes
-- Pattern identique à application_call_media_library
CREATE TABLE IF NOT EXISTS program_media_library (
    program_id UUID REFERENCES programs(id) ON DELETE CASCADE,
    album_external_id UUID NOT NULL,  -- → MEDIA.albums.id
    PRIMARY KEY (program_id, album_external_id)
);

COMMENT ON TABLE program_media_library IS '[ACADEMIC] Albums de la médiathèque associés à un programme';

COMMIT;
