-- ============================================================================
-- Rollback de la migration 032 — Album médiathèque « Gouvernance »
-- ============================================================================
-- Suppression ciblée :
--  - retire les liaisons album_media correspondant aux URLs présentes dans
--    editorial_contents.governance.foundingTexts.documents
--  - supprime les médias devenus orphelins (plus liés à aucun album)
--  - supprime l'album « gouvernance » uniquement si aucun media_id ne lui
--    reste (préservation des ajouts manuels admin postérieurs à la migration)
-- La colonne thumbnail_url n'est PAS supprimée (enrichissement durable).
-- ============================================================================

BEGIN;

-- 1. Vérifier la présence de l'album cible : si absent on sort sans rien casser.
--    On lève une exception "douce" interceptée par EXCEPTION WHEN OTHERS plus bas.
DO $$
DECLARE
  v_album_exists BOOLEAN;
  v_source_exists BOOLEAN;
  v_removed INT := 0;
BEGIN
  SELECT EXISTS (SELECT 1 FROM albums WHERE slug = 'gouvernance')
    INTO v_album_exists;

  IF NOT v_album_exists THEN
    RAISE NOTICE 'Rollback 032 — aucun album « gouvernance » trouvé, sortie sans action.';
    RETURN;
  END IF;

  SELECT EXISTS (
    SELECT 1
    FROM editorial_contents
    WHERE key = 'governance.foundingTexts.documents'
      AND value_type = 'json'
      AND value IS NOT NULL
      AND value <> ''
  ) INTO v_source_exists;

  IF NOT v_source_exists THEN
    RAISE NOTICE 'Rollback 032 — clé éditoriale source absente : impossible de cibler les URLs à retirer. Sortie sans action.';
    RETURN;
  END IF;

  -- 2. Calcul des médias à retirer (URL provenant de la clé éditoriale source)
  CREATE TEMP TABLE _to_remove ON COMMIT DROP AS
  SELECT m.id AS media_id, m.url
  FROM media m
  JOIN album_media am ON am.media_id = m.id
  JOIN albums a       ON a.id = am.album_id
  WHERE a.slug = 'gouvernance'
    AND m.url IN (
      SELECT (elem->>'file_url')::TEXT
      FROM editorial_contents ec,
           jsonb_array_elements(ec.value::jsonb) AS elem
      WHERE ec.key = 'governance.foundingTexts.documents'
        AND ec.value_type = 'json'
    );

  -- 3. Suppression des liaisons concernées
  DELETE FROM album_media
  WHERE media_id IN (SELECT media_id FROM _to_remove)
    AND album_id = (SELECT id FROM albums WHERE slug = 'gouvernance');

  -- 4. Suppression des médias devenus orphelins
  DELETE FROM media m
  WHERE m.id IN (SELECT media_id FROM _to_remove)
    AND NOT EXISTS (
      SELECT 1 FROM album_media am WHERE am.media_id = m.id
    );

  -- 5. Suppression de l'album si plus aucun media_id ne lui est lié
  DELETE FROM albums
  WHERE slug = 'gouvernance'
    AND NOT EXISTS (
      SELECT 1
      FROM album_media am
      JOIN albums a2 ON a2.id = am.album_id
      WHERE a2.slug = 'gouvernance'
    );

  SELECT COUNT(*) INTO v_removed FROM _to_remove;
  RAISE NOTICE 'Rollback 032 — % médias retirés ; album supprimé si vide.', v_removed;
END $$;

COMMIT;
