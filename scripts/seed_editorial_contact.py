#!/usr/bin/env python3
"""
Seed script : Informations de Contact (Editorial)
=================================================
Crée les données de simulation pour les informations de contact
de l'Université Senghor via le système éditorial.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_editorial_contact.py
"""

import asyncio
import json
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
# DONNÉES DE CONTACT
# =============================================================================

# Adresse principale
CONTACT_ADDRESS = {
    "street": "1 Place Ahmed Orabi",
    "postal_code": "21131",
    "city": "Alexandrie",
    "country": "Égypte",
    "latitude": 31.2001,
    "longitude": 29.9187,
}

# Numéros de téléphone
CONTACT_PHONES = {
    "main": "+20 3 484 3562",
    "secondary": "+20 3 484 3563",
    "fax": "+20 3 484 3564",
}

# Adresses email
CONTACT_EMAILS = {
    "general": "contact@usenghor.org",
    "admissions": "admissions@usenghor.org",
    "partnerships": "partenariats@usenghor.org",
    "press": "presse@usenghor.org",
}

# Horaires d'ouverture
CONTACT_HOURS = {
    "days": "Dimanche - Jeudi",
    "hours": "08h00 - 16h00",
    "timezone": "EET (UTC+2)",
    "closures": "Jours fériés égyptiens et français",
}

# Configuration du formulaire de contact
CONTACT_FORM_CONFIG = {
    "default_recipients": ["contact@usenghor.org"],
    "subjects": [
        "Demande d'information générale",
        "Admissions et inscriptions",
        "Partenariat institutionnel",
        "Partenariat entreprise",
        "Presse et médias",
        "Autre",
    ],
    "confirmation_message": "Votre message a bien été envoyé. Nous vous répondrons dans les meilleurs délais.",
}

# Contacts par département
DEPARTMENT_CONTACTS = [
    {
        "id": str(uuid4()),
        "department_name": "Service des admissions",
        "email": "admissions@usenghor.org",
        "phone": "+20 3 484 3565",
        "responsible_name": "Dr. Fatima El-Sayed",
        "order": 1,
    },
    {
        "id": str(uuid4()),
        "department_name": "Service de la scolarité",
        "email": "scolarite@usenghor.org",
        "phone": "+20 3 484 3566",
        "responsible_name": "M. Ahmed Hassan",
        "order": 2,
    },
    {
        "id": str(uuid4()),
        "department_name": "Relations internationales",
        "email": "international@usenghor.org",
        "phone": "+20 3 484 3567",
        "responsible_name": "Mme Claire Dubois",
        "order": 3,
    },
    {
        "id": str(uuid4()),
        "department_name": "Service financier",
        "email": "finances@usenghor.org",
        "phone": "+20 3 484 3568",
        "responsible_name": "M. Omar Benali",
        "order": 4,
    },
    {
        "id": str(uuid4()),
        "department_name": "Bibliothèque",
        "email": "bibliotheque@usenghor.org",
        "phone": "+20 3 484 3569",
        "responsible_name": "Mme Nadia Mansour",
        "order": 5,
    },
    {
        "id": str(uuid4()),
        "department_name": "Service informatique",
        "email": "informatique@usenghor.org",
        "phone": "+20 3 484 3570",
        "responsible_name": None,
        "order": 6,
    },
]

# Réseaux sociaux
SOCIAL_MEDIA_LINKS = {
    "facebook": "https://www.facebook.com/UniversiteSenghor",
    "twitter": "https://twitter.com/USenghor",
    "linkedin": "https://www.linkedin.com/school/universite-senghor/",
    "youtube": "https://www.youtube.com/@UniversiteSenghor",
    "instagram": None,
}

# Liste des contenus à créer
CONTACT_CONTENTS = [
    {
        "key": "contact_address",
        "value": CONTACT_ADDRESS,
        "description": "Adresse principale de l'université",
    },
    {
        "key": "contact_phones",
        "value": CONTACT_PHONES,
        "description": "Numéros de téléphone",
    },
    {
        "key": "contact_emails",
        "value": CONTACT_EMAILS,
        "description": "Adresses email de contact",
    },
    {
        "key": "contact_hours",
        "value": CONTACT_HOURS,
        "description": "Horaires d'ouverture",
    },
    {
        "key": "contact_form_config",
        "value": CONTACT_FORM_CONFIG,
        "description": "Configuration du formulaire de contact",
    },
    {
        "key": "contact_department_contacts",
        "value": DEPARTMENT_CONTACTS,
        "description": "Contacts par service/département",
    },
    {
        "key": "contact_social_media",
        "value": SOCIAL_MEDIA_LINKS,
        "description": "Liens vers les réseaux sociaux",
    },
]


# =============================================================================
# FONCTIONS DE SEED
# =============================================================================


async def get_or_create_contact_category(db) -> EditorialCategory:
    """Récupère ou crée la catégorie 'contact'."""
    result = await db.execute(
        select(EditorialCategory).where(EditorialCategory.code == "contact")
    )
    category = result.scalar_one_or_none()

    if not category:
        category = EditorialCategory(
            id=str(uuid4()),
            code="contact",
            name="Informations de contact",
            description="Coordonnées et informations de contact de l'université",
        )
        db.add(category)
        await db.flush()
        print("✓ Catégorie 'contact' créée")
    else:
        print("→ Catégorie 'contact' existe déjà")

    return category


async def seed_content(
    db,
    category_id: str,
    key: str,
    value: dict | list,
    description: str,
) -> EditorialContent | None:
    """Crée un contenu éditorial s'il n'existe pas déjà."""
    result = await db.execute(
        select(EditorialContent).where(EditorialContent.key == key)
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  → Contenu '{key}' existe déjà")
        return None

    content = EditorialContent(
        id=str(uuid4()),
        key=key,
        value=json.dumps(value, ensure_ascii=False),
        value_type=EditorialValueType.JSON,
        category_id=category_id,
        description=description,
        admin_editable=True,
    )
    db.add(content)
    await db.flush()

    print(f"  ✓ Contenu '{key}' créé")
    return content


async def seed():
    """Insère les données de seed pour les informations de contact."""
    async with async_session_maker() as db:
        # Vérifier si des contenus de contact existent déjà
        result = await db.execute(
            select(EditorialContent).where(
                EditorialContent.key.like("contact_%")
            )
        )
        existing_contents = result.scalars().all()

        if existing_contents:
            print(f"\n⚠ {len(existing_contents)} contenu(s) de contact existe(nt) déjà.")
            response = input("Voulez-vous continuer et ajouter les contenus manquants? (o/n): ")
            if response.lower() != "o":
                print("Opération annulée.")
                return

        print("\n=== Seed des informations de contact ===\n")

        # 1. Créer ou récupérer la catégorie
        category = await get_or_create_contact_category(db)

        # 2. Créer les contenus
        print("\nCréation des contenus de contact:")
        created_count = 0
        for content_data in CONTACT_CONTENTS:
            content = await seed_content(
                db,
                category_id=category.id,
                key=content_data["key"],
                value=content_data["value"],
                description=content_data["description"],
            )
            if content:
                created_count += 1

        await db.commit()

        # Résumé
        print("\n" + "=" * 50)
        print(f"✓ {created_count} contenu(s) créé(s)")
        print(f"→ Catégorie: {category.code} ({category.name})")
        print("=" * 50)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SEED - INFORMATIONS DE CONTACT (EDITORIAL)")
    print("=" * 60)
    asyncio.run(seed())
    print("\n✓ Seed terminé avec succès!\n")
