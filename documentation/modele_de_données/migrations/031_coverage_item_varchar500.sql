-- Migration : Augmenter la taille du champ item de call_coverage de 255 à 500 caractères
-- Date : 2026-03-30

ALTER TABLE call_coverage ALTER COLUMN item TYPE VARCHAR(500);
