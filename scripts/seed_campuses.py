#!/usr/bin/env python3
"""
Seed script : Campus
====================
Crée les données de simulation pour les campus (siège et externalisés).

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_campuses.py

Prérequis:
  - Le script seed_countries.py doit avoir été exécuté au préalable
"""

import asyncio
import sys
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.campus import Campus
from app.models.core import Country


# Données des campus
CAMPUSES_DATA = [
    {
        "code": "ALX",
        "name": "Siège - Campus d'Alexandrie",
        "description": "Le siège de l'Université Senghor situé à Alexandrie, Égypte. Campus principal accueillant les formations de master et les services administratifs centraux.",
        "country_iso": "EG",
        "city": "Alexandrie",
        "address": "1 Place Ahmed Orabi, El Mancheya",
        "postal_code": "21111",
        "email": "info@usenghor.org",
        "phone": "+20 3 487 1374",
        "latitude": Decimal("31.200921"),
        "longitude": Decimal("29.918739"),
        "is_headquarters": True,
    },
    {
        "code": "ABJ",
        "name": "Campus d'Abidjan",
        "description": "Campus externalisé en Côte d'Ivoire, hébergé au sein de l'Université Félix Houphouët-Boigny. Offre des formations en développement durable et gestion de projets.",
        "country_iso": "CI",
        "city": "Abidjan",
        "address": "Université Félix Houphouët-Boigny, Cocody",
        "email": "abidjan@usenghor.org",
        "latitude": Decimal("5.345317"),
        "longitude": Decimal("-4.024429"),
        "is_headquarters": False,
    },
    {
        "code": "DKR",
        "name": "Campus de Dakar",
        "description": "Campus externalisé au Sénégal, en partenariat avec l'Université Cheikh Anta Diop. Spécialisé dans les formations en santé publique et nutrition.",
        "country_iso": "SN",
        "city": "Dakar",
        "address": "Université Cheikh Anta Diop, Campus de Fann",
        "email": "dakar@usenghor.org",
        "latitude": Decimal("14.692061"),
        "longitude": Decimal("-17.459305"),
        "is_headquarters": False,
    },
    {
        "code": "YAO",
        "name": "Campus de Yaoundé",
        "description": "Campus externalisé au Cameroun, hébergé à l'Université de Yaoundé II. Propose des formations en administration et gestion des entreprises.",
        "country_iso": "CM",
        "city": "Yaoundé",
        "address": "Université de Yaoundé II, Soa",
        "email": "yaounde@usenghor.org",
        "latitude": Decimal("3.870124"),
        "longitude": Decimal("11.518634"),
        "is_headquarters": False,
    },
    {
        "code": "LBV",
        "name": "Campus de Libreville",
        "description": "Campus externalisé au Gabon, en collaboration avec l'Université Omar Bongo. Spécialisé dans les formations en environnement et développement durable.",
        "country_iso": "GA",
        "city": "Libreville",
        "address": "Université Omar Bongo, Quartier Louis",
        "email": "libreville@usenghor.org",
        "latitude": Decimal("0.390503"),
        "longitude": Decimal("9.454419"),
        "is_headquarters": False,
    },
    {
        "code": "TNR",
        "name": "Campus d'Antananarivo",
        "description": "Campus externalisé à Madagascar, en partenariat avec l'Université d'Antananarivo. Offre des formations en tourisme et patrimoine culturel.",
        "country_iso": "MG",
        "city": "Antananarivo",
        "address": "Université d'Antananarivo, Campus d'Ankatso",
        "email": "antananarivo@usenghor.org",
        "latitude": Decimal("-18.910610"),
        "longitude": Decimal("47.525673"),
        "is_headquarters": False,
    },
    {
        "code": "RBA",
        "name": "Campus de Rabat",
        "description": "Campus externalisé au Maroc, hébergé à l'Université Mohammed V. Spécialisé dans les formations en gouvernance et affaires internationales.",
        "country_iso": "MA",
        "city": "Rabat",
        "address": "Université Mohammed V, Agdal",
        "email": "rabat@usenghor.org",
        "latitude": Decimal("33.984400"),
        "longitude": Decimal("-6.864300"),
        "is_headquarters": False,
    },
]


async def get_country_id_by_iso(db, iso_code: str) -> str | None:
    """Récupère l'ID d'un pays par son code ISO."""
    result = await db.execute(
        select(Country).where(Country.iso_code == iso_code)
    )
    country = result.scalar_one_or_none()
    return country.id if country else None


async def seed():
    """Insère les données de seed pour les campus."""
    async with async_session_maker() as db:
        # Vérifier si des campus existent déjà
        existing = (await db.execute(select(Campus).limit(1))).scalar_one_or_none()

        if existing:
            print("[SKIP] Des campus existent déjà. Seed ignoré.")
            print("       Pour réinitialiser, supprimez les données existantes.")
            return

        # Vérifier que les pays existent
        countries_check = (await db.execute(select(Country).limit(1))).scalar_one_or_none()
        if not countries_check:
            print("[ERREUR] Aucun pays trouvé dans la base de données.")
            print("         Veuillez d'abord exécuter: python scripts/seed_countries.py")
            return

        # Créer les campus
        campuses_created = []
        for campus_data in CAMPUSES_DATA:
            # Récupérer l'ID du pays
            country_id = await get_country_id_by_iso(db, campus_data["country_iso"])
            if not country_id:
                print(f"[WARN] Pays non trouvé: {campus_data['country_iso']} - Campus ignoré: {campus_data['name']}")
                continue

            campus = Campus(
                id=str(uuid4()),
                code=campus_data["code"],
                name=campus_data["name"],
                description=campus_data.get("description"),
                country_external_id=country_id,
                city=campus_data.get("city"),
                address=campus_data.get("address"),
                postal_code=campus_data.get("postal_code"),
                email=campus_data.get("email"),
                phone=campus_data.get("phone"),
                latitude=campus_data.get("latitude"),
                longitude=campus_data.get("longitude"),
                is_headquarters=campus_data.get("is_headquarters", False),
                active=True,
            )
            db.add(campus)
            campuses_created.append(campus)

        await db.commit()

        print()
        print("=" * 60)
        print("Seed des campus terminé avec succès !")
        print("=" * 60)
        print(f"  Campus créés : {len(campuses_created)}")
        print()
        print("  Liste des campus :")
        for c in campuses_created:
            hq = " [SIÈGE]" if c.is_headquarters else ""
            print(f"    - {c.code}: {c.name}{hq}")
        print()
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
