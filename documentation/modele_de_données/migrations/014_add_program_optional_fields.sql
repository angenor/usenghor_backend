-- Migration 014: Ajout des champs facultatifs aux programmes
-- Objectifs, Public cible, Format, Modalités d'évaluation

ALTER TABLE programs ADD COLUMN IF NOT EXISTS objectives TEXT;
ALTER TABLE programs ADD COLUMN IF NOT EXISTS target_audience TEXT;
ALTER TABLE programs ADD COLUMN IF NOT EXISTS format TEXT;
ALTER TABLE programs ADD COLUMN IF NOT EXISTS evaluation_methods TEXT;
