-- Migration 020: Convertir les colonnes credits de INT à NUMERIC(5,1)
-- Permet les crédits ECTS décimaux (ex: 2.5)

ALTER TABLE programs ALTER COLUMN credits TYPE NUMERIC(5, 1);
ALTER TABLE program_semesters ALTER COLUMN credits TYPE NUMERIC(5, 1);
ALTER TABLE program_courses ALTER COLUMN credits TYPE NUMERIC(5, 1);
