-- ============================================================================
-- Migration 032 — Album médiathèque « Gouvernance » pour les textes fondateurs
-- ============================================================================
-- Spec: specs/018-governance-media-album/
-- Idempotente : peut être exécutée plusieurs fois sans créer de doublons.
-- Source de vérité : editorial_contents.key = 'governance.foundingTexts.documents'.
-- Identifiant d'idempotence pour les médias : media.url.
-- ============================================================================

BEGIN;

-- 1. Évolution de schéma (idempotente)
ALTER TABLE media ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500);

-- 2. Création / upsert de l'album « Gouvernance »
WITH upsert_album AS (
  INSERT INTO albums (slug, title, description, status)
  VALUES (
    'gouvernance',
    'Gouvernance',
    'Textes fondateurs de l''Université Senghor (chartes, conventions, statuts).',
    'published'
  )
  ON CONFLICT (slug) DO UPDATE
    SET title = EXCLUDED.title,
        description = EXCLUDED.description,
        status = EXCLUDED.status,
        updated_at = NOW()
  RETURNING id
)
SELECT id INTO TEMP TABLE _governance_album_id FROM upsert_album;

-- 3. Extraction des documents depuis editorial_contents
--    Déduplication par `url` : si la source contient plusieurs entrées avec la
--    même URL (artefact d'édition), on garde celle avec le plus petit
--    display_order (sort_order si défini, sinon position dans le tableau).
--    Indispensable pour éviter `ON CONFLICT DO UPDATE command cannot affect
--    row a second time` sur album_media (album_id, media_id).
CREATE TEMP TABLE _source_docs AS
WITH expanded AS (
  SELECT
    (elem->>'title_fr')::TEXT                                            AS name,
    NULLIF(elem->>'description_fr','')                                   AS description,
    (elem->>'file_url')::TEXT                                            AS url,
    NULLIF(elem->>'file_size','')::BIGINT                                AS size_bytes,
    NULLIF(elem->>'cover_image','')                                      AS thumbnail_url,
    NULLIF(elem->>'year','')                                             AS credits,
    COALESCE(
      NULLIF(elem->>'sort_order','')::INT,
      (row_number() OVER ())::INT - 1
    )                                                                    AS display_order
  FROM editorial_contents ec,
       jsonb_array_elements(ec.value::jsonb) AS elem
  WHERE ec.key = 'governance.foundingTexts.documents'
    AND ec.value_type = 'json'
    AND elem->>'file_url' IS NOT NULL
    AND elem->>'file_url' <> ''
)
SELECT DISTINCT ON (url)
  name, description, url, size_bytes, thumbnail_url, credits, display_order
FROM expanded
ORDER BY url, display_order ASC NULLS LAST;

-- 4. Insertion des médias absents (idempotence par url)
WITH inserted AS (
  INSERT INTO media (
    name, description, type, url, mime_type,
    size_bytes, thumbnail_url, credits, is_external_url
  )
  SELECT
    s.name,
    s.description,
    'document',
    s.url,
    'application/pdf',
    s.size_bytes,
    s.thumbnail_url,
    s.credits,
    FALSE
  FROM _source_docs s
  WHERE NOT EXISTS (SELECT 1 FROM media m WHERE m.url = s.url)
  RETURNING 1
)
SELECT COUNT(*) AS inserted_count INTO TEMP TABLE _inserted_count FROM inserted;

-- 5. Mise à jour des médias déjà existants (même url)
WITH updated AS (
  UPDATE media m
  SET name          = s.name,
      description   = s.description,
      size_bytes    = COALESCE(s.size_bytes, m.size_bytes),
      thumbnail_url = COALESCE(s.thumbnail_url, m.thumbnail_url),
      credits       = COALESCE(s.credits, m.credits),
      updated_at    = NOW()
  FROM _source_docs s
  WHERE m.url = s.url
  RETURNING 1
)
SELECT COUNT(*) AS updated_count INTO TEMP TABLE _updated_count FROM updated;

-- 6. Liaison album ⇄ média (avec mise à jour du display_order si déjà liée)
INSERT INTO album_media (album_id, media_id, display_order)
SELECT
  (SELECT id FROM _governance_album_id),
  m.id,
  s.display_order
FROM _source_docs s
JOIN media m ON m.url = s.url
ON CONFLICT (album_id, media_id) DO UPDATE
  SET display_order = EXCLUDED.display_order;

-- 7. Notices d'observabilité
DO $$
DECLARE
  v_inserted INT;
  v_updated  INT;
  v_linked   INT;
BEGIN
  SELECT inserted_count INTO v_inserted FROM _inserted_count;
  SELECT updated_count INTO v_updated  FROM _updated_count;
  SELECT COUNT(*) INTO v_linked
  FROM album_media am
  JOIN albums a ON a.id = am.album_id
  WHERE a.slug = 'gouvernance';

  RAISE NOTICE 'Migration 032 — médias insérés: %, médias mis à jour: %, total liés à l''album gouvernance: %',
    v_inserted, v_updated, v_linked;
END $$;

-- 8. Cleanup
DROP TABLE IF EXISTS _source_docs;
DROP TABLE IF EXISTS _governance_album_id;
DROP TABLE IF EXISTS _inserted_count;
DROP TABLE IF EXISTS _updated_count;

COMMIT;
