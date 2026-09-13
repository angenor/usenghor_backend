-- =============================================================================
-- Migration 045 : Socle du Pôle Entrepreneuriat et Innovation (PEI)
-- =============================================================================
-- Contexte :
--   Feature 021-pei-entrepreneurship-core. Le pôle PEI (service DDE, secteur
--   Rectorat) dispose de données propres (dispositifs du parcours, cohortes,
--   boîte à outils) gérées dans le backoffice « Entrepreneuriat (PEI) » et
--   exposées en lecture publique pour le futur mini-site « Entreprendre à
--   Senghor ». Schéma de référence : services/16_entrepreneurship.sql.
--
-- Effets :
--   1. Types ENUM pei_program_phase, pei_cohort_type, pei_resource_type
--   2. Tables pei_programs, pei_cohorts, pei_resources (+ index, triggers updated_at)
--   3. Permissions entrepreneurship.view|create|edit|delete attribuées à
--      super_admin, admin et editor
--   4. Données initiales FR : 5 dispositifs, 3 cohortes FSE
--   5. 43 clés éditoriales de la page « Entrepreneuriat » (catégorie values),
--      dont entrepreneurship.dde_service_id résolue depuis la table services
--
-- Rejouable : types gardés, IF NOT EXISTS, ON CONFLICT DO NOTHING (les valeurs
-- modifiées par les éditeurs ne sont jamais écrasées).
-- Traductions EN/AR : action « Traduire les champs manquants » du tableau de
-- bord du pôle, à lancer une fois après la migration.
--
-- Rollback : 045_entrepreneurship_rollback.sql
-- =============================================================================

BEGIN;

-- 1. Types ENUM
DO $$ BEGIN
    CREATE TYPE pei_program_phase AS ENUM
        ('awareness', 'status', 'pre_incubation', 'incubation', 'funding', 'ecosystem');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE pei_cohort_type AS ENUM ('fse', 'see');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE pei_resource_type AS ENUM ('document', 'link', 'video');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 2. Tables et index
-- Dispositifs du parcours entrepreneurial
CREATE TABLE IF NOT EXISTS pei_programs (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code                    VARCHAR(60)  UNIQUE NOT NULL,
    sigle                   VARCHAR(30),
    title                   VARCHAR(200) NOT NULL,
    title_en                VARCHAR(200),
    title_ar                VARCHAR(200),
    phase                   pei_program_phase NOT NULL,
    tagline                 TEXT,
    tagline_en              TEXT,
    tagline_ar              TEXT,
    content_html            TEXT,
    content_md              TEXT,
    content_en_html         TEXT,
    content_en_md           TEXT,
    content_ar_html         TEXT,
    content_ar_md           TEXT,
    highlight               VARCHAR(120),
    highlight_en            VARCHAR(120),
    highlight_ar            VARCHAR(120),
    color                   VARCHAR(20)  NOT NULL DEFAULT 'blue',
    cover_image_external_id UUID,                      -- → MEDIA.media.id (sans FK)
    display_order           INTEGER      NOT NULL DEFAULT 0,
    active                  BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by              UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by              UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_pei_programs_code  CHECK (code ~ '^[a-z0-9][a-z0-9-]*$'),
    CONSTRAINT chk_pei_programs_title CHECK (LENGTH(title) >= 3),
    CONSTRAINT chk_pei_programs_color CHECK (color IN ('blue', 'blue_dark', 'red', 'amber', 'teal'))
);

CREATE INDEX IF NOT EXISTS idx_pei_programs_active_order ON pei_programs (active, display_order);

-- Cohortes (FSE / SEE)
CREATE TABLE IF NOT EXISTS pei_cohorts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code            VARCHAR(60)  UNIQUE NOT NULL,
    label           VARCHAR(200) NOT NULL,
    label_en        VARCHAR(200),
    label_ar        VARCHAR(200),
    year            INTEGER      NOT NULL,
    type            pei_cohort_type NOT NULL,
    focus           TEXT,
    focus_en        TEXT,
    focus_ar        TEXT,
    summary_html    TEXT,
    summary_md      TEXT,
    summary_en_html TEXT,
    summary_en_md   TEXT,
    summary_ar_html TEXT,
    summary_ar_md   TEXT,
    display_order   INTEGER      NOT NULL DEFAULT 0,
    active          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_pei_cohorts_code CHECK (code ~ '^[a-z0-9][a-z0-9-]*$'),
    CONSTRAINT chk_pei_cohorts_year CHECK (year BETWEEN 2000 AND 2100)
);

CREATE INDEX IF NOT EXISTS idx_pei_cohorts_active_order ON pei_cohorts (active, display_order);
CREATE INDEX IF NOT EXISTS idx_pei_cohorts_type_year   ON pei_cohorts (type, year DESC);

-- Boîte à outils (documents, liens, vidéos)
CREATE TABLE IF NOT EXISTS pei_resources (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title             VARCHAR(200) NOT NULL,
    title_en          VARCHAR(200),
    title_ar          VARCHAR(200),
    description       TEXT,
    description_en    TEXT,
    description_ar    TEXT,
    type              pei_resource_type NOT NULL,
    media_external_id UUID,                          -- → MEDIA.media.id (sans FK), type = document
    url               VARCHAR(500),                  -- type = link | video
    category          VARCHAR(120),
    category_en       VARCHAR(120),
    category_ar       VARCHAR(120),
    display_order     INTEGER      NOT NULL DEFAULT 0,
    is_published      BOOLEAN      NOT NULL DEFAULT FALSE,
    published_at      TIMESTAMPTZ,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by        UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by        UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_pei_resources_source CHECK (
        (type = 'document' AND media_external_id IS NOT NULL)
        OR (type IN ('link', 'video') AND url IS NOT NULL AND LENGTH(url) > 0)
    )
);

CREATE INDEX IF NOT EXISTS idx_pei_resources_published_order ON pei_resources (is_published, display_order);

COMMENT ON TABLE pei_programs  IS '[PEI] Dispositifs du parcours entrepreneurial (OSER, SEE, MTI, Senghor''Innov, FSE).';
COMMENT ON TABLE pei_cohorts   IS '[PEI] Cohortes de lauréats FSE / étudiants-entrepreneurs SEE (lauréats en feature 022).';
COMMENT ON TABLE pei_resources IS '[PEI] Boîte à outils : documents de la médiathèque, liens, vidéos.';
COMMENT ON COLUMN pei_programs.color IS 'Couleur nommée de la charte : blue | blue_dark | red | amber | teal.';

-- 3. Triggers updated_at
DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['pei_programs', 'pei_cohorts', 'pei_resources'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_' || t || '_updated_at') THEN
            EXECUTE format(
                'CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON %I
                 FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', t, t);
        END IF;
    END LOOP;
END $$;

-- 4. Permissions
INSERT INTO permissions (code, name_fr, description, category) VALUES
    ('entrepreneurship.view',   'Voir le pôle Entrepreneuriat',                   'Consulter les dispositifs, cohortes et ressources du PEI', 'entrepreneurship'),
    ('entrepreneurship.create', 'Créer des contenus du pôle Entrepreneuriat',     NULL, 'entrepreneurship'),
    ('entrepreneurship.edit',   'Modifier des contenus du pôle Entrepreneuriat',  'Modifier, réordonner, activer, publier et traduire',     'entrepreneurship'),
    ('entrepreneurship.delete', 'Supprimer des contenus du pôle Entrepreneuriat', NULL, 'entrepreneurship')
ON CONFLICT (code) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.code IN ('super_admin', 'admin', 'editor')
  AND p.code IN ('entrepreneurship.view', 'entrepreneurship.create', 'entrepreneurship.edit', 'entrepreneurship.delete')
ON CONFLICT DO NOTHING;

-- 5. Dispositifs du parcours (FR seulement)
INSERT INTO pei_programs (code, sigle, title, phase, tagline, content_md, content_html, highlight, color, display_order) VALUES
    ('oser', 'OSER', 'Parcours OSER', 'awareness', 'Éveiller l''esprit créatif et susciter le déclic entrepreneurial dès l''arrivée à l''Université.',
     'Éveiller l''esprit créatif et susciter le déclic entrepreneurial dès l''arrivée : module SCIADO, campagne « Réalise un exploit », Semaine Senghorienne de l''Entrepreneuriat (2SE).',
     '<p>Éveiller l''esprit créatif et susciter le déclic entrepreneurial dès l''arrivée : module SCIADO, campagne « Réalise un exploit », Semaine Senghorienne de l''Entrepreneuriat (2SE).</p>',
     NULL, 'teal', 0),
    ('see', 'SEE', 'Statut Étudiant-Entrepreneur', 'status', 'Une reconnaissance officielle et un cadre privilégié : aménagements académiques, projet valorisé comme stage ou mémoire.',
     'Le statut d''étudiant-entrepreneur est une passerelle : un accompagnement personnalisé et un aménagement de votre parcours pour faire éclore votre projet, tout en validant votre Master.

Selon l''avancement de votre idée, vous intégrez l''un des deux parcours : SEE 1 pour structurer une idée ou un concept avec Mature Ton Idée, SEE 2 pour passer à la vitesse supérieure avec l''incubateur Senghor''Innov lorsque votre plan d''affaires est prêt.

Coaching et mentorat, projet lié au stage et au mémoire de Master, 10 h de temps libéré sur vos cours et 4 crédits universitaires, accès potentiel au Fonds de Soutien à l''Entrepreneuriat et à un espace de travail sur le campus.',
     '<p>Le statut d''étudiant-entrepreneur est une passerelle : un accompagnement personnalisé et un aménagement de votre parcours pour faire éclore votre projet, tout en validant votre Master.</p><p>Selon l''avancement de votre idée, vous intégrez l''un des deux parcours : SEE 1 pour structurer une idée ou un concept avec Mature Ton Idée, SEE 2 pour passer à la vitesse supérieure avec l''incubateur Senghor''Innov lorsque votre plan d''affaires est prêt.</p><p>Coaching et mentorat, projet lié au stage et au mémoire de Master, 10 h de temps libéré sur vos cours et 4 crédits universitaires, accès potentiel au Fonds de Soutien à l''Entrepreneuriat et à un espace de travail sur le campus.</p>',
     '4 crédits · 10 h libérées', 'blue_dark', 1),
    ('mti', 'MTI', 'Mature Ton Idée', 'pre_incubation', '3 mois pour passer de l''idée au projet.',
     '3 mois pour passer de l''idée au projet : design thinking, modèle économique, pitch. 4 crédits universitaires validés.',
     '<p>3 mois pour passer de l''idée au projet : design thinking, modèle économique, pitch. 4 crédits universitaires validés.</p>',
     '4 crédits', 'blue', 2),
    ('senghor-innov', NULL, 'Senghor''Innov', 'incubation', 'Accélérer la création de start-up.',
     'Accélérer la création de start-up : MVP, sécurisation juridique, mentorat par des alumni expérimentés.',
     '<p>Accélérer la création de start-up : MVP, sécurisation juridique, mentorat par des alumni expérimentés.</p>',
     NULL, 'red', 3),
    ('fse', 'FSE', 'Fonds de Soutien à l''Entrepreneuriat', 'funding', 'Une subvention d''amorçage pour lancer les premières opérations concrètes.',
     'Une subvention d''amorçage jusqu''à 5 000 € par projet pour lancer les premières opérations concrètes.',
     '<p>Une subvention d''amorçage jusqu''à 5 000 € par projet pour lancer les premières opérations concrètes.</p>',
     '5 000 €', 'amber', 4)
ON CONFLICT (code) DO NOTHING;

-- 6. Cohortes FSE (ordre : la plus récente en premier)
INSERT INTO pei_cohorts (code, label, year, type, focus, display_order) VALUES
    ('fse-3', 'FSE 3 · Promotion 2025', 2025, 'fse', 'Innovation et passage à l''échelle — projets incubés via Senghor''Innov', 0),
    ('fse-2', 'FSE 2 · Consolidation', 2024, 'fse', 'Dimension intrapreneuriale — projets à fort impact social et technologique', 1),
    ('fse-1', 'FSE 1 · Lancement 2023', 2023, 'fse', 'Preuve de concept — projets en amorçage', 2)
ON CONFLICT (code) DO NOTHING;

-- 7. Clés éditoriales de la page « Entrepreneuriat »
INSERT INTO editorial_contents (key, value, value_type, category_id, description)
SELECT v.key, v.value, v.value_type::editorial_value_type,
       (SELECT id FROM editorial_categories WHERE code = 'values'), v.description
FROM (VALUES
    ('entrepreneurship.hero.badge', 'Pôle Entrepreneuriat et Innovation', 'text', 'Petit libellé au-dessus du titre du hero'),
    ('entrepreneurship.hero.title', 'Entreprendre à Senghor', 'text', 'Titre principal du mini-site'),
    ('entrepreneurship.hero.slogan', 'INNOVER. AGIR. TRANSFORMER.', 'text', 'Slogan affiché sous le titre'),
    ('entrepreneurship.hero.subtitle', 'Le Pôle Entrepreneuriat et Innovation (PEI) accompagne les étudiants et alumni de l''Université Senghor, de l''idée à l''entreprise.', 'text', 'Phrase d''introduction du hero'),
    ('entrepreneurship.hero.cta1.text', 'Devenir étudiant-entrepreneur', 'text', 'Texte du bouton principal (vers le statut étudiant-entrepreneur)'),
    ('entrepreneurship.hero.cta2.text', 'Découvrir le parcours', 'text', 'Texte du bouton secondaire (vers le parcours)'),
    ('entrepreneurship.hero.slide1.image', '', 'text', 'Première image de fond du hero'),
    ('entrepreneurship.hero.slide2.image', '', 'text', 'Deuxième image de fond du hero'),
    ('entrepreneurship.hero.slide3.image', '', 'text', 'Troisième image de fond du hero'),
    ('entrepreneurship.presentation.badge', 'Présentation du pôle', 'text', 'Libellé de la section présentation'),
    ('entrepreneurship.presentation.title', 'Une université entrepreneuriale de référence', 'text', 'Titre de la section présentation'),
    ('entrepreneurship.presentation.content', '<p>Créé en 2022 au sein de la Direction du Développement et de l''Entrepreneuriat (DDE), le PEI favorise l''émergence, l''accompagnement et la réussite des initiatives portées par nos étudiants et alumni, en insufflant une véritable culture d''intrapreneuriat.</p><p>Catalyseur de talents à l''échelle du continent, le pôle a structuré un parcours contextualisé, de la sensibilisation à l''incubation, appuyé sur deux piliers : le programme de pré-incubation « Mature Ton Idée » et l''incubateur « Senghor''Innov ».</p><p>Pour 2025-2027, ses grands chantiers sont l''opérationnalisation du Statut de l''Étudiant-Entrepreneur, la réforme des parcours de formation et l''organisation d''un hackathon international.</p>', 'html', 'Présentation du pôle (HTML)'),
    ('entrepreneurship.presentation.link', 'Historique, vision et missions du pôle', 'text', 'Texte du lien vers la page de présentation détaillée'),
    ('entrepreneurship.stats.title', 'Chiffres clés', 'text', 'Titre du bloc des chiffres clés'),
    ('entrepreneurship.stats.1.value', '3', 'text', 'Valeur du premier chiffre clé'),
    ('entrepreneurship.stats.1.label', 'ans d''existence', 'text', 'Libellé du premier chiffre clé'),
    ('entrepreneurship.stats.2.value', '3', 'text', 'Valeur du deuxième chiffre clé'),
    ('entrepreneurship.stats.2.label', 'événements internationaux', 'text', 'Libellé du deuxième chiffre clé'),
    ('entrepreneurship.stats.3.value', '12', 'text', 'Valeur du troisième chiffre clé'),
    ('entrepreneurship.stats.3.label', 'lauréats du FSE', 'text', 'Libellé du troisième chiffre clé'),
    ('entrepreneurship.stats.4.value', '500+', 'text', 'Valeur du quatrième chiffre clé'),
    ('entrepreneurship.stats.4.label', 'étudiants et alumni formés', 'text', 'Libellé du quatrième chiffre clé'),
    ('entrepreneurship.activities.badge', 'Nos activités', 'text', 'Libellé de la section activités'),
    ('entrepreneurship.activities.title', 'Un parcours, de l''idée à l''entreprise', 'text', 'Titre de la section activités'),
    ('entrepreneurship.activities.subtitle', 'Le PEI a structuré son intervention autour d''un parcours de croissance complet, conçu pour transformer une simple intuition en une entreprise viable et structurée.', 'text', 'Introduction du parcours (les dispositifs sont gérés dans Entrepreneuriat → Dispositifs)'),
    ('entrepreneurship.activities.ecosystem.title', 'Et toute l''année, l''animation de l''écosystème', 'text', 'Titre du bloc d''animation de l''écosystème'),
    ('entrepreneurship.activities.ecosystem.items', 'Semaine Senghorienne de l''Entrepreneuriat (2SE)
Hackathons internationaux
Bootcamps
Afterworks
Séminaires et webinaires', 'text', 'Une action par ligne'),
    ('entrepreneurship.activities.link', 'Voir toutes nos activités', 'text', 'Texte du lien vers toutes les activités'),
    ('entrepreneurship.quote.text', 'L''accompagnement du Pôle Entrepreneuriat ne s''arrête pas au chèque ou à une reconnaissance académique. C''est tout un écosystème : le mentorat, l''accès au réseau de l''Université et à des espaces de travail et de créativité privilégiés, qui nous ouvre les portes à des investisseurs internationaux.', 'text', 'Texte de la citation'),
    ('entrepreneurship.quote.author', 'Gaël Gbonsou', 'text', 'Nom de l''auteur de la citation'),
    ('entrepreneurship.quote.role', 'Directeur du Développement et de l''Entrepreneuriat', 'text', 'Fonction de l''auteur de la citation'),
    ('entrepreneurship.quote.image', '', 'text', 'Portrait associé à la citation'),
    ('entrepreneurship.impact.text', 'L''impact est déjà tangible : 100 étudiants ont bénéficié d''un accompagnement personnalisé, menant à la distinction de 12 lauréats. Nos actions de sensibilisation ont touché plus de 500 étudiants et alumni, créant une dynamique de réseau durable.', 'text', 'Paragraphe présentant l''impact du pôle'),
    ('entrepreneurship.impact.image', '', 'text', 'Illustration du bloc impact'),
    ('entrepreneurship.cta.title', 'Prêt à passer à l''action ?', 'text', 'Titre de l''appel à l''action'),
    ('entrepreneurship.cta.description', 'Ne laissez pas votre projet dormir dans un tiroir. Entreprendre et étudier à Senghor, c''est possible grâce au statut d''étudiant-entrepreneur.', 'text', 'Texte de l''appel à l''action'),
    ('entrepreneurship.cta.button', 'Postuler au statut', 'text', 'Texte du bouton de l''appel à l''action'),
    ('entrepreneurship.contact.email', 'entrepreneuriat@usenghor.org', 'text', 'Adresse e-mail de contact du pôle'),
    ('entrepreneurship.see.call_slug', '', 'text', 'Slug de l''appel à candidatures du Statut Étudiant-Entrepreneur en cours (Candidatures → Appels)'),
    ('entrepreneurship.see.mentor.title', 'Vous êtes alumni entrepreneur ?', 'text', 'Titre de l''encart « devenir mentor »'),
    ('entrepreneurship.see.mentor.description', 'Rejoignez le réseau des mentors et accompagnez les nouvelles cohortes SEE 1 et SEE 2.', 'text', 'Texte de l''encart « devenir mentor »'),
    ('entrepreneurship.see.mentor.button', 'Devenir mentor', 'text', 'Texte du bouton de l''encart « devenir mentor »')
) AS v(key, value, value_type, description)
ON CONFLICT (key) DO NOTHING;

-- Service DDE : identifiant résolu depuis l'organigramme, vide sinon
INSERT INTO editorial_contents (key, value, value_type, category_id, description)
SELECT 'entrepreneurship.dde_service_id',
       COALESCE((SELECT id::text FROM services
                 WHERE name ILIKE '%Développement et de l''Entrepreneuriat%'
                 ORDER BY created_at LIMIT 1), ''),
       'text',
       (SELECT id FROM editorial_categories WHERE code = 'values'),
       'Identifiant du service DDE (organigramme) auquel sont rattachés actualités, événements et albums du PEI'
ON CONFLICT (key) DO NOTHING;

COMMIT;

\echo 'Migration 045_entrepreneurship terminée'
