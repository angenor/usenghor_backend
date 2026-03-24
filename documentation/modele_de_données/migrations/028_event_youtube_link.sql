-- Migration 028: Ajout du champ youtube_link aux événements
-- Permet d'associer un lien YouTube (replay) à un événement

ALTER TABLE events
ADD COLUMN IF NOT EXISTS youtube_link VARCHAR(500) DEFAULT NULL;

COMMENT ON COLUMN events.youtube_link IS 'Lien YouTube de replay de l''événement';
