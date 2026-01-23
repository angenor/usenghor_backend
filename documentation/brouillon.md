# Analyse du modèle de données - Université Senghor

## 1. Utilisateurs

Il s'agit d'une personne inscrite sur la plateforme.

### 1.1. Propriétés (données utilisateur)

- nom
- prenom
- civilité
- nationalité
- pays
- email
- photo
- jour d'anniversaire
- téléphone (optionnel)
- rôles
- linkedin (optionnel)
- département (optionnel)
- campus (optionnel)

---

## 2. Rôle

Il s'agit des droits dont dispose une personne sur la plateforme sur certains éléments sur la plateforme: modifier, éditer, supprimer certains éléments selon le rôle qui lui a été attribué.

Un utilisateur peut avoir plusieurs rôles.

### 2.1. Propriétés

- dénomination du rôle
- date de création
- possibilités (ceux dont il est capable de modifier)

---

## 3. Formations

Il s'agit des différentes formations délivrées par l'Université Senghor. Pour une formation donnée, on peut avoir 0 ou plusieurs partenaires.

### 3.1. Propriétés

- titre de la formation
- sous-titre
- description
- modalités pédagogiques
- image de couverture
- type (master, doctorat, Diplômes d'Université, Formations certifiantes)
- durée de la formation
- nombre de crédit
- diplôme obtenu
- diplôme requis
- département
- statut candidature
- campus ou se déroule la formation
- programme [Semestres et leurs contenue + les crédits correspondants]
- date limite de candidature
- date de rentrée

---

## 4. Appels à candidatures

### 4.1. Propriétés

- titre de l'appel
- description
- image de couverture
- type (Candidatures, Bourses, Projets, Recrutements, formation)
- statut (En cours, clos)
- date limite de soumission
- campus
- Formation concerné
- dates du programme
- publics cibles
- critères d'éligibilité []
- prises en charge []
- frais d'inscription pédagogique
- dossier de candidature
- calendrier récapitulatif
- débouchés []
- compétences visées []

---

## 5. Événements

### 5.1. Propriétés

- titre
- description
- image de couverture
- date et heure de début
- date et heure de fin
- lieu
- inscription
- partenaires
- médiathèque (où l'on mettra après les photos et les vidéos de l'événement)
- actualité (un événement qui se tiendra dans 5 mois, est précédé de rencontres qu'il est bien de documenter sous forme d'article)
- Type d'événement (Conférences, Ateliers, Cérémonies, Autres (à préciser))

---

## 6. Actualités

### 6.1. Propriétés

- titre
- description
- statut (à la une, en vedette, standard)
- image de couverture
- visible à partir de (date et heure)
- vidéo (pour insertion de vidéo)
- photo (pour insérer des photo)

---

## 7. Département/Directions

### 7.1. Propriétés

- présentation
- dénomination
- icône/logo
- image de couverture

---

## 8. Services de département

### 8.1. Propriétés

- présentation
- département concernée
- mission
- objectifs principaux []
- equipe
- réalisations (titre, type, description, image de couverture, année)
- projets (titre, description, image de couverture, progression, statut)
- actualités (titre, description, image de couverture, date de publication)
- médiathèque (albums photos, videos, documents)

---

## 9. Partenaires

### 9.1. Propriétés

- nom
- logo
- présentation
- lien site web
- type (Opérateur de la charte, Partenaires Campus)

---

## 10. Campus externalisés

Il s'agit des autres lieux de formation externe au siège de l'université senghor d'alexandrie. On peut avoir 0 ou plusieurs événements, 0 ou plusieurs actualités liés à un campus. Un campus dispose d'une équipe. Un campus externalisé a au moins 1 partenaire.

### 10.1. Propriétés

- nom
- description
- image de couverture
- email
- téléphone
- pays
- ville
- adresse
- equipe
- partenaire(s)
- géolocalisation (longitude, latitude)
- actualités (titre, description, image de couverture, date de publication)
- médiathèque (albums photos, videos, documents)
- appel à candidature

---

## 11. Candidatures formation

### 11.1. Propriétés

#### Spécialité choisie

- Spécialité

#### Informations personnelles

- Formation
- Utilisateur (nom, prénom, pays, nationalité)
- Date de naissance
- Ville de naissance
- Situation familiale actuelle
- Situation professionnelle actuelle (Etudiant(e), Enseignant(e), Fonctionnaire, Salarié(e) du secteur privé, Employé(e) d'une ONG ou d'une coopération, Sans emploi, autre (à préciser))
- Spécialité choisie

#### Informations professionnelles

- Disposez-vous d'expériences professionnelles ? (Oui, Non)
- Emploi actuel
- Fonction ou titre
- Organisme employeur
- Adresse
- Ville
- Pays
- Téléphone
- Adresse email
- Durée de votre expérience professionnelle (1 ans, entre 1 et 3 ans, entre 3 et 5, entre 5 et 10, plus de 10 ans)

#### Adresse et coordonnées

- Adresse
- Ville
- Pays
- Téléphone - WhatsApp avec indicatif
- Téléphone

#### Formations

- Niveau du diplôme obtenu le plus élevé
- Intitulé du diplôme obtenu le plus élevé
- Date d'obtention
- Lieu d'obtention
- diplômes (Titre du diplôme, Année, Établissement, Ville, Pays, Spécialité)

#### Documents

- Lettre de recommandation
- CV
- Photo
- Lettre de motivation
- Passeport / Pièce d'identité
- Relevé de notes
- Diplômes
- Accord de l'employeur ou d'une autre organisation pour vous accueillir en stage

---

## 12. Candidatures enseignant

### 12.1. Propriétés

- xxx
- xxx

---

## 13. Projets

### 13.1. Propriétés

- titre
- résumé
- description
- période
- pays concernés (plusieurs pays possibles)
- Budget
- Bénéficiaires
- statut
- Catégorie (plusieurs catégorie possibles)
- Appels (titre, description, statut, conditions, type, date limite, partenaires)

---

## 14. Contenus éditoriaux de configurations

Il s'agit des valeurs textes, chiffres et autres de la plateforme. Ces valeurs sont dynamiques mais non automatiques.

### 14.1. Propriétés

- clé (nombre alumni, année création, nos valeurs, etc…)
- valeur
- type de valeur (text, nombre, json, html)
- catégorie (statistique, valeur, stratégie, etc): table dédié pour rendre encore plus flexible et prévoir des valeurs attendue selon
- année concernée (important pour historique de statistique)

---

## 15. Newsletter moderne et dynamique

---

## Notes

- Une personne n'est pas obligée de s'inscrire sur la plateforme pour pouvoir s'inscrire à un événement.
- Pour les candidats de formation. Il est possible de postuler directement sur la plateforme ou de rediriger vers un formulaire externe (google doc, etc…). L'administrateur va définir cela lors de la création de l'appel.
- Le super admin a tous les droits évidemment.
- Les droits d'un administrateur sont rattachés à un campus donné.
- Les images, vidéos et documents peuvent être soit uploadé directement sur le serveur ou bien juste un lien externe peut être enregistré.
- Dans le dashboard, selon son rôle, un utilisateur sera capable de voir ou non, d'ajouter ou non, de modifier ou non, de supprimer ou non.
