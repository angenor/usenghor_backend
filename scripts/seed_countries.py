#!/usr/bin/env python3
"""
Seed script : Pays (Countries)
==============================
Crée les données de référence pour les pays africains francophones.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_countries.py
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.core import Country


# Liste des pays africains francophones et partenaires
COUNTRIES_DATA = [
    # Afrique de l'Ouest francophone
    ("SN", "SEN", "Sénégal", "Senegal", "+221"),
    ("ML", "MLI", "Mali", "Mali", "+223"),
    ("CI", "CIV", "Côte d'Ivoire", "Ivory Coast", "+225"),
    ("BF", "BFA", "Burkina Faso", "Burkina Faso", "+226"),
    ("GN", "GIN", "Guinée", "Guinea", "+224"),
    ("TG", "TGO", "Togo", "Togo", "+228"),
    ("BJ", "BEN", "Bénin", "Benin", "+229"),
    ("NE", "NER", "Niger", "Niger", "+227"),
    ("MR", "MRT", "Mauritanie", "Mauritania", "+222"),

    # Afrique Centrale francophone
    ("GA", "GAB", "Gabon", "Gabon", "+241"),
    ("CM", "CMR", "Cameroun", "Cameroon", "+237"),
    ("CD", "COD", "République Démocratique du Congo", "Democratic Republic of Congo", "+243"),
    ("CG", "COG", "République du Congo", "Republic of Congo", "+242"),
    ("CF", "CAF", "République Centrafricaine", "Central African Republic", "+236"),
    ("TD", "TCD", "Tchad", "Chad", "+235"),
    ("GQ", "GNQ", "Guinée Équatoriale", "Equatorial Guinea", "+240"),

    # Afrique du Nord francophone
    ("MA", "MAR", "Maroc", "Morocco", "+212"),
    ("DZ", "DZA", "Algérie", "Algeria", "+213"),
    ("TN", "TUN", "Tunisie", "Tunisia", "+216"),

    # Îles et autres
    ("MG", "MDG", "Madagascar", "Madagascar", "+261"),
    ("MU", "MUS", "Maurice", "Mauritius", "+230"),
    ("SC", "SYC", "Seychelles", "Seychelles", "+248"),
    ("KM", "COM", "Comores", "Comoros", "+269"),
    ("DJ", "DJI", "Djibouti", "Djibouti", "+253"),
    ("RW", "RWA", "Rwanda", "Rwanda", "+250"),
    ("BI", "BDI", "Burundi", "Burundi", "+257"),

    # Afrique anglophone partenaire
    ("GH", "GHA", "Ghana", "Ghana", "+233"),
    ("NG", "NGA", "Nigéria", "Nigeria", "+234"),
    ("KE", "KEN", "Kenya", "Kenya", "+254"),
    ("ZA", "ZAF", "Afrique du Sud", "South Africa", "+27"),
    ("ET", "ETH", "Éthiopie", "Ethiopia", "+251"),

    # Afrique lusophone partenaire
    ("CV", "CPV", "Cap-Vert", "Cape Verde", "+238"),
    ("GW", "GNB", "Guinée-Bissau", "Guinea-Bissau", "+245"),
    ("ST", "STP", "São Tomé-et-Príncipe", "Sao Tome and Principe", "+239"),
    ("AO", "AGO", "Angola", "Angola", "+244"),
    ("MZ", "MOZ", "Mozambique", "Mozambique", "+258"),

    # Pays hôte
    ("EG", "EGY", "Égypte", "Egypt", "+20"),

    # France (partenaire principal)
    ("FR", "FRA", "France", "France", "+33"),
]


async def seed():
    """Insère les données de seed pour les pays."""
    async with async_session_maker() as db:
        # Vérifier si des pays existent déjà
        existing = (await db.execute(select(Country).limit(1))).scalar_one_or_none()

        if existing:
            print("[SKIP] Des pays existent déjà. Seed ignoré.")
            return

        # Créer les pays
        countries_created = []
        for iso2, iso3, name_fr, name_en, phone_code in COUNTRIES_DATA:
            country = Country(
                id=str(uuid4()),
                iso_code=iso2,
                iso_code3=iso3,
                name_fr=name_fr,
                name_en=name_en,
                phone_code=phone_code,
                active=True,
            )
            db.add(country)
            countries_created.append(country)

        await db.commit()

        print()
        print("=" * 50)
        print("Seed des pays terminé avec succès !")
        print("=" * 50)
        print(f"  Pays créés : {len(countries_created)}")
        print()
        print("  Exemples :")
        for c in countries_created[:5]:
            print(f"    - {c.iso_code}: {c.name_fr}")
        print("    ...")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
