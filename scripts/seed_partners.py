#!/usr/bin/env python3
"""
Seed script : Partenaires (Partners)
====================================
Crée les données de simulation pour les partenaires de l'Université Senghor.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_partners.py
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.partner import Partner, PartnerType


# Partenaires de l'Université Senghor
# Note: logo_external_id et country_external_id sont des UUID référençant
# les services MEDIA et CORE respectivement
PARTNERS_DATA = [
    # Opérateurs de la Charte
    {
        "name": "Agence Universitaire de la Francophonie (AUF)",
        "description": "L'AUF est le premier réseau universitaire au monde. Elle regroupe plus de 1000 établissements d'enseignement supérieur et de recherche dans plus de 100 pays.",
        "type": PartnerType.CHARTER_OPERATOR,
        "website": "https://www.auf.org",
        "email": "contact@auf.org",
        "phone": "+33 1 44 41 18 18",
        "active": True,
    },
    {
        "name": "Organisation Internationale de la Francophonie (OIF)",
        "description": "L'OIF est une institution fondée sur le partage d'une langue, le français, et de valeurs communes. Elle compte 88 États et gouvernements.",
        "type": PartnerType.CHARTER_OPERATOR,
        "website": "https://www.francophonie.org",
        "email": "oif@francophonie.org",
        "phone": "+33 1 44 37 33 00",
        "active": True,
    },
    {
        "name": "Ministère français de l'Europe et des Affaires étrangères",
        "description": "Le ministère chargé des relations diplomatiques de la France avec les autres pays et de la politique étrangère française.",
        "type": PartnerType.CHARTER_OPERATOR,
        "website": "https://www.diplomatie.gouv.fr",
        "email": None,
        "phone": None,
        "active": True,
    },
    # Partenaires de Campus
    {
        "name": "Université Paris 1 Panthéon-Sorbonne",
        "description": "Grande université parisienne spécialisée en sciences humaines et sociales, droit, économie et gestion.",
        "type": PartnerType.CAMPUS_PARTNER,
        "website": "https://www.pantheonsorbonne.fr",
        "email": "international@univ-paris1.fr",
        "phone": "+33 1 44 07 80 00",
        "active": True,
    },
    {
        "name": "Université Cheikh Anta Diop de Dakar",
        "description": "Plus grande université du Sénégal et l'une des plus anciennes d'Afrique de l'Ouest francophone.",
        "type": PartnerType.CAMPUS_PARTNER,
        "website": "https://www.ucad.sn",
        "email": "rectorat@ucad.sn",
        "phone": "+221 33 825 05 30",
        "active": True,
    },
    {
        "name": "Université d'Alexandrie",
        "description": "Deuxième plus grande université d'Égypte, partenaire historique de l'Université Senghor.",
        "type": PartnerType.CAMPUS_PARTNER,
        "website": "https://www.alexu.edu.eg",
        "email": "info@alexu.edu.eg",
        "phone": "+20 3 591 4675",
        "active": True,
    },
    # Partenaires Académiques
    {
        "name": "Institut de Recherche pour le Développement (IRD)",
        "description": "Organisme français de recherche scientifique dédié au développement durable des pays du Sud.",
        "type": PartnerType.PROGRAM_PARTNER,
        "website": "https://www.ird.fr",
        "email": "contact@ird.fr",
        "phone": "+33 4 91 99 92 00",
        "active": True,
    },
    {
        "name": "École Nationale d'Administration (ENA)",
        "description": "Grande école française formant les hauts fonctionnaires, devenue l'Institut national du service public (INSP).",
        "type": PartnerType.PROGRAM_PARTNER,
        "website": "https://insp.gouv.fr",
        "email": None,
        "phone": None,
        "active": True,
    },
    {
        "name": "HEC Paris",
        "description": "École de commerce française de renommée mondiale, partenaire pour les programmes de management.",
        "type": PartnerType.PROGRAM_PARTNER,
        "website": "https://www.hec.edu",
        "email": "info@hec.fr",
        "phone": "+33 1 39 67 70 00",
        "active": True,
    },
    # Partenaires de Projets
    {
        "name": "Banque Africaine de Développement (BAD)",
        "description": "Institution financière multilatérale de développement œuvrant pour le progrès économique et social de l'Afrique.",
        "type": PartnerType.PROJECT_PARTNER,
        "website": "https://www.afdb.org",
        "email": "afdb@afdb.org",
        "phone": "+225 20 26 10 20",
        "active": True,
    },
    {
        "name": "UNESCO",
        "description": "Organisation des Nations Unies pour l'éducation, la science et la culture.",
        "type": PartnerType.PROJECT_PARTNER,
        "website": "https://www.unesco.org",
        "email": "info@unesco.org",
        "phone": "+33 1 45 68 10 00",
        "active": True,
    },
    {
        "name": "Programme des Nations Unies pour l'Environnement (PNUE)",
        "description": "Principale autorité mondiale en matière d'environnement au sein du système des Nations Unies.",
        "type": PartnerType.PROJECT_PARTNER,
        "website": "https://www.unep.org",
        "email": "unenvironment-info@un.org",
        "phone": "+254 20 762 1234",
        "active": True,
    },
    # Autres partenaires
    {
        "name": "Fondation pour l'Innovation Politique",
        "description": "Think tank français promouvant la recherche en sciences politiques et économiques.",
        "type": PartnerType.OTHER,
        "website": "https://www.fondapol.org",
        "email": "contact@fondapol.org",
        "phone": "+33 1 47 53 67 00",
        "active": True,
    },
    {
        "name": "Centre de Recherche pour le Développement International (CRDI)",
        "description": "Organisation canadienne finançant la recherche dans les pays en développement.",
        "type": PartnerType.OTHER,
        "website": "https://www.idrc.ca",
        "email": "info@idrc.ca",
        "phone": "+1 613 236 6163",
        "active": False,  # Partenariat en pause
    },
]


async def seed():
    """Insère les données de seed pour les partenaires."""
    async with async_session_maker() as db:
        # Vérifier si des partenaires existent déjà
        existing = (await db.execute(select(Partner).limit(1))).scalar_one_or_none()

        if existing:
            print("[SKIP] Des partenaires existent déjà. Seed ignoré.")
            return

        # Créer les partenaires
        partners_created = []
        type_counts = {}

        for order, data in enumerate(PARTNERS_DATA, start=1):
            partner = Partner(
                id=str(uuid4()),
                name=data["name"],
                description=data["description"],
                type=data["type"],
                website=data.get("website"),
                email=data.get("email"),
                phone=data.get("phone"),
                display_order=order,
                active=data["active"],
                # Explicitement None pour les UUID externes
                logo_external_id=None,
                country_external_id=None,
            )
            db.add(partner)
            partners_created.append(partner)

            # Compter par type
            type_name = data["type"].value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        await db.commit()

        # Afficher le résumé
        print()
        print("=" * 60)
        print("Seed des partenaires terminé avec succès !")
        print("=" * 60)
        print(f"  Total partenaires créés : {len(partners_created)}")
        print()
        print("  Par type :")
        for type_name, count in sorted(type_counts.items()):
            print(f"    - {type_name}: {count}")
        print()
        print("  Partenaires :")
        for p in partners_created:
            status = "✓" if p.active else "○"
            type_label = p.type.value.replace("_", " ").title()
            print(f"    {status} [{type_label[:15]:<15}] {p.name[:40]}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
