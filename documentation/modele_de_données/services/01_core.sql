-- ============================================================================
-- ███████╗ ██████╗ ██████╗ ███████╗
-- ██╔════╝██╔═══██╗██╔══██╗██╔════╝
-- █████╗  ██║   ██║██████╔╝█████╗
-- ██╔══╝  ██║   ██║██╔══██╗██╔══╝
-- ██║     ╚██████╔╝██║  ██║███████╗
-- ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝
-- SERVICE: CORE (Données partagées)
-- ============================================================================
-- Tables: countries
-- Dépendances: Aucune
-- Note: Ces données peuvent être dupliquées dans chaque microservice si nécessaire
-- ============================================================================

-- Pays (table de référence pouvant être répliquée)
CREATE TABLE countries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    iso_code CHAR(2) UNIQUE NOT NULL,
    iso_code3 CHAR(3) UNIQUE,
    name_fr VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    name_ar VARCHAR(100),
    phone_code VARCHAR(10),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_countries_iso_code ON countries(iso_code);
CREATE INDEX idx_countries_name_fr ON countries(name_fr);

COMMENT ON TABLE countries IS '[CORE] Pays - Table de référence partagée, peut être répliquée dans chaque microservice';

-- ============================================================================
-- FIN DU SERVICE CORE
-- ============================================================================
