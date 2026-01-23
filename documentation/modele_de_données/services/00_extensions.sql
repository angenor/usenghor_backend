-- ============================================================================
-- UNIVERSITÉ SENGHOR - EXTENSIONS ET TYPES PARTAGÉS
-- PostgreSQL 15+
-- ============================================================================
-- Ce fichier contient les extensions PostgreSQL et les types ENUM
-- utilisés par plusieurs services.
-- ============================================================================

-- ============================================================================
-- EXTENSIONS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TYPES ENUM PARTAGÉS
-- Note: En microservices, chaque service doit déclarer les types dont il a besoin
-- ============================================================================

-- Type partagé: Civilité
CREATE TYPE salutation AS ENUM ('Mr', 'Mrs', 'Dr', 'Pr');

-- Type partagé: Statut de publication
CREATE TYPE publication_status AS ENUM ('draft', 'published', 'archived');

-- Type partagé: Type de média
CREATE TYPE media_type AS ENUM ('image', 'video', 'document', 'audio');

-- ============================================================================
-- FIN DU FICHIER 00_extensions.sql
-- ============================================================================
