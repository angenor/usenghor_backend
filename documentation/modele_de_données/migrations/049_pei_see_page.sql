-- =============================================================================
-- Migration 049 : Page « Entreprendre et étudier à Senghor » (Statut
--                 Étudiant-Entrepreneur) — textes du guide et FAQ SEE
-- =============================================================================
-- Contexte :
--   Feature 025-pei-see-status-page. La page publique
--   /entrepreneuriat/statut-etudiant-entrepreneur lit :
--   - 65 clés éditoriales entrepreneurship.see.* (Admin → Valeurs → Entrepreneuriat,
--     section « Statut Étudiant-Entrepreneur ») ;
--   - les catégories FAQ au code préfixé see- (Admin → FAQ), visibles aussi sur /faq ;
--   - l'appel désigné par entrepreneurship.see.call_slug (Candidatures → Appels).
--
-- Dépend de : 033_faq.sql, 045_entrepreneurship.sql (catégorie values, clés see.*)
--
-- Effets : +65 editorial_contents, +4 faq_categories, +8 faq_entries
--   (2 publiées, 6 brouillons à compléter). Aucune table, colonne ni type nouveau.
--   Traductions EN/AR des entrées publiées : Admin → Entrepreneuriat (PEI) →
--   « Traduire les champs manquants » ; les brouillons sont traduits à leur
--   enregistrement dans le backoffice FAQ.
--
-- Rejouable : ON CONFLICT DO NOTHING ; aucune valeur éditée n'est écrasée.
--
-- Rollback : 049_pei_see_page_rollback.sql
-- =============================================================================

BEGIN;

-- 1. Clés éditoriales -----------------------------------------------------------
INSERT INTO editorial_contents (key, value, value_type, category_id, description)
SELECT v.key, v.value, v.value_type::editorial_value_type,
       (SELECT id FROM editorial_categories WHERE code = 'values'), v.description
FROM (VALUES
    -- Hero
    ('entrepreneurship.see.hero.badge', 'Statut Étudiant-Entrepreneur', 'text', 'Badge du hero de la page SEE (l''année de l''appel est ajoutée automatiquement)'),
    ('entrepreneurship.see.hero.title', 'Entreprendre et étudier à Senghor', 'text', 'Titre du hero de la page SEE'),
    ('entrepreneurship.see.hero.subtitle', 'Concilier les exigences d''un Master de haut niveau avec le lancement d''une start-up, c''est possible grâce au Statut Étudiant-Entrepreneur (SEE).', 'text', 'Sous-titre du hero de la page SEE'),
    ('entrepreneurship.see.hero.image', '', 'text', 'Image du hero de la page SEE (identifiant média ; vide = motif)'),
    -- Intro
    ('entrepreneurship.see.intro.eyebrow', 'Devenir étudiant-entrepreneur', 'text', 'Surtitre de l''introduction'),
    ('entrepreneurship.see.intro.title', 'Vous avez une idée ? Nous avons le cadre pour la faire grandir.', 'text', 'Titre de l''introduction'),
    ('entrepreneurship.see.intro.lead', 'L''époque où l''université n''était qu''un lieu de transmission théorique est révolue. Le campus de l''Université Senghor s''affirme comme un véritable incubateur de talents où l''acquisition des savoirs s''articule avec l''audace de créer.', 'text', 'Paragraphe d''accroche de l''introduction'),
    ('entrepreneurship.see.intro.body', 'Le statut d''étudiant-entrepreneur est une passerelle : un accompagnement personnalisé et un aménagement de votre parcours pour faire éclore votre projet, tout en validant votre Master.', 'text', 'Paragraphe courant de l''introduction'),
    -- Encadré « Le SEE, c'est quoi ? »
    ('entrepreneurship.see.what.label', 'Le SEE, c''est quoi ?', 'text', 'Libellé de l''encadré de définition'),
    ('entrepreneurship.see.what.text', 'Un « accélérateur » intégré à votre cursus. Selon l''avancement de votre idée, vous intégrez l''un des deux parcours.', 'text', 'Texte de l''encadré de définition'),
    -- Cartes SEE 1 / SEE 2
    ('entrepreneurship.see.tracks.1.badge', 'SEE 1', 'text', 'Parcours 1 — badge'),
    ('entrepreneurship.see.tracks.1.title', 'Vous avez une idée ou un concept ?', 'text', 'Parcours 1 — titre'),
    ('entrepreneurship.see.tracks.1.text', 'Nous vous aidons à structurer votre projet (phase d''idéation) avec Mature Ton Idée.', 'text', 'Parcours 1 — texte'),
    ('entrepreneurship.see.tracks.2.badge', 'SEE 2', 'text', 'Parcours 2 — badge'),
    ('entrepreneurship.see.tracks.2.title', 'Votre plan d''affaires est prêt ?', 'text', 'Parcours 2 — titre'),
    ('entrepreneurship.see.tracks.2.text', 'Passez à la vitesse supérieure avec l''incubateur Senghor''Innov.', 'text', 'Parcours 2 — texte'),
    -- Pourquoi postuler ? (6 leviers)
    ('entrepreneurship.see.levers.eyebrow', 'Pourquoi postuler ?', 'text', 'Surtitre de la section des avantages'),
    ('entrepreneurship.see.levers.title', 'Six leviers pour votre projet', 'text', 'Titre de la section des avantages'),
    ('entrepreneurship.see.levers.1.icon', 'fa-solid fa-comments', 'text', 'Levier 1 — icône Font Awesome'),
    ('entrepreneurship.see.levers.1.title', 'Coaching et mentorat', 'text', 'Levier 1 — titre'),
    ('entrepreneurship.see.levers.1.text', 'Un accompagnement sur mesure par des experts et des alumni entrepreneurs.', 'text', 'Levier 1 — texte'),
    ('entrepreneurship.see.levers.2.icon', 'fa-solid fa-rocket', 'text', 'Levier 2 — icône Font Awesome'),
    ('entrepreneurship.see.levers.2.title', 'Programmes d''élite', 'text', 'Levier 2 — titre'),
    ('entrepreneurship.see.levers.2.text', 'Accès direct à Mature Ton Idée (MTI) et à l''incubateur Senghor''Innov.', 'text', 'Levier 2 — texte'),
    ('entrepreneurship.see.levers.3.icon', 'fa-solid fa-graduation-cap', 'text', 'Levier 3 — icône Font Awesome'),
    ('entrepreneurship.see.levers.3.title', 'Diplôme et projet liés', 'text', 'Levier 3 — titre'),
    ('entrepreneurship.see.levers.3.text', 'Votre projet devient votre sujet de stage et de mémoire de Master.', 'text', 'Levier 3 — texte'),
    ('entrepreneurship.see.levers.4.icon', 'fa-solid fa-clock', 'text', 'Levier 4 — icône Font Awesome'),
    ('entrepreneurship.see.levers.4.title', 'Flexibilité', 'text', 'Levier 4 — titre'),
    ('entrepreneurship.see.levers.4.text', '10 h de temps libéré sur vos cours et 4 crédits universitaires.', 'text', 'Levier 4 — texte'),
    ('entrepreneurship.see.levers.5.icon', 'fa-solid fa-coins', 'text', 'Levier 5 — icône Font Awesome'),
    ('entrepreneurship.see.levers.5.title', 'Financement', 'text', 'Levier 5 — titre'),
    ('entrepreneurship.see.levers.5.text', 'Accès potentiel au Fonds de Soutien à l''Entrepreneuriat, jusqu''à 5 000 €.', 'text', 'Levier 5 — texte'),
    ('entrepreneurship.see.levers.6.icon', 'fa-solid fa-building', 'text', 'Levier 6 — icône Font Awesome'),
    ('entrepreneurship.see.levers.6.title', 'Espace de travail', 'text', 'Levier 6 — titre'),
    ('entrepreneurship.see.levers.6.text', 'Un bureau, un espace de coworking et l''accès au fablab du campus.', 'text', 'Levier 6 — texte'),
    -- Suis-je le bon candidat ?
    ('entrepreneurship.see.apply.eyebrow', 'Candidater', 'text', 'Surtitre de la section candidature'),
    ('entrepreneurship.see.apply.title', 'Suis-je le bon candidat ?', 'text', 'Titre de la section candidature'),
    ('entrepreneurship.see.apply.intro', 'L''appel est ouvert à tous les étudiants de Master de l''Université Senghor, en projet individuel ou collectif.', 'text', 'Introduction de la section candidature'),
    ('entrepreneurship.see.conditions.title', 'Conditions', 'text', 'Titre de la carte des conditions'),
    ('entrepreneurship.see.conditions.1', 'Inscrit régulièrement pour l''année en cours', 'text', 'Condition 1 (affichée si l''appel n''a pas de critères d''éligibilité)'),
    ('entrepreneurship.see.conditions.2', 'Porteur d''une idée innovante ou d''un projet à impact pour le continent africain', 'text', 'Condition 2 (affichée si l''appel n''a pas de critères d''éligibilité)'),
    ('entrepreneurship.see.conditions.3', 'Prêt à s''engager activement dans l''aventure', 'text', 'Condition 3 (affichée si l''appel n''a pas de critères d''éligibilité)'),
    ('entrepreneurship.see.jury.title', 'Les critères du jury', 'text', 'Titre de la carte des critères du jury'),
    ('entrepreneurship.see.jury.1', 'L''innovation de votre projet', 'text', 'Critère du jury 1'),
    ('entrepreneurship.see.jury.2', 'L''impact de votre solution', 'text', 'Critère du jury 2'),
    ('entrepreneurship.see.jury.3', 'Votre motivation', 'text', 'Critère du jury 3'),
    ('entrepreneurship.see.jury.4', 'La cohérence avec vos études', 'text', 'Critère du jury 4'),
    ('entrepreneurship.see.documents.title', 'Mon dossier de candidature', 'text', 'Titre de la carte du dossier'),
    ('entrepreneurship.see.documents.1', 'Avis de non-objection du Directeur de département', 'text', 'Pièce 1 (affichée si l''appel n''a pas de pièces requises)'),
    ('entrepreneurship.see.documents.2', 'Lettre de motivation adressée au Recteur', 'text', 'Pièce 2 (affichée si l''appel n''a pas de pièces requises)'),
    ('entrepreneurship.see.documents.3', 'Fiche projet synthétique ou business plan', 'text', 'Pièce 3 (affichée si l''appel n''a pas de pièces requises)'),
    ('entrepreneurship.see.documents.4', 'Tout bonus : vidéo, prototype, photos', 'text', 'Pièce 4 (affichée si l''appel n''a pas de pièces requises)'),
    -- Agenda
    ('entrepreneurship.see.agenda.button', 'Postuler via le formulaire', 'text', 'Bouton du panneau agenda (appel ouvert)'),
    ('entrepreneurship.see.agenda.cc_note', 'Mettez votre Directeur de département en copie.', 'text', 'Rappel sous le bouton de candidature et dans l''appel à l''action final'),
    ('entrepreneurship.see.closed.title', 'Appel clos — prochaine session', 'text', 'Titre affiché lorsqu''aucun appel n''est ouvert'),
    ('entrepreneurship.see.closed.text', 'Les candidatures de cette session sont closes. Écrivez-nous pour être informé de l''ouverture de la prochaine session.', 'text', 'Texte affiché lorsqu''aucun appel n''est ouvert'),
    -- FAQ et PÉPITE France
    ('entrepreneurship.see.faq.eyebrow', 'FAQ', 'text', 'Surtitre de la FAQ (questions gérées dans Admin → FAQ, catégories see-*)'),
    ('entrepreneurship.see.faq.title', 'Vos questions sur le statut', 'text', 'Titre de la FAQ'),
    ('entrepreneurship.see.pepite.intro', 'Pour aller plus loin :', 'text', 'Texte précédant le lien PÉPITE France'),
    ('entrepreneurship.see.pepite.label', 'Réseau PÉPITE France', 'text', 'Libellé du lien PÉPITE France'),
    ('entrepreneurship.see.pepite.url', '', 'text', 'Adresse du lien PÉPITE France (vide = lien masqué)'),
    -- CTA final
    ('entrepreneurship.see.cta.title', 'Prêt à passer à l''action ?', 'text', 'Titre de l''appel à l''action final'),
    ('entrepreneurship.see.cta.text', 'Ne laissez pas votre projet dormir dans un tiroir. Besoin d''aide ? Passez nous voir au Pôle Entrepreneuriat (DDE).', 'text', 'Texte de l''appel à l''action final'),
    ('entrepreneurship.see.cta.button', 'Cliquez ici pour postuler', 'text', 'Bouton de l''appel à l''action final (appel ouvert)')
) AS v(key, value, value_type, description)
ON CONFLICT (key) DO NOTHING;

-- 2. Catégories FAQ SEE (visibles aussi sur /faq) -------------------------------
INSERT INTO faq_categories (code, label_fr, label_en, label_ar, display_order, is_active)
VALUES
    ('see-general',         'Généralités',                'General information',          'معلومات عامة',       10, TRUE),
    ('see-avantages',       'Avantages et aménagements',  'Benefits and accommodations',  'المزايا والتسهيلات',  11, TRUE),
    ('see-engagement',      'Engagement et risques',      'Commitment and risks',         'الالتزام والمخاطر',   12, TRUE),
    ('see-confidentialite', 'Confidentialité',            'Confidentiality',              'السرية',             13, TRUE)
ON CONFLICT (code) DO NOTHING;

-- 3. Questions (2 publiées, 6 brouillons à compléter) ----------------------------
INSERT INTO faq_entries (category_id, slug, question_fr, answer_fr_md, answer_fr_html,
                         is_published, published_at, display_order)
SELECT c.id, v.slug, v.question, v.answer, '<p>' || v.answer || '</p>',
       v.published, CASE WHEN v.published THEN NOW() END, v.display_order
FROM (VALUES
    ('see-general',         'see-statut-payant',             'Le statut est-il payant ?',
     'Non, l''obtention du statut est gratuite pour les étudiants en cours de cursus.', TRUE, 0),
    ('see-general',         'see-entreprise-deja-creee',     'Dois-je déjà avoir créé mon entreprise ?',
     'Réponse à rédiger par le Pôle Entrepreneuriat et Innovation.', FALSE, 1),
    ('see-general',         'see-postuler-en-groupe',        'Est-ce que je peux postuler en groupe ?',
     'Réponse à rédiger par le Pôle Entrepreneuriat et Innovation.', FALSE, 2),
    ('see-avantages',       'see-amenagements-academiques',  'Ai-je droit à des aménagements académiques grâce au SEE ?',
     'Oui : 10 h de temps libéré sur vos temps de cours et 4 crédits universitaires, sous condition de validation des évaluations du parcours.', TRUE, 0),
    ('see-avantages',       'see-stage-remplace-par-projet', 'Puis-je remplacer mon stage par mon projet ?',
     'Réponse à rédiger par le Pôle Entrepreneuriat et Innovation.', FALSE, 1),
    ('see-engagement',      'see-echec-etudes-ou-projet',    'Que se passe-t-il si j''échoue dans mes études ou mon projet ?',
     'Réponse à rédiger par le Pôle Entrepreneuriat et Innovation.', FALSE, 0),
    ('see-engagement',      'see-duree-validite-statut',     'Combien de temps le statut est-il valable ?',
     'Réponse à rédiger par le Pôle Entrepreneuriat et Innovation.', FALSE, 1),
    ('see-confidentialite', 'see-protection-idee',           'Mon idée sera-t-elle protégée ?',
     'Réponse à rédiger par le Pôle Entrepreneuriat et Innovation.', FALSE, 0)
) AS v(category_code, slug, question, answer, published, display_order)
JOIN faq_categories c ON c.code = v.category_code
ON CONFLICT (slug) DO NOTHING;

COMMIT;

\echo 'Migration 049_pei_see_page terminée'
