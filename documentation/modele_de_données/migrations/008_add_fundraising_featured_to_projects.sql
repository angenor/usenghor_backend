-- Migration: Ajout des champs de levée de fonds à la table projects
-- Description: Permet de marquer des projets comme "à la une" pour la section
--              de levée de fonds sur la page stratégie

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'is_fundraising_featured'
    ) THEN
        ALTER TABLE projects
        ADD COLUMN is_fundraising_featured BOOLEAN DEFAULT FALSE;

        COMMENT ON COLUMN projects.is_fundraising_featured
            IS 'Projet mis en avant dans la section levée de fonds';

        CREATE INDEX idx_projects_fundraising_featured
            ON projects(is_fundraising_featured)
            WHERE is_fundraising_featured = TRUE;

        RAISE NOTICE 'Colonne is_fundraising_featured ajoutée à la table projects';
    ELSE
        RAISE NOTICE 'La colonne is_fundraising_featured existe déjà';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'fundraising_display_order'
    ) THEN
        ALTER TABLE projects
        ADD COLUMN fundraising_display_order INT DEFAULT 0;

        COMMENT ON COLUMN projects.fundraising_display_order
            IS 'Ordre d''affichage dans la section levée de fonds';

        RAISE NOTICE 'Colonne fundraising_display_order ajoutée à la table projects';
    ELSE
        RAISE NOTICE 'La colonne fundraising_display_order existe déjà';
    END IF;
END $$;
