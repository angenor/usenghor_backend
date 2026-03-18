-- Migration 023: Ajout des colonnes biography_html et biography_md aux utilisateurs
-- Remplace le champ biography unique par le pattern double colonne HTML/Markdown (TOAST UI)

BEGIN;

-- Ajouter les nouvelles colonnes
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS biography_html TEXT,
    ADD COLUMN IF NOT EXISTS biography_md TEXT;

-- Migrer les données existantes : si biography contient du HTML, le copier dans biography_html
UPDATE users
SET biography_html = biography,
    biography_md = biography
WHERE biography IS NOT NULL AND biography != '';

COMMIT;
