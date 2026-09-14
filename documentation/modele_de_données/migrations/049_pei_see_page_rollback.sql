-- Rollback 049_pei_see_page : retire les entrées seedées, les catégories see-*
-- seedées restées vides, et les clés entrepreneurship.see.* ajoutées.
BEGIN;

DELETE FROM faq_entries WHERE slug IN (
    'see-statut-payant', 'see-entreprise-deja-creee', 'see-postuler-en-groupe',
    'see-amenagements-academiques', 'see-stage-remplace-par-projet',
    'see-echec-etudes-ou-projet', 'see-duree-validite-statut', 'see-protection-idee'
);

-- Une catégorie contenant une question créée par l'équipe est conservée (FK RESTRICT).
DELETE FROM faq_categories c
WHERE c.code IN ('see-general', 'see-avantages', 'see-engagement', 'see-confidentialite')
  AND NOT EXISTS (SELECT 1 FROM faq_entries e WHERE e.category_id = c.id);

DELETE FROM editorial_contents
WHERE key LIKE 'entrepreneurship.see.%'
  AND key NOT IN (
      'entrepreneurship.see.call_slug', 'entrepreneurship.see.mentor.title',
      'entrepreneurship.see.mentor.description', 'entrepreneurship.see.mentor.button'
  );

COMMIT;

\echo 'Rollback 049_pei_see_page terminé (catégories see-* non vides conservées)'
