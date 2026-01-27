#!/usr/bin/env python3
"""
Seed script : Mentions Légales (Editorial)
==========================================
Crée les données de simulation pour les pages légales obligatoires
de l'Université Senghor via le système éditorial.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_editorial_legal.py
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.editorial import (
    EditorialCategory,
    EditorialContent,
    EditorialValueType,
)


# =============================================================================
# DONNÉES DES PAGES LÉGALES
# =============================================================================

# Mentions légales
LEGAL_NOTICE_CONTENT = """<h2>Éditeur du site</h2>
<p><strong>Université Senghor</strong><br>
1 Place Ahmed Orabi<br>
El Mancheya, Alexandrie<br>
Égypte</p>

<p><strong>Téléphone :</strong> +20 3 484 6155<br>
<strong>Email :</strong> info@usenghor.org</p>

<h2>Directeur de la publication</h2>
<p>Le Recteur de l'Université Senghor</p>

<h2>Hébergeur</h2>
<p><strong>Firebase Hosting</strong><br>
Google LLC<br>
1600 Amphitheatre Parkway<br>
Mountain View, CA 94043<br>
États-Unis</p>

<h2>Propriété intellectuelle</h2>
<p>L'ensemble des contenus (textes, images, vidéos, etc.) présents sur ce site sont la propriété exclusive de l'Université Senghor ou de ses partenaires. Toute reproduction, représentation, modification, publication, adaptation de tout ou partie des éléments du site, quel que soit le moyen ou le procédé utilisé, est interdite, sauf autorisation écrite préalable.</p>

<h2>Crédits</h2>
<p>Conception et développement : Équipe informatique de l'Université Senghor</p>"""

# Politique de confidentialité
PRIVACY_POLICY_CONTENT = """<h2>Introduction</h2>
<p>L'Université Senghor s'engage à protéger la vie privée des utilisateurs de son site internet. Cette politique de confidentialité explique comment nous collectons, utilisons et protégeons vos données personnelles.</p>

<h2>Données collectées</h2>
<p>Nous collectons les données suivantes :</p>
<ul>
<li><strong>Données d'identification :</strong> nom, prénom, adresse email</li>
<li><strong>Données de connexion :</strong> adresse IP, logs de connexion</li>
<li><strong>Données de navigation :</strong> pages visitées, durée des visites</li>
</ul>

<h2>Finalités du traitement</h2>
<p>Vos données sont utilisées pour :</p>
<ul>
<li>Répondre à vos demandes de contact</li>
<li>Vous envoyer notre newsletter (avec votre consentement)</li>
<li>Améliorer nos services</li>
<li>Établir des statistiques de fréquentation</li>
</ul>

<h2>Base légale</h2>
<p>Le traitement de vos données repose sur :</p>
<ul>
<li>Votre consentement</li>
<li>L'exécution d'un contrat</li>
<li>Nos intérêts légitimes</li>
</ul>

<h2>Durée de conservation</h2>
<p>Vos données sont conservées pendant une durée de 3 ans à compter de votre dernière interaction avec nous, sauf obligation légale contraire.</p>

<h2>Vos droits</h2>
<p>Conformément au RGPD, vous disposez des droits suivants :</p>
<ul>
<li>Droit d'accès à vos données</li>
<li>Droit de rectification</li>
<li>Droit à l'effacement</li>
<li>Droit à la limitation du traitement</li>
<li>Droit à la portabilité</li>
<li>Droit d'opposition</li>
</ul>

<h2>Contact DPO</h2>
<p>Pour exercer vos droits ou pour toute question relative à la protection de vos données, contactez notre Délégué à la Protection des Données :</p>
<p><strong>Email :</strong> dpo@usenghor.org</p>"""

# Conditions générales d'utilisation
TERMS_OF_USE_CONTENT = """<h2>Article 1 - Objet</h2>
<p>Les présentes Conditions Générales d'Utilisation (CGU) régissent l'accès et l'utilisation du site internet de l'Université Senghor.</p>

<h2>Article 2 - Accès au site</h2>
<p>Le site est accessible gratuitement à tout utilisateur disposant d'un accès à Internet. L'Université Senghor met en œuvre tous les moyens raisonnables à sa disposition pour assurer un accès de qualité au site.</p>

<h2>Article 3 - Propriété intellectuelle</h2>
<p>L'ensemble des éléments constituant le site (textes, graphismes, logiciels, photographies, images, sons, plans, logos, marques, créations, etc.) sont protégés par le droit de la propriété intellectuelle.</p>

<h2>Article 4 - Responsabilités</h2>
<p>L'Université Senghor ne saurait être tenue responsable :</p>
<ul>
<li>Des interruptions momentanées du site</li>
<li>De la présence de virus informatiques</li>
<li>Des dommages résultant de l'utilisation du site</li>
</ul>

<h2>Article 5 - Liens hypertextes</h2>
<p>Le site peut contenir des liens vers d'autres sites. L'Université Senghor n'exerce aucun contrôle sur ces sites et décline toute responsabilité quant à leur contenu.</p>

<h2>Article 6 - Modification des CGU</h2>
<p>L'Université Senghor se réserve le droit de modifier à tout moment les présentes CGU. Les utilisateurs seront informés de ces modifications par la mise en ligne des CGU actualisées.</p>

<h2>Article 7 - Droit applicable</h2>
<p>Les présentes CGU sont soumises au droit français. Tout litige relatif à l'interprétation ou à l'exécution des présentes sera soumis aux tribunaux compétents.</p>"""

# Politique de cookies
COOKIE_POLICY_CONTENT = """<h2>Qu'est-ce qu'un cookie ?</h2>
<p>Un cookie est un petit fichier texte déposé sur votre terminal (ordinateur, tablette, smartphone) lors de la visite d'un site web. Il permet au site de mémoriser des informations sur votre visite.</p>

<h2>Types de cookies utilisés</h2>

<h3>Cookies essentiels</h3>
<p>Ces cookies sont nécessaires au fonctionnement du site. Ils permettent d'utiliser les principales fonctionnalités du site (session, préférences linguistiques, etc.).</p>

<h3>Cookies analytiques</h3>
<p>Ces cookies nous permettent de mesurer l'audience du site et d'analyser les comportements de navigation pour améliorer nos services. Nous utilisons Google Analytics.</p>

<h3>Cookies marketing</h3>
<p>Ces cookies sont utilisés pour vous proposer des contenus personnalisés. Ils peuvent être déposés par nos partenaires publicitaires.</p>

<h2>Gestion des cookies</h2>
<p>Vous pouvez à tout moment gérer vos préférences en matière de cookies :</p>
<ul>
<li>Via le bandeau de consentement affiché lors de votre première visite</li>
<li>Via les paramètres de votre navigateur</li>
</ul>

<h2>Durée de conservation</h2>
<p>Les cookies sont conservés pour une durée maximale de 13 mois.</p>

<h2>Liste des cookies utilisés</h2>
<table>
<tr><th>Nom</th><th>Finalité</th><th>Durée</th></tr>
<tr><td>_ga</td><td>Google Analytics - Statistiques</td><td>2 ans</td></tr>
<tr><td>_gid</td><td>Google Analytics - Statistiques</td><td>24h</td></tr>
<tr><td>consent</td><td>Mémorisation du consentement</td><td>1 an</td></tr>
</table>

<h2>Plus d'informations</h2>
<p>Pour en savoir plus sur les cookies, vous pouvez consulter le site de la CNIL : <a href="https://www.cnil.fr/fr/cookies-et-autres-traceurs" target="_blank">www.cnil.fr</a></p>"""

# Liste des contenus à créer
LEGAL_CONTENTS = [
    {
        "key": "legal_notice",
        "title": "Mentions légales",
        "content": LEGAL_NOTICE_CONTENT,
        "description": "Informations légales sur l'éditeur, l'hébergeur et la propriété intellectuelle",
    },
    {
        "key": "privacy_policy",
        "title": "Politique de confidentialité",
        "content": PRIVACY_POLICY_CONTENT,
        "description": "Politique de protection des données personnelles (RGPD)",
    },
    {
        "key": "terms_of_use",
        "title": "Conditions générales d'utilisation",
        "content": TERMS_OF_USE_CONTENT,
        "description": "Conditions d'utilisation du site et des services",
    },
    {
        "key": "cookie_policy",
        "title": "Politique de cookies",
        "content": COOKIE_POLICY_CONTENT,
        "description": "Gestion des cookies et traceurs",
    },
]


# =============================================================================
# FONCTIONS DE SEED
# =============================================================================


async def get_or_create_legal_category(db) -> EditorialCategory:
    """Récupère ou crée la catégorie 'legal'."""
    result = await db.execute(
        select(EditorialCategory).where(EditorialCategory.code == "legal")
    )
    category = result.scalar_one_or_none()

    if not category:
        category = EditorialCategory(
            id=str(uuid4()),
            code="legal",
            name="Pages légales",
            description="Contenus juridiques obligatoires du site",
        )
        db.add(category)
        await db.flush()
        print("  Catégorie 'legal' créée")
    else:
        print("  Catégorie 'legal' existe déjà")

    return category


async def seed_content(
    db,
    category_id: str,
    key: str,
    title: str,
    content: str,
    description: str,
) -> EditorialContent | None:
    """Crée un contenu éditorial s'il n'existe pas déjà."""
    result = await db.execute(
        select(EditorialContent).where(EditorialContent.key == key)
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"    Contenu '{key}' existe déjà")
        return None

    # Le contenu est stocké comme JSON avec title et content
    import json
    value = json.dumps({
        "title": title,
        "content": content,
    }, ensure_ascii=False)

    editorial_content = EditorialContent(
        id=str(uuid4()),
        key=key,
        value=value,
        value_type=EditorialValueType.JSON,
        category_id=category_id,
        description=description,
        admin_editable=True,
    )
    db.add(editorial_content)
    await db.flush()

    print(f"    Contenu '{key}' créé")
    return editorial_content


async def seed():
    """Insère les données de seed pour les pages légales."""
    async with async_session_maker() as db:
        # Vérifier si des contenus légaux existent déjà
        result = await db.execute(
            select(EditorialContent).where(
                EditorialContent.key.in_([c["key"] for c in LEGAL_CONTENTS])
            )
        )
        existing_contents = result.scalars().all()

        if existing_contents:
            print(f"\n  {len(existing_contents)} contenu(s) légal(aux) existe(nt) déjà.")
            response = input("Voulez-vous continuer et ajouter les contenus manquants? (o/n): ")
            if response.lower() != "o":
                print("Opération annulée.")
                return

        print("\n=== Seed des pages légales ===\n")

        # 1. Créer ou récupérer la catégorie
        print("1. Catégorie:")
        category = await get_or_create_legal_category(db)

        # 2. Créer les contenus
        print("\n2. Contenus des pages légales:")
        created_count = 0
        for content_data in LEGAL_CONTENTS:
            content = await seed_content(
                db,
                category_id=category.id,
                key=content_data["key"],
                title=content_data["title"],
                content=content_data["content"],
                description=content_data["description"],
            )
            if content:
                created_count += 1

        await db.commit()

        # Résumé
        print("\n" + "=" * 50)
        print(f"  {created_count} contenu(s) créé(s)")
        print(f"  Catégorie: {category.code} ({category.name})")
        print("=" * 50)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SEED - PAGES LÉGALES (EDITORIAL)")
    print("=" * 60)
    asyncio.run(seed())
    print("\n  Seed terminé avec succès!\n")
