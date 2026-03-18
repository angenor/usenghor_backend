-- Migration 024: Ajout des colonnes description_html et description_md aux campus
-- Pattern double colonne HTML/Markdown (TOAST UI) pour les campus

BEGIN;

ALTER TABLE campuses
    ADD COLUMN IF NOT EXISTS description_html TEXT,
    ADD COLUMN IF NOT EXISTS description_md TEXT;

-- Migrer les données existantes : copier description dans les deux colonnes
UPDATE campuses
SET description_html = description,
    description_md = description
WHERE description IS NOT NULL AND description != '';

COMMIT;
