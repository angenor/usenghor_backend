-- ============================================================================
-- Migration 011 : Configuration de la carte du monde
-- Date : 2026-02-18
-- Description : Ajouter la configuration de la carte (viewBox, pays exclus)
--               dans les contenus éditoriaux existants
-- ============================================================================

-- Catégorie « Configuration carte »
INSERT INTO editorial_categories (id, code, name, description)
VALUES (
  gen_random_uuid(),
  'map_config',
  'Configuration de la carte',
  'Paramètres d''affichage de la carte du monde (viewBox, pays exclus)'
)
ON CONFLICT (code) DO NOTHING;

-- ViewBox de la carte
INSERT INTO editorial_contents (id, key, value, value_type, category_id, description, admin_editable)
VALUES (
  gen_random_uuid(),
  'map_viewbox',
  '{"x": 420, "y": 55, "width": 590, "height": 540}',
  'json',
  (SELECT id FROM editorial_categories WHERE code = 'map_config'),
  'ViewBox SVG de la carte du monde (zone visible)',
  true
)
ON CONFLICT (key) DO NOTHING;

-- Pays exclus de la carte
INSERT INTO editorial_contents (id, key, value, value_type, category_id, description, admin_editable)
VALUES (
  gen_random_uuid(),
  'map_excluded_countries',
  '["gl","us","ca","mx","gt","bz","hn","sv","ni","cr","pa","cu","jm","ht","do","pr","bs","tt","bb","gd","vc","lc","dm","ag","kn","br","ar","co","pe","ve","cl","ec","bo","py","uy","gy","sr","gf"]',
  'json',
  (SELECT id FROM editorial_categories WHERE code = 'map_config'),
  'Codes ISO des pays exclus de l''affichage sur la carte',
  true
)
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- FIN DE LA MIGRATION
-- ============================================================================
