#!/usr/bin/env python3
"""
Seed script : Editorial (Chiffres clés)
=======================================
Crée les données de simulation pour les contenus éditoriaux (chiffres clés).

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_editorial.py
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
    EditorialContentHistory,
    EditorialValueType,
)


# Données des catégories
CATEGORIES_DATA = [
    {
        "code": "key_figures",
        "name": "Chiffres clés",
        "description": "Statistiques principales affichées sur le site",
    },
    {
        "code": "rates",
        "name": "Taux et pourcentages",
        "description": "Taux de réussite, d'insertion, de satisfaction, etc.",
    },
    {
        "code": "history",
        "name": "Historique",
        "description": "Données historiques de l'université",
    },
    {
        "code": "contact",
        "name": "Contact",
        "description": "Informations de contact générales",
    },
    {
        "code": "social",
        "name": "Réseaux sociaux",
        "description": "Liens vers les réseaux sociaux",
    },
]


# Données des contenus éditoriaux (chiffres clés)
CONTENTS_DATA = [
    # === CHIFFRES CLÉS PRINCIPAUX ===
    {
        "key": "graduates_count",
        "value": "5200",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "key_figures",
        "year": 2024,
        "description": "Nombre total de diplômés depuis la création",
        "admin_editable": True,
    },
    {
        "key": "countries_count",
        "value": "54",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "key_figures",
        "year": None,
        "description": "Nombre de pays africains représentés",
        "admin_editable": True,
    },
    {
        "key": "programs_count",
        "value": "12",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "key_figures",
        "year": 2024,
        "description": "Nombre de formations proposées",
        "admin_editable": True,
    },
    {
        "key": "partners_count",
        "value": "150",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "key_figures",
        "year": 2024,
        "description": "Nombre de partenaires internationaux",
        "admin_editable": True,
    },
    {
        "key": "faculty_count",
        "value": "85",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "key_figures",
        "year": 2024,
        "description": "Nombre d'enseignants et chercheurs",
        "admin_editable": True,
    },
    {
        "key": "library_books",
        "value": "25000",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "key_figures",
        "year": 2024,
        "description": "Nombre d'ouvrages en bibliothèque",
        "admin_editable": True,
    },
    {
        "key": "campus_area",
        "value": "15000",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "key_figures",
        "year": None,
        "description": "Surface du campus en m²",
        "admin_editable": True,
    },
    {
        "key": "current_students",
        "value": "450",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "key_figures",
        "year": 2024,
        "description": "Nombre d'étudiants actuellement inscrits",
        "admin_editable": True,
    },
    # === TAUX ET POURCENTAGES ===
    {
        "key": "success_rate",
        "value": "92",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "rates",
        "year": 2024,
        "description": "Taux de réussite aux examens (%)",
        "admin_editable": True,
    },
    {
        "key": "employment_rate",
        "value": "87",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "rates",
        "year": 2024,
        "description": "Taux d'insertion professionnelle à 6 mois (%)",
        "admin_editable": True,
    },
    {
        "key": "satisfaction_rate",
        "value": "94",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "rates",
        "year": 2024,
        "description": "Taux de satisfaction des étudiants (%)",
        "admin_editable": True,
    },
    {
        "key": "women_ratio",
        "value": "42",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "rates",
        "year": 2024,
        "description": "Proportion de femmes parmi les étudiants (%)",
        "admin_editable": True,
    },
    # === HISTORIQUE ===
    {
        "key": "foundation_year",
        "value": "1990",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "history",
        "year": None,
        "description": "Année de fondation de l'université",
        "admin_editable": False,
    },
    {
        "key": "years_existence",
        "value": "35",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "history",
        "year": 2025,
        "description": "Années d'existence de l'université (depuis 1990)",
        "admin_editable": True,
    },
    {
        "key": "first_promotion_year",
        "value": "1992",
        "value_type": EditorialValueType.NUMBER,
        "category_code": "history",
        "year": None,
        "description": "Année de la première promotion diplômée",
        "admin_editable": False,
    },
    # === CONTACT ===
    {
        "key": "contact_email",
        "value": "info@usenghor.org",
        "value_type": EditorialValueType.TEXT,
        "category_code": "contact",
        "year": None,
        "description": "Adresse email principale de contact",
        "admin_editable": True,
    },
    {
        "key": "contact_phone",
        "value": "+20 3 487 1374",
        "value_type": EditorialValueType.TEXT,
        "category_code": "contact",
        "year": None,
        "description": "Numéro de téléphone principal",
        "admin_editable": True,
    },
    {
        "key": "contact_address",
        "value": "1 Place Ahmed Orabi, El Mancheya, 21111 Alexandrie, Égypte",
        "value_type": EditorialValueType.TEXT,
        "category_code": "contact",
        "year": None,
        "description": "Adresse postale du siège",
        "admin_editable": True,
    },
    # === RÉSEAUX SOCIAUX ===
    {
        "key": "social_facebook",
        "value": "https://www.facebook.com/UniversiteSenghor",
        "value_type": EditorialValueType.TEXT,
        "category_code": "social",
        "year": None,
        "description": "Lien vers la page Facebook",
        "admin_editable": True,
    },
    {
        "key": "social_twitter",
        "value": "https://twitter.com/usabordeaux",
        "value_type": EditorialValueType.TEXT,
        "category_code": "social",
        "year": None,
        "description": "Lien vers le compte X (Twitter)",
        "admin_editable": True,
    },
    {
        "key": "social_linkedin",
        "value": "https://www.linkedin.com/school/universite-senghor/",
        "value_type": EditorialValueType.TEXT,
        "category_code": "social",
        "year": None,
        "description": "Lien vers la page LinkedIn",
        "admin_editable": True,
    },
    {
        "key": "social_youtube",
        "value": "https://www.youtube.com/channel/UCuniversitesenghor",
        "value_type": EditorialValueType.TEXT,
        "category_code": "social",
        "year": None,
        "description": "Lien vers la chaîne YouTube",
        "admin_editable": True,
    },
]


# Historique simulé pour quelques contenus
HISTORY_DATA = [
    # Historique pour graduates_count
    {
        "content_key": "graduates_count",
        "old_value": "5000",
        "new_value": "5200",
    },
    {
        "content_key": "graduates_count",
        "old_value": "4800",
        "new_value": "5000",
    },
    # Historique pour success_rate
    {
        "content_key": "success_rate",
        "old_value": "90",
        "new_value": "92",
    },
    # Historique pour employment_rate
    {
        "content_key": "employment_rate",
        "old_value": "85",
        "new_value": "87",
    },
    # Historique pour partners_count
    {
        "content_key": "partners_count",
        "old_value": "140",
        "new_value": "150",
    },
    {
        "content_key": "partners_count",
        "old_value": "130",
        "new_value": "140",
    },
]


async def seed():
    """Insère les données de seed pour les contenus éditoriaux."""
    async with async_session_maker() as db:
        # Vérifier si des catégories existent déjà
        existing = (
            await db.execute(select(EditorialCategory).limit(1))
        ).scalar_one_or_none()

        if existing:
            print("[SKIP] Des catégories éditorielles existent déjà. Seed ignoré.")
            print("       Pour réinitialiser, supprimez les données existantes.")
            return

        # Créer les catégories
        categories_map = {}
        categories_created = []

        print("\n[INFO] Création des catégories éditorielles...")
        for cat_data in CATEGORIES_DATA:
            category = EditorialCategory(
                id=str(uuid4()),
                code=cat_data["code"],
                name=cat_data["name"],
                description=cat_data.get("description"),
            )
            db.add(category)
            categories_map[cat_data["code"]] = category
            categories_created.append(category)

        await db.flush()
        print(f"[OK] {len(categories_created)} catégories créées")

        # Créer les contenus
        contents_map = {}
        contents_created = []

        print("\n[INFO] Création des contenus éditoriaux (chiffres clés)...")
        for content_data in CONTENTS_DATA:
            category = categories_map.get(content_data.get("category_code"))

            content = EditorialContent(
                id=str(uuid4()),
                key=content_data["key"],
                value=content_data["value"],
                value_type=content_data["value_type"],
                category_id=category.id if category else None,
                year=content_data.get("year"),
                description=content_data.get("description"),
                admin_editable=content_data.get("admin_editable", True),
            )
            db.add(content)
            contents_map[content_data["key"]] = content
            contents_created.append(content)

        await db.flush()
        print(f"[OK] {len(contents_created)} contenus créés")

        # Créer l'historique
        history_created = []

        print("\n[INFO] Création de l'historique des modifications...")
        for hist_data in HISTORY_DATA:
            content = contents_map.get(hist_data["content_key"])
            if not content:
                continue

            history = EditorialContentHistory(
                id=str(uuid4()),
                content_id=content.id,
                old_value=hist_data["old_value"],
                new_value=hist_data["new_value"],
                modified_by_external_id=None,
            )
            db.add(history)
            history_created.append(history)

        await db.flush()
        print(f"[OK] {len(history_created)} entrées d'historique créées")

        await db.commit()

        # Afficher le résumé
        print()
        print("=" * 60)
        print("[SUCCESS] Seed des contenus éditoriaux terminé !")
        print("=" * 60)
        print(f"  Catégories créées : {len(categories_created)}")
        for cat in categories_created:
            count = sum(1 for c in contents_created if c.category_id == cat.id)
            print(f"    - {cat.code}: {cat.name} ({count} contenus)")

        print()
        print(f"  Contenus créés : {len(contents_created)}")
        print()

        # Grouper par catégorie
        by_type = {}
        for c in contents_created:
            vt = c.value_type.value
            by_type[vt] = by_type.get(vt, 0) + 1

        print("  Par type de valeur :")
        for vt, count in sorted(by_type.items()):
            print(f"    - {vt}: {count}")

        print()
        print(f"  Entrées d'historique : {len(history_created)}")
        print()
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
