-- =============================================================================
-- Migration 043 : Permissions manquantes (médiathèque et autres modules)
-- =============================================================================
-- Contexte :
--   Le backend protège ses routes admin avec `PermissionChecker("<code>")`,
--   mais 22 codes de permission exigés par le code n'ont jamais été insérés
--   dans la table `permissions`. Ils n'apparaissent donc pas dans le
--   backoffice « Rôles » et ne peuvent être attribués à aucun rôle. Seul le
--   super_admin (qui contourne la vérification) pouvait utiliser ces routes.
--
--   Symptôme signalé : un utilisateur « Éditeur » peut modifier les textes de
--   ses rubriques mais ne peut pas insérer d'image, car l'upload passe par
--   POST /api/admin/media/upload qui exige `media.create` — permission
--   inexistante en base.
--
-- Codes concernés :
--   media.view / media.create / media.edit / media.delete
--   dashboard.view
--   editorial.create / editorial.delete
--   applications.create / applications.edit / applications.delete
--   newsletter.edit / newsletter.delete
--   organization.view / organization.edit
--   project.view / project.create / project.edit / project.delete
--   fundraisers.view / fundraisers.create / fundraisers.edit / fundraisers.delete
--
-- Attribution :
--   1. super_admin et admin reçoivent toutes les nouvelles permissions.
--   2. Tout rôle disposant déjà d'au moins une permission de rédaction de
--      contenu (`*.create` ou `*.edit`, hors catégories users/admin) reçoit
--      `media.view`, `media.create`, `media.edit` et `dashboard.view` :
--      quiconque peut rédiger un contenu doit pouvoir y insérer des images.
--
-- Rollback : 043_permissions_manquantes_rollback.sql
-- =============================================================================

BEGIN;

-- 1. Insertion des permissions manquantes
INSERT INTO permissions (code, name_fr, description, category) VALUES
    -- Médiathèque
    ('media.view',   'Voir la médiathèque',        'Consulter les médias et albums',                       'media'),
    ('media.create', 'Ajouter des médias',         'Téléverser des images et fichiers (éditeur inclus)',   'media'),
    ('media.edit',   'Modifier des médias',        'Modifier les métadonnées des médias et albums',        'media'),
    ('media.delete', 'Supprimer des médias',       'Supprimer des médias et albums',                       'media'),
    -- Tableau de bord
    ('dashboard.view', 'Voir le tableau de bord',  'Consulter les statistiques du tableau de bord admin',  'dashboard'),
    -- Éditorial
    ('editorial.create', 'Créer des contenus éditoriaux',     NULL, 'editorial'),
    ('editorial.delete', 'Supprimer des contenus éditoriaux', NULL, 'editorial'),
    -- Candidatures
    ('applications.create', 'Créer des appels et candidatures',     NULL, 'applications'),
    ('applications.edit',   'Modifier des appels et candidatures',  NULL, 'applications'),
    ('applications.delete', 'Supprimer des appels et candidatures', NULL, 'applications'),
    -- Newsletter
    ('newsletter.edit',   'Modifier des newsletters',  NULL, 'newsletter'),
    ('newsletter.delete', 'Supprimer des newsletters', NULL, 'newsletter'),
    -- Organisation
    ('organization.view', 'Voir l''organisation',     'Consulter les secteurs et services', 'organization'),
    ('organization.edit', 'Modifier l''organisation', 'Gérer les secteurs et services',     'organization'),
    -- Projets institutionnels
    ('project.view',   'Voir les projets',      NULL, 'project'),
    ('project.create', 'Créer des projets',     NULL, 'project'),
    ('project.edit',   'Modifier des projets',  NULL, 'project'),
    ('project.delete', 'Supprimer des projets', NULL, 'project'),
    -- Levées de fonds
    ('fundraisers.view',   'Voir les levées de fonds',      NULL, 'fundraisers'),
    ('fundraisers.create', 'Créer des levées de fonds',     NULL, 'fundraisers'),
    ('fundraisers.edit',   'Modifier des levées de fonds',  NULL, 'fundraisers'),
    ('fundraisers.delete', 'Supprimer des levées de fonds', NULL, 'fundraisers')
ON CONFLICT (code) DO NOTHING;

-- 2. super_admin et admin : toutes les permissions ci-dessus
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.category IN ('media', 'dashboard', 'editorial', 'applications',
                                     'newsletter', 'organization', 'project', 'fundraisers')
WHERE r.code IN ('super_admin', 'admin')
ON CONFLICT DO NOTHING;

-- 3. Rôles rédacteurs de contenu : accès médiathèque (lecture, ajout, édition)
--    et tableau de bord
INSERT INTO role_permissions (role_id, permission_id)
SELECT DISTINCT r.id, p.id
FROM roles r
JOIN role_permissions rp ON rp.role_id = r.id
JOIN permissions existing ON existing.id = rp.permission_id
JOIN permissions p ON p.code IN ('media.view', 'media.create', 'media.edit', 'dashboard.view')
WHERE r.code NOT IN ('super_admin', 'admin')
  AND (existing.code LIKE '%.create' OR existing.code LIKE '%.edit')
  AND existing.category NOT IN ('users', 'admin')
ON CONFLICT DO NOTHING;

COMMIT;

\echo 'Migration 043_permissions_manquantes terminée avec succès'
