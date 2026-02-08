-- Migration 005: Association actualités-appels et médiathèque des appels
-- Date: 2026-02-08
-- Description: Ajoute call_external_id à la table news pour permettre
--              l'association d'actualités à un appel à candidature.
--              Crée la table application_call_media_library pour la
--              médiathèque des appels (albums associés).

BEGIN;

-- 1) Ajouter call_external_id à la table news
-- Référence externe vers APPLICATION.application_calls.id (pas de FK, pattern inter-service)
ALTER TABLE news
    ADD COLUMN IF NOT EXISTS call_external_id UUID;

COMMENT ON COLUMN news.call_external_id IS 'Référence externe vers APPLICATION.application_calls.id';

CREATE INDEX IF NOT EXISTS idx_news_call ON news(call_external_id);

-- 2) Créer la table de jonction pour la médiathèque des appels
-- Pattern identique à event_media_library et project_media_library
CREATE TABLE IF NOT EXISTS application_call_media_library (
    call_id UUID REFERENCES application_calls(id) ON DELETE CASCADE,
    album_external_id UUID NOT NULL,  -- → MEDIA.albums.id
    PRIMARY KEY (call_id, album_external_id)
);

COMMENT ON TABLE application_call_media_library IS '[APPLICATION] Albums de la médiathèque associés à un appel à candidature';

COMMIT;
