-- Migration 012: Seed des sous-items de navigation secondaire
-- Les sous-items sont stockes en JSON dans editorial_contents
-- Ils alimentent dynamiquement le menu "Plus" de la navbar

-- Recuperer l'ID de la categorie 'values' (utilisee pour les contenus globaux)
DO $$
DECLARE
  v_category_id UUID;
BEGIN
  SELECT id INTO v_category_id FROM editorial_categories WHERE code = 'values';

  IF v_category_id IS NULL THEN
    RAISE EXCEPTION 'Categorie "values" introuvable. Verifiez que les donnees initiales ont ete chargees.';
  END IF;

  -- === Sous-menu "Nous connaitre" ===
  INSERT INTO editorial_contents (id, key, value, value_type, category_id, description, admin_editable)
  VALUES (
    gen_random_uuid(),
    'navbar.secondary.about.children',
    '[
      {"id":"mission","label":"Notre mission","route":"/a-propos#mission","icon":"fa-solid fa-bullseye","sort_order":1},
      {"id":"history","label":"Notre histoire","route":"/a-propos/histoire","icon":"fa-solid fa-landmark","sort_order":2},
      {"id":"governance","label":"Gouvernance","route":"/a-propos/gouvernance","icon":"fa-solid fa-sitemap","sort_order":3}
    ]',
    'json',
    v_category_id,
    'Sous-items du menu secondaire "Nous connaitre"',
    true
  )
  ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    value_type = EXCLUDED.value_type,
    updated_at = NOW();

  -- === Sous-menu "Nos projets" ===
  INSERT INTO editorial_contents (id, key, value, value_type, category_id, description, admin_editable)
  VALUES (
    gen_random_uuid(),
    'navbar.secondary.projects.children',
    '[
      {"id":"transformAction","label":"Transform''Action Africa","route":"/projets/transformaction","icon":"fa-solid fa-rocket","badge":"flagship","sort_order":1},
      {"id":"kreAfrika","label":"KreAfrika","route":"/projets/kreafrika","icon":"fa-solid fa-lightbulb","sort_order":2},
      {"id":"fundraising","label":"Levee de fonds","route":"/projets/levee-de-fonds","icon":"fa-solid fa-hand-holding-dollar","sort_order":3}
    ]',
    'json',
    v_category_id,
    'Sous-items du menu secondaire "Nos projets"',
    true
  )
  ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    value_type = EXCLUDED.value_type,
    updated_at = NOW();

  -- === Sous-menu "Nos alumni" ===
  INSERT INTO editorial_contents (id, key, value, value_type, category_id, description, admin_editable)
  VALUES (
    gen_random_uuid(),
    'navbar.secondary.alumni.children',
    '[
      {"id":"reseau","label":"Reseau alumni","route":"/alumni#reseau","icon":"fa-solid fa-users","badge":"4200+","sort_order":1},
      {"id":"temoignages","label":"Temoignages","route":"/alumni#temoignages","icon":"fa-solid fa-quote-left","sort_order":2},
      {"id":"annuaire","label":"Annuaire","route":"/alumni#annuaire","icon":"fa-solid fa-address-book","sort_order":3}
    ]',
    'json',
    v_category_id,
    'Sous-items du menu secondaire "Nos alumni"',
    true
  )
  ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    value_type = EXCLUDED.value_type,
    updated_at = NOW();

  -- === Sous-menu "Notre site" ===
  INSERT INTO editorial_contents (id, key, value, value_type, category_id, description, admin_editable)
  VALUES (
    gen_random_uuid(),
    'navbar.secondary.site.children',
    '[
      {"id":"hebergement","label":"Hebergement","route":"/site#hebergement","icon":"fa-solid fa-house","sort_order":1},
      {"id":"bibliotheque","label":"Bibliotheque","route":"/site#bibliotheque","icon":"fa-solid fa-book","sort_order":2},
      {"id":"salles-conference","label":"Salles de conferences","route":"/site#salles-conference","icon":"fa-solid fa-microphone","sort_order":3},
      {"id":"espaces-academiques","label":"Espaces academiques","route":"/site#espaces-academiques","icon":"fa-solid fa-chalkboard","sort_order":4},
      {"id":"installations-sportives","label":"Installations sportives","route":"/site#installations-sportives","icon":"fa-solid fa-futbol","sort_order":5},
      {"id":"hotel","label":"Hotel","route":"/site#hotel","icon":"fa-solid fa-hotel","sort_order":6}
    ]',
    'json',
    v_category_id,
    'Sous-items du menu secondaire "Notre site"',
    true
  )
  ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    value_type = EXCLUDED.value_type,
    updated_at = NOW();

  RAISE NOTICE 'Seed des sous-items de navigation effectue avec succes (4 menus).';
END $$;
