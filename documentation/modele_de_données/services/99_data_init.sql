-- ============================================================================
-- ██████╗  █████╗ ████████╗ █████╗     ██╗███╗   ██╗██╗████████╗
-- ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗    ██║████╗  ██║██║╚══██╔══╝
-- ██║  ██║███████║   ██║   ███████║    ██║██╔██╗ ██║██║   ██║
-- ██║  ██║██╔══██║   ██║   ██╔══██║    ██║██║╚██╗██║██║   ██║
-- ██████╔╝██║  ██║   ██║   ██║  ██║    ██║██║ ╚████║██║   ██║
-- ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝    ╚═╝╚═╝  ╚═══╝╚═╝   ╚═╝
-- DONNÉES INITIALES
-- ============================================================================
-- Ce fichier contient les données de base nécessaires au fonctionnement.
-- ============================================================================

-- ============================================================================
-- [IDENTITY] Rôles par défaut
-- ============================================================================
INSERT INTO roles (code, name_fr, description, hierarchy_level) VALUES
('super_admin', 'Super Administrateur', 'Accès complet à toutes les fonctionnalités', 100),
('admin', 'Administrateur', 'Administration générale de la plateforme', 80),
('campus_admin', 'Administrateur Campus', 'Administration d''un campus spécifique', 60),
('editor', 'Éditeur', 'Création et modification de contenus', 40),
('moderator', 'Modérateur', 'Modération des contenus et candidatures', 30),
('user', 'Utilisateur', 'Utilisateur standard inscrit', 10);

-- ============================================================================
-- [EDITORIAL] Catégories de contenus éditoriaux
-- ============================================================================
INSERT INTO editorial_categories (code, name, description) VALUES
('statistics', 'Statistiques', 'Chiffres clés et statistiques'),
('values', 'Valeurs', 'Valeurs de l''université'),
('strategy', 'Stratégie', 'Éléments stratégiques'),
('contact', 'Contact', 'Informations de contact'),
('social_media', 'Réseaux sociaux', 'Liens vers les réseaux sociaux'),
('legal', 'Mentions légales', 'Contenus juridiques');

-- ============================================================================
-- [IDENTITY] Permissions de base
-- ============================================================================
INSERT INTO permissions (code, name_fr, category) VALUES
-- Gestion des utilisateurs
('users.view', 'Voir les utilisateurs', 'users'),
('users.create', 'Créer des utilisateurs', 'users'),
('users.edit', 'Modifier les utilisateurs', 'users'),
('users.delete', 'Supprimer des utilisateurs', 'users'),
('users.roles', 'Gérer les rôles des utilisateurs', 'users'),
-- Gestion des formations
('programs.view', 'Voir les formations', 'programs'),
('programs.create', 'Créer des formations', 'programs'),
('programs.edit', 'Modifier les formations', 'programs'),
('programs.delete', 'Supprimer des formations', 'programs'),
-- Gestion des candidatures
('applications.view', 'Voir les candidatures', 'applications'),
('applications.evaluate', 'Évaluer les candidatures', 'applications'),
('applications.export', 'Exporter les candidatures', 'applications'),
-- Gestion des événements
('events.view', 'Voir les événements', 'events'),
('events.create', 'Créer des événements', 'events'),
('events.edit', 'Modifier les événements', 'events'),
('events.delete', 'Supprimer des événements', 'events'),
-- Gestion des actualités
('news.view', 'Voir les actualités', 'news'),
('news.create', 'Créer des actualités', 'news'),
('news.edit', 'Modifier les actualités', 'news'),
('news.delete', 'Supprimer des actualités', 'news'),
-- Gestion des campus
('campuses.view', 'Voir les campus', 'campuses'),
('campuses.create', 'Créer des campus', 'campuses'),
('campuses.edit', 'Modifier les campus', 'campuses'),
('campuses.delete', 'Supprimer des campus', 'campuses'),
-- Gestion des partenaires
('partners.view', 'Voir les partenaires', 'partners'),
('partners.create', 'Créer des partenaires', 'partners'),
('partners.edit', 'Modifier les partenaires', 'partners'),
('partners.delete', 'Supprimer des partenaires', 'partners'),
-- Gestion des contenus éditoriaux
('editorial.view', 'Voir les contenus éditoriaux', 'editorial'),
('editorial.edit', 'Modifier les contenus éditoriaux', 'editorial'),
-- Gestion de la newsletter
('newsletter.view', 'Voir les newsletters', 'newsletter'),
('newsletter.create', 'Créer des newsletters', 'newsletter'),
('newsletter.send', 'Envoyer des newsletters', 'newsletter'),
-- Administration
('admin.settings', 'Gérer les paramètres', 'admin'),
('admin.audit', 'Voir les logs d''audit', 'admin');

-- ============================================================================
-- Attribution de toutes les permissions au super_admin
-- ============================================================================
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.code = 'super_admin';

-- ============================================================================
-- FIN DU FICHIER 99_data_init.sql
-- ============================================================================
