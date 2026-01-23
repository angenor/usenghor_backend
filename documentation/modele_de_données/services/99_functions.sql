-- ============================================================================
-- ███████╗ ██████╗ ███╗   ██╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗███████╗
-- ██╔════╝██╔═══██╗████╗  ██║██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
-- █████╗  ██║   ██║██╔██╗ ██║██║        ██║   ██║██║   ██║██╔██╗ ██║███████╗
-- ██╔══╝  ██║   ██║██║╚██╗██║██║        ██║   ██║██║   ██║██║╚██╗██║╚════██║
-- ██║     ╚██████╔╝██║ ╚████║╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║███████║
-- ╚═╝      ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
-- FONCTIONS ET TRIGGERS
-- ============================================================================
-- Ce fichier contient les fonctions et triggers partagés.
-- À dupliquer dans chaque microservice si nécessaire.
-- ============================================================================

-- ============================================================================
-- FONCTION: Mise à jour automatique de updated_at
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================================================
-- APPLICATION DU TRIGGER updated_at SUR TOUTES LES TABLES
-- ============================================================================
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT table_name
        FROM information_schema.columns
        WHERE column_name = 'updated_at'
        AND table_schema = 'public'
    LOOP
        EXECUTE format('
            CREATE TRIGGER update_%I_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', t, t);
    END LOOP;
END;
$$ language 'plpgsql';

-- ============================================================================
-- SERVICE: APPLICATION - Génération des numéros de dossier
-- ============================================================================

-- Séquence pour les numéros de dossier
CREATE SEQUENCE IF NOT EXISTS seq_application_reference START 1;

-- Fonction pour générer un numéro de dossier de candidature
CREATE OR REPLACE FUNCTION generate_application_reference()
RETURNS TRIGGER AS $$
BEGIN
    NEW.reference_number = 'APP-' || TO_CHAR(NOW(), 'YYYY') || '-' || LPAD(NEXTVAL('seq_application_reference')::TEXT, 6, '0');
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger pour générer le numéro de dossier
CREATE TRIGGER trigger_generate_application_reference
BEFORE INSERT ON applications
FOR EACH ROW
WHEN (NEW.reference_number IS NULL)
EXECUTE FUNCTION generate_application_reference();

-- ============================================================================
-- FIN DU FICHIER 99_functions.sql
-- ============================================================================
