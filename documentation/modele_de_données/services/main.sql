-- ============================================================================
-- ██╗   ██╗███╗   ██╗██╗██╗   ██╗███████╗██████╗ ███████╗██╗████████╗███████╗
-- ██║   ██║████╗  ██║██║██║   ██║██╔════╝██╔══██╗██╔════╝██║╚══██╔══╝██╔════╝
-- ██║   ██║██╔██╗ ██║██║██║   ██║█████╗  ██████╔╝███████╗██║   ██║   █████╗
-- ██║   ██║██║╚██╗██║██║╚██╗ ██╔╝██╔══╝  ██╔══██╗╚════██║██║   ██║   ██╔══╝
-- ╚██████╔╝██║ ╚████║██║ ╚████╔╝ ███████╗██║  ██║███████║██║   ██║   ███████╗
--  ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝   ╚══════╝
-- ███████╗███████╗███╗   ██╗ ██████╗ ██╗  ██╗ ██████╗ ██████╗
-- ██╔════╝██╔════╝████╗  ██║██╔════╝ ██║  ██║██╔═══██╗██╔══██╗
-- ███████╗█████╗  ██╔██╗ ██║██║  ███╗███████║██║   ██║██████╔╝
-- ╚════██║██╔══╝  ██║╚██╗██║██║   ██║██╔══██║██║   ██║██╔══██╗
-- ███████║███████╗██║ ╚████║╚██████╔╝██║  ██║╚██████╔╝██║  ██║
-- ╚══════╝╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
-- SCHÉMA PRINCIPAL - IMPORT DE TOUS LES SERVICES
-- ============================================================================
-- PostgreSQL 15+ - Architecture préparée pour microservices
--
-- Usage: psql -d usenghor -f main.sql
--
-- Ce fichier importe tous les fichiers de services dans l'ordre correct
-- pour créer la base de données complète en mode monolithique.
--
-- Pour une migration vers microservices, chaque fichier de service peut
-- être utilisé indépendamment avec son propre fichier 00_extensions.sql.
-- ============================================================================

-- ============================================================================
-- ORDRE D'IMPORT POUR MICROSERVICES
-- ============================================================================
-- 1. CORE       - Données partagées (aucune dépendance)
-- 2. MEDIA      - Gestion médias (aucune dépendance)
-- 3. IDENTITY   - Authentification (dépend: CORE, MEDIA)
-- 4. PARTNER    - Partenaires (dépend: CORE, MEDIA)
-- 5. ORGANIZATION - Structure orga (dépend: IDENTITY, MEDIA)
-- 6. CAMPUS     - Campus (dépend: CORE, IDENTITY, MEDIA, PARTNER)
-- 7. ACADEMIC   - Formations (dépend: ORGANIZATION, IDENTITY, MEDIA, CAMPUS, PARTNER)
-- 8. PROJECT    - Projets (dépend: CORE, ORGANIZATION, IDENTITY, MEDIA, PARTNER)
-- 9. CONTENT    - Actualités/Événements (dépend: tous)
-- 10. APPLICATION - Candidatures (dépend: ACADEMIC, CAMPUS, IDENTITY, MEDIA, CORE)
-- 11. NEWSLETTER - Newsletter (dépend: IDENTITY)
-- 12. EDITORIAL - Configuration (dépend: IDENTITY)
-- ============================================================================

\echo '=============================================='
\echo 'UNIVERSITÉ SENGHOR - Installation du schéma'
\echo '=============================================='

-- Extensions et types partagés
\echo '[1/16] Extensions et types partagés...'
\i 00_extensions.sql

-- Services de base (sans dépendances)
\echo '[2/16] Service CORE (pays)...'
\i 01_core.sql

\echo '[3/16] Service MEDIA (médias)...'
\i 03_media.sql

-- Services d'identité et partenaires
\echo '[4/16] Service IDENTITY (utilisateurs)...'
\i 02_identity.sql

\echo '[5/16] Service PARTNER (partenaires)...'
\i 06_partner.sql

-- Structure organisationnelle
\echo '[6/16] Service ORGANIZATION (départements)...'
\i 04_organization.sql

\echo '[7/16] Service CAMPUS (campus)...'
\i 05_campus.sql

-- Services métiers
\echo '[8/16] Service ACADEMIC (formations)...'
\i 07_academic.sql

\echo '[9/16] Service PROJECT (projets)...'
\i 10_project.sql

\echo '[10/16] Service CONTENT (actualités/événements)...'
\i 09_content.sql

\echo '[11/16] Service APPLICATION (candidatures)...'
\i 08_application.sql

-- Services auxiliaires
\echo '[12/16] Service NEWSLETTER...'
\i 11_newsletter.sql

\echo '[13/16] Service EDITORIAL (configuration)...'
\i 12_editorial.sql

-- Fonctions, triggers et données
\echo '[14/16] Fonctions et triggers...'
\i 99_functions.sql

\echo '[15/16] Données initiales...'
\i 99_data_init.sql

\echo '[16/16] Vues...'
\i 99_views.sql

\echo '=============================================='
\echo 'Installation terminée avec succès!'
\echo '=============================================='

-- ============================================================================
-- GUIDE DE DÉCOUPAGE EN MICROSERVICES
-- ============================================================================
--
-- Chaque fichier SQL peut être extrait dans sa propre base de données.
-- Voici le mapping des tables par service:
--
-- ┌─────────────────┬────────────────────────────────────────────────────────────┐
-- │ SERVICE         │ TABLES                                                      │
-- ├─────────────────┼────────────────────────────────────────────────────────────┤
-- │ 01_core         │ countries                                                   │
-- ├─────────────────┼────────────────────────────────────────────────────────────┤
-- │ 02_identity     │ permissions, roles, role_permissions, users, user_roles,   │
-- │                 │ user_tokens, audit_logs                                     │
-- ├─────────────────┼────────────────────────────────────────────────────────────┤
-- │ 03_media        │ media, albums, album_media                                  │
-- ├─────────────────┼────────────────────────────────────────────────────────────┤
-- │ 04_organization │ sectors, services, service_objectives,                       │
-- │                 │ service_achievements, service_projects, service_media_library,│
-- │                 │ service_team                                                  │
-- ├─────────────────┼────────────────────────────────────────────────────────────┤
-- │ 05_campus       │ campuses, campus_partners, campus_team, campus_media_library│
-- ├─────────────────┼────────────────────────────────────────────────────────────┤
-- │ 06_partner      │ partners                                                    │
-- ├─────────────────┼────────────────────────────────────────────────────────────┤
-- │ 07_academic     │ programs, program_campuses, program_partners,               │
-- │                 │ program_semesters, program_courses,                         │
-- │                 │ program_career_opportunities, program_skills                │
-- ├─────────────────┼────────────────────────────────────────────────────────────┤
-- │ 08_application  │ application_calls, call_eligibility_criteria, call_coverage,│
-- │                 │ call_required_documents, call_schedule, applications,       │
-- │                 │ application_degrees, application_documents                  │
-- ├─────────────────┼────────────────────────────────────────────────────────────┤
-- │ 09_content      │ events, event_partners, event_registrations,                │
-- │                 │ event_media_library, news, news_media, tags, news_tags      │
-- ├─────────────────┼────────────────────────────────────────────────────────────┤
-- │ 10_project      │ project_categories, projects, project_countries,            │
-- │                 │ project_category_links, project_partners, project_calls,    │
-- │                 │ project_media_library                                       │
-- ├─────────────────┼────────────────────────────────────────────────────────────┤
-- │ 11_newsletter   │ newsletter_subscribers, newsletter_campaigns,               │
-- │                 │ newsletter_sends                                            │
-- ├─────────────────┼────────────────────────────────────────────────────────────┤
-- │ 12_editorial    │ editorial_categories, editorial_contents,                   │
-- │                 │ editorial_contents_history                                  │
-- └─────────────────┴────────────────────────────────────────────────────────────┘
--
-- RÈGLES DE COMMUNICATION INTER-SERVICES:
-- 1. Les colonnes *_external_id contiennent des UUID sans FK physique
-- 2. La validation de l'existence se fait via API entre services
-- 3. La cohérence est maintenue par des événements (event sourcing)
-- 4. Chaque service peut répliquer les données de référence (countries, etc.)
--
-- ============================================================================
