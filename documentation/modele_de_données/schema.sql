-- ============================================================================
-- UNIVERSITÉ SENGHOR - SCHÉMA DE BASE DE DONNÉES
-- PostgreSQL 15+
-- ============================================================================

-- ============================================================================
-- EXTENSIONS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TYPES ÉNUMÉRÉS
-- ============================================================================

-- Civilités
CREATE TYPE civilite AS ENUM ('M.', 'Mme', 'Dr', 'Pr');

-- Types de formation
CREATE TYPE type_formation AS ENUM ('master', 'doctorat', 'diplome_universite', 'formation_certifiante');

-- Statuts génériques
CREATE TYPE statut_publication AS ENUM ('brouillon', 'publie', 'archive');

-- Statuts de candidature
CREATE TYPE statut_candidature AS ENUM ('ouverte', 'fermee', 'en_evaluation');

-- Types d'appel à candidature
CREATE TYPE type_appel AS ENUM ('candidature', 'bourse', 'projet', 'recrutement', 'formation');

-- Statuts d'appel
CREATE TYPE statut_appel AS ENUM ('en_cours', 'clos', 'a_venir');

-- Types d'événement
CREATE TYPE type_evenement AS ENUM ('conference', 'atelier', 'ceremonie', 'seminaire', 'colloque', 'autre');

-- Statuts d'actualité
CREATE TYPE statut_actualite AS ENUM ('standard', 'a_la_une', 'en_vedette');

-- Types de partenaire
CREATE TYPE type_partenaire AS ENUM ('operateur_charte', 'partenaire_campus', 'partenaire_formation', 'partenaire_projet', 'autre');

-- Situations familiales
CREATE TYPE situation_familiale AS ENUM ('celibataire', 'marie', 'divorce', 'veuf', 'autre');

-- Situations professionnelles
CREATE TYPE situation_professionnelle AS ENUM ('etudiant', 'enseignant', 'fonctionnaire', 'salarie_prive', 'employe_ong', 'sans_emploi', 'autre');

-- Durées d'expérience
CREATE TYPE duree_experience AS ENUM ('moins_1_an', 'entre_1_3_ans', 'entre_3_5_ans', 'entre_5_10_ans', 'plus_10_ans');

-- Types de média
CREATE TYPE type_media AS ENUM ('image', 'video', 'document', 'audio');

-- Statuts de candidature soumise
CREATE TYPE statut_candidature_soumise AS ENUM ('soumise', 'en_cours_evaluation', 'acceptee', 'refusee', 'liste_attente', 'incomplete');

-- Types de contenu éditorial
CREATE TYPE type_valeur_editoriale AS ENUM ('texte', 'nombre', 'json', 'html', 'markdown');

-- Statuts de projet
CREATE TYPE statut_projet AS ENUM ('en_cours', 'termine', 'suspendu', 'planifie');

-- ============================================================================
-- TABLES DE RÉFÉRENCE
-- ============================================================================

-- Pays
CREATE TABLE pays (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code_iso CHAR(2) UNIQUE NOT NULL,
    code_iso3 CHAR(3) UNIQUE,
    nom_fr VARCHAR(100) NOT NULL,
    nom_en VARCHAR(100),
    nom_ar VARCHAR(100),
    indicatif_tel VARCHAR(10),
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pays_code_iso ON pays(code_iso);
CREATE INDEX idx_pays_nom_fr ON pays(nom_fr);

-- ============================================================================
-- MÉDIAS ET FICHIERS
-- ============================================================================

-- Table centralisée des médias
CREATE TABLE medias (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nom VARCHAR(255) NOT NULL,
    description TEXT,
    type type_media NOT NULL,
    url VARCHAR(500) NOT NULL,
    url_externe BOOLEAN DEFAULT FALSE,
    taille_octets BIGINT,
    mime_type VARCHAR(100),
    largeur INT,
    hauteur INT,
    duree_secondes INT,
    alt_text VARCHAR(255),
    credits VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_medias_type ON medias(type);

-- Albums (regroupement de médias)
CREATE TABLE albums (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titre VARCHAR(255) NOT NULL,
    description TEXT,
    statut statut_publication DEFAULT 'brouillon',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Relation albums <-> médias
CREATE TABLE album_medias (
    album_id UUID REFERENCES albums(id) ON DELETE CASCADE,
    media_id UUID REFERENCES medias(id) ON DELETE CASCADE,
    ordre INT DEFAULT 0,
    PRIMARY KEY (album_id, media_id)
);

-- ============================================================================
-- UTILISATEURS ET AUTHENTIFICATION
-- ============================================================================

-- Permissions (actions possibles)
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    nom_fr VARCHAR(100) NOT NULL,
    description TEXT,
    categorie VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rôles
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    nom_fr VARCHAR(100) NOT NULL,
    description TEXT,
    niveau_hierarchie INT DEFAULT 0,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Relation rôles <-> permissions
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Utilisateurs
CREATE TABLE utilisateurs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    mot_de_passe_hash VARCHAR(255),
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    civilite civilite,
    date_naissance DATE,
    telephone VARCHAR(30),
    telephone_whatsapp VARCHAR(30),
    linkedin VARCHAR(255),
    photo_id UUID REFERENCES medias(id) ON DELETE SET NULL,
    nationalite_id UUID REFERENCES pays(id),
    pays_residence_id UUID REFERENCES pays(id),
    ville VARCHAR(100),
    adresse TEXT,
    actif BOOLEAN DEFAULT TRUE,
    email_verifie BOOLEAN DEFAULT FALSE,
    derniere_connexion TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_utilisateurs_email ON utilisateurs(email);
CREATE INDEX idx_utilisateurs_nom ON utilisateurs(nom, prenom);

-- Relation utilisateurs <-> rôles
CREATE TABLE utilisateur_roles (
    utilisateur_id UUID REFERENCES utilisateurs(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    campus_id UUID, -- Rattachement optionnel à un campus (ajouté après création de la table campus)
    date_attribution TIMESTAMPTZ DEFAULT NOW(),
    attribue_par UUID REFERENCES utilisateurs(id),
    PRIMARY KEY (utilisateur_id, role_id)
);

-- Tokens de réinitialisation et vérification
CREATE TABLE tokens_utilisateur (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    utilisateur_id UUID REFERENCES utilisateurs(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'verification_email', 'reset_password'
    expire_at TIMESTAMPTZ NOT NULL,
    utilise BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tokens_token ON tokens_utilisateur(token);

-- ============================================================================
-- STRUCTURE ORGANISATIONNELLE
-- ============================================================================

-- Départements / Directions
CREATE TABLE departements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(20) UNIQUE NOT NULL,
    denomination VARCHAR(255) NOT NULL,
    presentation TEXT,
    mission TEXT,
    icone_id UUID REFERENCES medias(id) ON DELETE SET NULL,
    image_couverture_id UUID REFERENCES medias(id) ON DELETE SET NULL,
    responsable_id UUID REFERENCES utilisateurs(id) ON DELETE SET NULL,
    ordre_affichage INT DEFAULT 0,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Services de département
CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    departement_id UUID REFERENCES departements(id) ON DELETE CASCADE,
    nom VARCHAR(255) NOT NULL,
    presentation TEXT,
    mission TEXT,
    responsable_id UUID REFERENCES utilisateurs(id) ON DELETE SET NULL,
    email VARCHAR(255),
    telephone VARCHAR(30),
    album_id UUID REFERENCES albums(id) ON DELETE SET NULL,
    ordre_affichage INT DEFAULT 0,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Objectifs d'un service
CREATE TABLE service_objectifs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    titre VARCHAR(255) NOT NULL,
    description TEXT,
    ordre INT DEFAULT 0
);

-- Réalisations d'un service
CREATE TABLE service_realisations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    titre VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(100),
    image_couverture_id UUID REFERENCES medias(id) ON DELETE SET NULL,
    date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Projets internes d'un service
CREATE TABLE service_projets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    titre VARCHAR(255) NOT NULL,
    description TEXT,
    image_couverture_id UUID REFERENCES medias(id) ON DELETE SET NULL,
    progression INT DEFAULT 0 CHECK (progression >= 0 AND progression <= 100),
    statut statut_projet DEFAULT 'planifie',
    date_debut DATE,
    date_fin_prevue DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Médiathèque d'un service (plusieurs albums possibles)
CREATE TABLE service_mediatheque (
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    album_id UUID REFERENCES albums(id) ON DELETE CASCADE,
    PRIMARY KEY (service_id, album_id)
);

-- ============================================================================
-- PARTENAIRES
-- ============================================================================

CREATE TABLE partenaires (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nom VARCHAR(255) NOT NULL,
    presentation TEXT,
    logo_id UUID REFERENCES medias(id) ON DELETE SET NULL,
    site_web VARCHAR(500),
    type type_partenaire NOT NULL,
    pays_id UUID REFERENCES pays(id),
    email VARCHAR(255),
    telephone VARCHAR(30),
    ordre_affichage INT DEFAULT 0,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_partenaires_type ON partenaires(type);

-- ============================================================================
-- CAMPUS
-- ============================================================================

CREATE TABLE campus (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(20) UNIQUE NOT NULL,
    nom VARCHAR(255) NOT NULL,
    description TEXT,
    image_couverture_id UUID REFERENCES medias(id) ON DELETE SET NULL,
    email VARCHAR(255),
    telephone VARCHAR(30),
    pays_id UUID REFERENCES pays(id),
    ville VARCHAR(100),
    adresse TEXT,
    code_postal VARCHAR(20),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    est_siege BOOLEAN DEFAULT FALSE,
    responsable_id UUID REFERENCES utilisateurs(id) ON DELETE SET NULL,
    album_id UUID REFERENCES albums(id) ON DELETE SET NULL,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_campus_pays ON campus(pays_id);

-- Ajout de la contrainte FK pour utilisateur_roles.campus_id
ALTER TABLE utilisateur_roles
ADD CONSTRAINT fk_utilisateur_roles_campus
FOREIGN KEY (campus_id) REFERENCES campus(id) ON DELETE SET NULL;

-- Relation campus <-> partenaires
CREATE TABLE campus_partenaires (
    campus_id UUID REFERENCES campus(id) ON DELETE CASCADE,
    partenaire_id UUID REFERENCES partenaires(id) ON DELETE CASCADE,
    date_debut DATE,
    date_fin DATE,
    PRIMARY KEY (campus_id, partenaire_id)
);

-- Équipe d'un campus
CREATE TABLE campus_equipe (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campus_id UUID REFERENCES campus(id) ON DELETE CASCADE,
    utilisateur_id UUID REFERENCES utilisateurs(id) ON DELETE CASCADE,
    fonction VARCHAR(255) NOT NULL,
    ordre_affichage INT DEFAULT 0,
    date_debut DATE,
    date_fin DATE,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Médiathèque d'un campus (plusieurs albums possibles)
CREATE TABLE campus_mediatheque (
    campus_id UUID REFERENCES campus(id) ON DELETE CASCADE,
    album_id UUID REFERENCES albums(id) ON DELETE CASCADE,
    PRIMARY KEY (campus_id, album_id)
);

-- ============================================================================
-- FORMATIONS
-- ============================================================================

CREATE TABLE formations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(30) UNIQUE NOT NULL,
    titre VARCHAR(255) NOT NULL,
    sous_titre VARCHAR(255),
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    modalites_pedagogiques TEXT,
    image_couverture_id UUID REFERENCES medias(id) ON DELETE SET NULL,
    type type_formation NOT NULL,
    duree_mois INT,
    nombre_credits INT,
    diplome_obtenu VARCHAR(255),
    diplome_requis TEXT,
    departement_id UUID REFERENCES departements(id) ON DELETE SET NULL,
    responsable_id UUID REFERENCES utilisateurs(id) ON DELETE SET NULL,
    statut statut_publication DEFAULT 'brouillon',
    ordre_affichage INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_formations_type ON formations(type);
CREATE INDEX idx_formations_slug ON formations(slug);
CREATE INDEX idx_formations_departement ON formations(departement_id);

-- Campus où se déroule une formation
CREATE TABLE formation_campus (
    formation_id UUID REFERENCES formations(id) ON DELETE CASCADE,
    campus_id UUID REFERENCES campus(id) ON DELETE CASCADE,
    PRIMARY KEY (formation_id, campus_id)
);

-- Partenaires d'une formation
CREATE TABLE formation_partenaires (
    formation_id UUID REFERENCES formations(id) ON DELETE CASCADE,
    partenaire_id UUID REFERENCES partenaires(id) ON DELETE CASCADE,
    type_partenariat VARCHAR(100),
    PRIMARY KEY (formation_id, partenaire_id)
);

-- Programme de formation (semestres)
CREATE TABLE formation_semestres (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    formation_id UUID REFERENCES formations(id) ON DELETE CASCADE,
    numero INT NOT NULL,
    titre VARCHAR(255),
    credits INT DEFAULT 1,
    ordre INT DEFAULT 0,
    UNIQUE (formation_id, numero)
);

-- Unités d'enseignement (UE) d'un semestre
CREATE TABLE formation_ues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    semestre_id UUID REFERENCES formation_semestres(id) ON DELETE CASCADE,
    code VARCHAR(20),
    titre VARCHAR(255) NOT NULL,
    description TEXT,
    credits INT,
    heures_cm INT DEFAULT 0,
    heures_td INT DEFAULT 0,
    heures_tp INT DEFAULT 0,
    coefficient DECIMAL(4, 2),
    ordre INT DEFAULT 0
);

-- Débouchés d'une formation
CREATE TABLE formation_debouches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    formation_id UUID REFERENCES formations(id) ON DELETE CASCADE,
    titre VARCHAR(255) NOT NULL,
    description TEXT,
    ordre INT DEFAULT 0
);

-- Compétences visées par une formation
CREATE TABLE formation_competences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    formation_id UUID REFERENCES formations(id) ON DELETE CASCADE,
    titre VARCHAR(255) NOT NULL,
    description TEXT,
    ordre INT DEFAULT 0
);

-- ============================================================================
-- APPELS À CANDIDATURE
-- ============================================================================

CREATE TABLE appels_candidature (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titre VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    image_couverture_id UUID REFERENCES medias(id) ON DELETE SET NULL,
    type type_appel NOT NULL,
    statut statut_appel DEFAULT 'a_venir',
    date_ouverture DATE,
    date_limite TIMESTAMPTZ,
    formation_id UUID REFERENCES formations(id) ON DELETE SET NULL,
    campus_id UUID REFERENCES campus(id) ON DELETE SET NULL,
    date_debut_programme DATE,
    date_fin_programme DATE,
    publics_cibles TEXT,
    frais_inscription DECIMAL(10, 2),
    devise VARCHAR(10) DEFAULT 'EUR',
    url_formulaire_externe VARCHAR(500),
    utiliser_formulaire_interne BOOLEAN DEFAULT TRUE,
    statut_publication statut_publication DEFAULT 'brouillon',
    created_by UUID REFERENCES utilisateurs(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_appels_type ON appels_candidature(type);
CREATE INDEX idx_appels_statut ON appels_candidature(statut);
CREATE INDEX idx_appels_date_limite ON appels_candidature(date_limite);
CREATE INDEX idx_appels_slug ON appels_candidature(slug);

-- Critères d'éligibilité d'un appel
CREATE TABLE appel_criteres_eligibilite (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appel_id UUID REFERENCES appels_candidature(id) ON DELETE CASCADE,
    critere TEXT NOT NULL,
    obligatoire BOOLEAN DEFAULT TRUE,
    ordre INT DEFAULT 0
);

-- Prises en charge d'un appel
CREATE TABLE appel_prises_en_charge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appel_id UUID REFERENCES appels_candidature(id) ON DELETE CASCADE,
    element VARCHAR(255) NOT NULL,
    description TEXT,
    ordre INT DEFAULT 0
);

-- Documents requis pour un appel
CREATE TABLE appel_documents_requis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appel_id UUID REFERENCES appels_candidature(id) ON DELETE CASCADE,
    nom_document VARCHAR(255) NOT NULL,
    description TEXT,
    obligatoire BOOLEAN DEFAULT TRUE,
    formats_acceptes VARCHAR(100), -- ex: 'pdf,doc,docx'
    taille_max_mo INT,
    ordre INT DEFAULT 0
);

-- Calendrier récapitulatif d'un appel
CREATE TABLE appel_calendrier (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appel_id UUID REFERENCES appels_candidature(id) ON DELETE CASCADE,
    etape VARCHAR(255) NOT NULL,
    date_debut DATE,
    date_fin DATE,
    description TEXT,
    ordre INT DEFAULT 0
);

-- ============================================================================
-- CANDIDATURES SOUMISES
-- ============================================================================

-- Candidatures formation
CREATE TABLE candidatures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    numero_dossier VARCHAR(50) UNIQUE NOT NULL,
    appel_id UUID REFERENCES appels_candidature(id) ON DELETE SET NULL,
    formation_id UUID REFERENCES formations(id) ON DELETE SET NULL,
    utilisateur_id UUID REFERENCES utilisateurs(id) ON DELETE SET NULL,

    -- Informations personnelles (peuvent différer du profil utilisateur)
    civilite civilite,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE,
    ville_naissance VARCHAR(100),
    pays_naissance_id UUID REFERENCES pays(id),
    nationalite_id UUID REFERENCES pays(id),
    situation_familiale situation_familiale,
    situation_professionnelle situation_professionnelle,
    situation_professionnelle_autre VARCHAR(255),

    -- Coordonnées
    adresse TEXT,
    ville VARCHAR(100),
    code_postal VARCHAR(20),
    pays_id UUID REFERENCES pays(id),
    telephone VARCHAR(30),
    telephone_whatsapp VARCHAR(30),
    email VARCHAR(255) NOT NULL,

    -- Informations professionnelles
    a_experience_professionnelle BOOLEAN DEFAULT FALSE,
    emploi_actuel VARCHAR(255),
    fonction_titre VARCHAR(255),
    organisme_employeur VARCHAR(255),
    employeur_adresse TEXT,
    employeur_ville VARCHAR(100),
    employeur_pays_id UUID REFERENCES pays(id),
    employeur_telephone VARCHAR(30),
    employeur_email VARCHAR(255),
    duree_experience duree_experience,

    -- Formation académique
    niveau_diplome_eleve VARCHAR(100),
    intitule_diplome_eleve VARCHAR(255),
    date_obtention_diplome DATE,
    lieu_obtention_diplome VARCHAR(255),

    -- Statut
    statut statut_candidature_soumise DEFAULT 'soumise',
    date_soumission TIMESTAMPTZ DEFAULT NOW(),
    date_evaluation TIMESTAMPTZ,
    evaluateur_id UUID REFERENCES utilisateurs(id),
    notes_evaluation TEXT,
    score_evaluation DECIMAL(5, 2),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_candidatures_numero ON candidatures(numero_dossier);
CREATE INDEX idx_candidatures_appel ON candidatures(appel_id);
CREATE INDEX idx_candidatures_statut ON candidatures(statut);
CREATE INDEX idx_candidatures_utilisateur ON candidatures(utilisateur_id);

-- Diplômes du candidat
CREATE TABLE candidature_diplomes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidature_id UUID REFERENCES candidatures(id) ON DELETE CASCADE,
    titre VARCHAR(255) NOT NULL,
    annee INT,
    etablissement VARCHAR(255),
    ville VARCHAR(100),
    pays_id UUID REFERENCES pays(id),
    specialite VARCHAR(255),
    mention VARCHAR(50),
    ordre INT DEFAULT 0
);

-- Documents soumis par le candidat
CREATE TABLE candidature_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidature_id UUID REFERENCES candidatures(id) ON DELETE CASCADE,
    document_requis_id UUID REFERENCES appel_documents_requis(id) ON DELETE SET NULL,
    nom_document VARCHAR(255) NOT NULL,
    media_id UUID REFERENCES medias(id) ON DELETE SET NULL,
    valide BOOLEAN,
    commentaire_validation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- ÉVÉNEMENTS
-- ============================================================================

CREATE TABLE evenements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titre VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    contenu TEXT, -- Contenu riche
    image_couverture_id UUID REFERENCES medias(id) ON DELETE SET NULL,
    type type_evenement NOT NULL,
    type_autre VARCHAR(100), -- Si type = 'autre'
    date_debut TIMESTAMPTZ NOT NULL,
    date_fin TIMESTAMPTZ,
    lieu VARCHAR(255),
    adresse TEXT,
    ville VARCHAR(100),
    pays_id UUID REFERENCES pays(id),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    en_ligne BOOLEAN DEFAULT FALSE,
    lien_visio VARCHAR(500),
    inscription_requise BOOLEAN DEFAULT FALSE,
    lien_inscription VARCHAR(500),
    nombre_places INT,
    campus_id UUID REFERENCES campus(id) ON DELETE SET NULL,
    departement_id UUID REFERENCES departements(id) ON DELETE SET NULL,
    projet_id UUID, -- FK ajoutée après création de la table projets
    organisateur_id UUID REFERENCES utilisateurs(id) ON DELETE SET NULL,
    album_id UUID REFERENCES albums(id) ON DELETE SET NULL,
    statut statut_publication DEFAULT 'brouillon',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_evenements_date ON evenements(date_debut);
CREATE INDEX idx_evenements_projet ON evenements(projet_id);
CREATE INDEX idx_evenements_type ON evenements(type);
CREATE INDEX idx_evenements_slug ON evenements(slug);

-- Partenaires d'un événement
CREATE TABLE evenement_partenaires (
    evenement_id UUID REFERENCES evenements(id) ON DELETE CASCADE,
    partenaire_id UUID REFERENCES partenaires(id) ON DELETE CASCADE,
    PRIMARY KEY (evenement_id, partenaire_id)
);

-- Inscriptions à un événement
CREATE TABLE evenement_inscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evenement_id UUID REFERENCES evenements(id) ON DELETE CASCADE,
    utilisateur_id UUID REFERENCES utilisateurs(id) ON DELETE SET NULL,
    -- Pour les non-inscrits
    nom VARCHAR(100),
    prenom VARCHAR(100),
    email VARCHAR(255) NOT NULL,
    telephone VARCHAR(30),
    organisation VARCHAR(255),
    statut VARCHAR(50) DEFAULT 'inscrit', -- inscrit, confirme, annule, present
    date_inscription TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (evenement_id, email)
);

-- Médiathèque d'un événement (plusieurs albums possibles)
CREATE TABLE evenement_mediatheque (
    evenement_id UUID REFERENCES evenements(id) ON DELETE CASCADE,
    album_id UUID REFERENCES albums(id) ON DELETE CASCADE,
    PRIMARY KEY (evenement_id, album_id)
);

-- ============================================================================
-- ACTUALITÉS
-- ============================================================================

CREATE TABLE actualites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titre VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    contenu TEXT, -- Contenu riche (HTML/Markdown)
    image_couverture_id UUID REFERENCES medias(id) ON DELETE SET NULL,
    video_url VARCHAR(500),
    statut_mise_en_avant statut_actualite DEFAULT 'standard',
    statut statut_publication DEFAULT 'brouillon',
    date_publication TIMESTAMPTZ,
    visible_a_partir_de TIMESTAMPTZ,
    campus_id UUID REFERENCES campus(id) ON DELETE SET NULL,
    departement_id UUID REFERENCES departements(id) ON DELETE SET NULL,
    service_id UUID REFERENCES services(id) ON DELETE SET NULL,
    evenement_id UUID REFERENCES evenements(id) ON DELETE SET NULL,
    projet_id UUID, -- FK ajoutée après création de la table projets
    auteur_id UUID REFERENCES utilisateurs(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_actualites_date ON actualites(date_publication);
CREATE INDEX idx_actualites_statut ON actualites(statut, statut_mise_en_avant);
CREATE INDEX idx_actualites_slug ON actualites(slug);
CREATE INDEX idx_actualites_projet ON actualites(projet_id);

-- Photos d'une actualité
CREATE TABLE actualite_medias (
    actualite_id UUID REFERENCES actualites(id) ON DELETE CASCADE,
    media_id UUID REFERENCES medias(id) ON DELETE CASCADE,
    ordre INT DEFAULT 0,
    PRIMARY KEY (actualite_id, media_id)
);

-- Tags/catégories pour actualités
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nom VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    icone VARCHAR(50),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE actualite_tags (
    actualite_id UUID REFERENCES actualites(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (actualite_id, tag_id)
);

-- ============================================================================
-- PROJETS
-- ============================================================================

-- Catégories de projets
CREATE TABLE projet_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nom VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icone VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE projets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titre VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    resume TEXT,
    description TEXT,
    image_couverture_id UUID REFERENCES medias(id) ON DELETE SET NULL,
    date_debut DATE,
    date_fin DATE,
    budget DECIMAL(15, 2),
    devise VARCHAR(10) DEFAULT 'EUR',
    beneficiaires TEXT,
    statut statut_projet DEFAULT 'planifie',
    statut_publication statut_publication DEFAULT 'brouillon',
    departement_id UUID REFERENCES departements(id) ON DELETE SET NULL,
    responsable_id UUID REFERENCES utilisateurs(id) ON DELETE SET NULL,
    album_id UUID REFERENCES albums(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_projets_statut ON projets(statut);
CREATE INDEX idx_projets_slug ON projets(slug);

-- Pays concernés par un projet
CREATE TABLE projet_pays (
    projet_id UUID REFERENCES projets(id) ON DELETE CASCADE,
    pays_id UUID REFERENCES pays(id) ON DELETE CASCADE,
    PRIMARY KEY (projet_id, pays_id)
);

-- Catégories d'un projet
CREATE TABLE projet_projet_categories (
    projet_id UUID REFERENCES projets(id) ON DELETE CASCADE,
    categorie_id UUID REFERENCES projet_categories(id) ON DELETE CASCADE,
    PRIMARY KEY (projet_id, categorie_id)
);

-- Partenaires d'un projet
CREATE TABLE projet_partenaires (
    projet_id UUID REFERENCES projets(id) ON DELETE CASCADE,
    partenaire_id UUID REFERENCES partenaires(id) ON DELETE CASCADE,
    role_partenaire VARCHAR(255),
    PRIMARY KEY (projet_id, partenaire_id)
);

-- Appels liés à un projet
CREATE TABLE projet_appels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    projet_id UUID REFERENCES projets(id) ON DELETE CASCADE,
    titre VARCHAR(255) NOT NULL,
    description TEXT,
    statut statut_appel DEFAULT 'a_venir',
    conditions TEXT,
    type type_appel,
    date_limite TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Médiathèque d'un projet (plusieurs albums possibles)
CREATE TABLE projet_mediatheque (
    projet_id UUID REFERENCES projets(id) ON DELETE CASCADE,
    album_id UUID REFERENCES albums(id) ON DELETE CASCADE,
    PRIMARY KEY (projet_id, album_id)
);

-- Ajout des FK vers projets pour evenements et actualites
ALTER TABLE evenements
ADD CONSTRAINT fk_evenements_projet
FOREIGN KEY (projet_id) REFERENCES projets(id) ON DELETE SET NULL;

ALTER TABLE actualites
ADD CONSTRAINT fk_actualites_projet
FOREIGN KEY (projet_id) REFERENCES projets(id) ON DELETE SET NULL;

-- ============================================================================
-- CONTENUS ÉDITORIAUX ET CONFIGURATION
-- ============================================================================

-- Catégories de contenus éditoriaux
CREATE TABLE contenu_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Contenus éditoriaux de configuration
CREATE TABLE contenus_editoriaux (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cle VARCHAR(100) UNIQUE NOT NULL,
    valeur TEXT,
    type_valeur type_valeur_editoriale DEFAULT 'texte',
    categorie_id UUID REFERENCES contenu_categories(id) ON DELETE SET NULL,
    annee_concernee INT,
    description TEXT,
    modifiable_par_admin BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_contenus_cle ON contenus_editoriaux(cle);
CREATE INDEX idx_contenus_categorie ON contenus_editoriaux(categorie_id);

-- Historique des modifications de contenus éditoriaux
CREATE TABLE contenus_editoriaux_historique (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contenu_id UUID REFERENCES contenus_editoriaux(id) ON DELETE CASCADE,
    ancienne_valeur TEXT,
    nouvelle_valeur TEXT,
    modifie_par UUID REFERENCES utilisateurs(id),
    modifie_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- NEWSLETTER
-- ============================================================================

-- Abonnés à la newsletter
CREATE TABLE newsletter_abonnes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    utilisateur_id UUID REFERENCES utilisateurs(id) ON DELETE SET NULL,
    actif BOOLEAN DEFAULT TRUE,
    token_desinscription VARCHAR(255) UNIQUE,
    source VARCHAR(100), -- d'où vient l'inscription
    date_inscription TIMESTAMPTZ DEFAULT NOW(),
    date_desinscription TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_newsletter_email ON newsletter_abonnes(email);

-- Campagnes de newsletter
CREATE TABLE newsletter_campagnes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titre VARCHAR(255) NOT NULL,
    sujet VARCHAR(255) NOT NULL,
    contenu_html TEXT,
    contenu_texte TEXT,
    statut VARCHAR(50) DEFAULT 'brouillon', -- brouillon, programmee, envoyee
    date_envoi_programmee TIMESTAMPTZ,
    date_envoi_effective TIMESTAMPTZ,
    nombre_destinataires INT DEFAULT 0,
    nombre_ouvertures INT DEFAULT 0,
    nombre_clics INT DEFAULT 0,
    created_by UUID REFERENCES utilisateurs(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Historique d'envoi par destinataire
CREATE TABLE newsletter_envois (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campagne_id UUID REFERENCES newsletter_campagnes(id) ON DELETE CASCADE,
    abonne_id UUID REFERENCES newsletter_abonnes(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    statut VARCHAR(50) DEFAULT 'envoye', -- envoye, ouvert, clique, erreur
    date_envoi TIMESTAMPTZ DEFAULT NOW(),
    date_ouverture TIMESTAMPTZ,
    date_clic TIMESTAMPTZ,
    erreur_message TEXT
);

CREATE INDEX idx_newsletter_envois_campagne ON newsletter_envois(campagne_id);

-- ============================================================================
-- AUDIT ET LOGS
-- ============================================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    utilisateur_id UUID REFERENCES utilisateurs(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL, -- create, update, delete, login, logout
    table_concernee VARCHAR(100),
    enregistrement_id UUID,
    anciennes_valeurs JSONB,
    nouvelles_valeurs JSONB,
    ip_adresse INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_utilisateur ON audit_logs(utilisateur_id);
CREATE INDEX idx_audit_table ON audit_logs(table_concernee);
CREATE INDEX idx_audit_date ON audit_logs(created_at);

-- ============================================================================
-- FONCTIONS ET TRIGGERS
-- ============================================================================

-- Fonction pour mettre à jour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Application du trigger sur toutes les tables avec updated_at
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT table_name
        FROM information_schema.columns
        WHERE column_name = 'updated_at'
        AND table_schema = 'public'
    LOOP
        EXECUTE format('
            CREATE TRIGGER update_%I_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', t, t);
    END LOOP;
END;
$$ language 'plpgsql';

-- Fonction pour générer un numéro de dossier de candidature
CREATE OR REPLACE FUNCTION generer_numero_dossier()
RETURNS TRIGGER AS $$
BEGIN
    NEW.numero_dossier = 'CAND-' || TO_CHAR(NOW(), 'YYYY') || '-' || LPAD(NEXTVAL('seq_candidature_numero')::TEXT, 6, '0');
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Séquence pour les numéros de dossier
CREATE SEQUENCE IF NOT EXISTS seq_candidature_numero START 1;

-- Trigger pour générer le numéro de dossier
CREATE TRIGGER trigger_generer_numero_dossier
BEFORE INSERT ON candidatures
FOR EACH ROW
WHEN (NEW.numero_dossier IS NULL)
EXECUTE FUNCTION generer_numero_dossier();

-- ============================================================================
-- DONNÉES INITIALES
-- ============================================================================

-- Rôles par défaut
INSERT INTO roles (code, nom_fr, description, niveau_hierarchie) VALUES
('super_admin', 'Super Administrateur', 'Accès complet à toutes les fonctionnalités', 100),
('admin', 'Administrateur', 'Administration générale de la plateforme', 80),
('admin_campus', 'Administrateur Campus', 'Administration d''un campus spécifique', 60),
('editeur', 'Éditeur', 'Création et modification de contenus', 40),
('moderateur', 'Modérateur', 'Modération des contenus et candidatures', 30),
('utilisateur', 'Utilisateur', 'Utilisateur standard inscrit', 10);

-- Catégories de contenus éditoriaux
INSERT INTO contenu_categories (code, nom, description) VALUES
('statistique', 'Statistiques', 'Chiffres clés et statistiques'),
('valeur', 'Valeurs', 'Valeurs de l''université'),
('strategie', 'Stratégie', 'Éléments stratégiques'),
('contact', 'Contact', 'Informations de contact'),
('reseaux_sociaux', 'Réseaux sociaux', 'Liens vers les réseaux sociaux'),
('legal', 'Mentions légales', 'Contenus juridiques');

-- Permissions de base
INSERT INTO permissions (code, nom_fr, categorie) VALUES
-- Gestion des utilisateurs
('users.view', 'Voir les utilisateurs', 'utilisateurs'),
('users.create', 'Créer des utilisateurs', 'utilisateurs'),
('users.edit', 'Modifier les utilisateurs', 'utilisateurs'),
('users.delete', 'Supprimer des utilisateurs', 'utilisateurs'),
('users.roles', 'Gérer les rôles des utilisateurs', 'utilisateurs'),
-- Gestion des formations
('formations.view', 'Voir les formations', 'formations'),
('formations.create', 'Créer des formations', 'formations'),
('formations.edit', 'Modifier les formations', 'formations'),
('formations.delete', 'Supprimer des formations', 'formations'),
-- Gestion des candidatures
('candidatures.view', 'Voir les candidatures', 'candidatures'),
('candidatures.evaluate', 'Évaluer les candidatures', 'candidatures'),
('candidatures.export', 'Exporter les candidatures', 'candidatures'),
-- Gestion des événements
('evenements.view', 'Voir les événements', 'evenements'),
('evenements.create', 'Créer des événements', 'evenements'),
('evenements.edit', 'Modifier les événements', 'evenements'),
('evenements.delete', 'Supprimer des événements', 'evenements'),
-- Gestion des actualités
('actualites.view', 'Voir les actualités', 'actualites'),
('actualites.create', 'Créer des actualités', 'actualites'),
('actualites.edit', 'Modifier les actualités', 'actualites'),
('actualites.delete', 'Supprimer des actualités', 'actualites'),
-- Gestion des campus
('campus.view', 'Voir les campus', 'campus'),
('campus.create', 'Créer des campus', 'campus'),
('campus.edit', 'Modifier les campus', 'campus'),
('campus.delete', 'Supprimer des campus', 'campus'),
-- Gestion des partenaires
('partenaires.view', 'Voir les partenaires', 'partenaires'),
('partenaires.create', 'Créer des partenaires', 'partenaires'),
('partenaires.edit', 'Modifier les partenaires', 'partenaires'),
('partenaires.delete', 'Supprimer des partenaires', 'partenaires'),
-- Gestion des contenus éditoriaux
('contenus.view', 'Voir les contenus éditoriaux', 'contenus'),
('contenus.edit', 'Modifier les contenus éditoriaux', 'contenus'),
-- Gestion de la newsletter
('newsletter.view', 'Voir les newsletters', 'newsletter'),
('newsletter.create', 'Créer des newsletters', 'newsletter'),
('newsletter.send', 'Envoyer des newsletters', 'newsletter'),
-- Administration
('admin.settings', 'Gérer les paramètres', 'administration'),
('admin.audit', 'Voir les logs d''audit', 'administration');

-- Attribution de toutes les permissions au super_admin
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.code = 'super_admin';

-- ============================================================================
-- VUES UTILES
-- ============================================================================

-- Vue des formations avec leurs campus
CREATE VIEW v_formations_campus AS
SELECT
    f.*,
    d.denomination as departement_nom,
    ARRAY_AGG(DISTINCT c.nom) FILTER (WHERE c.id IS NOT NULL) as campus_noms,
    ARRAY_AGG(DISTINCT c.id) FILTER (WHERE c.id IS NOT NULL) as campus_ids
FROM formations f
LEFT JOIN departements d ON f.departement_id = d.id
LEFT JOIN formation_campus fc ON f.id = fc.formation_id
LEFT JOIN campus c ON fc.campus_id = c.id
GROUP BY f.id, d.denomination;

-- Vue des événements à venir
CREATE VIEW v_evenements_a_venir AS
SELECT
    e.*,
    c.nom as campus_nom,
    p.nom_fr as pays_nom
FROM evenements e
LEFT JOIN campus c ON e.campus_id = c.id
LEFT JOIN pays p ON e.pays_id = p.id
WHERE e.statut = 'publie'
AND e.date_debut >= NOW()
ORDER BY e.date_debut ASC;

-- Vue des actualités publiées
CREATE VIEW v_actualites_publiees AS
SELECT
    a.*,
    u.nom as auteur_nom,
    u.prenom as auteur_prenom,
    c.nom as campus_nom,
    d.denomination as departement_nom
FROM actualites a
LEFT JOIN utilisateurs u ON a.auteur_id = u.id
LEFT JOIN campus c ON a.campus_id = c.id
LEFT JOIN departements d ON a.departement_id = d.id
WHERE a.statut = 'publie'
AND (a.visible_a_partir_de IS NULL OR a.visible_a_partir_de <= NOW())
ORDER BY a.date_publication DESC;

-- Vue statistiques des candidatures par appel
CREATE VIEW v_statistiques_candidatures AS
SELECT
    ac.id as appel_id,
    ac.titre as appel_titre,
    COUNT(c.id) as total_candidatures,
    COUNT(CASE WHEN c.statut = 'soumise' THEN 1 END) as soumises,
    COUNT(CASE WHEN c.statut = 'en_cours_evaluation' THEN 1 END) as en_evaluation,
    COUNT(CASE WHEN c.statut = 'acceptee' THEN 1 END) as acceptees,
    COUNT(CASE WHEN c.statut = 'refusee' THEN 1 END) as refusees,
    COUNT(CASE WHEN c.statut = 'liste_attente' THEN 1 END) as liste_attente
FROM appels_candidature ac
LEFT JOIN candidatures c ON ac.id = c.appel_id
GROUP BY ac.id, ac.titre;

-- ============================================================================
-- COMMENTAIRES POUR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE utilisateurs IS 'Utilisateurs inscrits sur la plateforme';
COMMENT ON TABLE roles IS 'Rôles définissant les permissions des utilisateurs';
COMMENT ON TABLE formations IS 'Formations proposées par l''Université Senghor';
COMMENT ON TABLE appels_candidature IS 'Appels à candidature (formations, bourses, projets, recrutements)';
COMMENT ON TABLE candidatures IS 'Candidatures soumises par les utilisateurs';
COMMENT ON TABLE evenements IS 'Événements organisés par l''université';
COMMENT ON TABLE actualites IS 'Articles d''actualité et news';
COMMENT ON TABLE campus IS 'Campus de l''université (siège et externalisés)';
COMMENT ON TABLE partenaires IS 'Partenaires de l''université';
COMMENT ON TABLE projets IS 'Projets de l''université';
COMMENT ON TABLE contenus_editoriaux IS 'Contenus de configuration dynamiques (statistiques, valeurs, etc.)';
COMMENT ON TABLE newsletter_abonnes IS 'Abonnés à la newsletter';
COMMENT ON TABLE medias IS 'Fichiers médias centralisés (images, vidéos, documents)';
