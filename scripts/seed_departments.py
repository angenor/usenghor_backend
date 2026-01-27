#!/usr/bin/env python3
"""
Seed script : Départements (Departments)
========================================
Crée les données de simulation pour les départements de l'Université Senghor.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_departments.py
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.organization import Department, Service


# Départements de l'Université Senghor
# Note: icon_external_id et cover_image_external_id sont des UUID référençant le service MEDIA
# Pour l'instant, on les laisse à None car pas de médias associés
DEPARTMENTS_DATA = [
    {
        "code": "DEP-CUL",
        "name": "Culture",
        "description": "Département des arts, du patrimoine et des industries culturelles",
        "mission": """Le département Culture forme des cadres capables de gérer, promouvoir et
développer le patrimoine culturel africain dans ses dimensions matérielles et immatérielles.
Il contribue à la valorisation des identités culturelles africaines et à leur rayonnement international.""",
        "active": True,
        "services": [
            ("Patrimoine", "Gestion et valorisation du patrimoine culturel"),
            ("Industries créatives", "Accompagnement des industries culturelles et créatives"),
        ],
    },
    {
        "code": "DEP-ENV",
        "name": "Environnement",
        "description": "Département de l'environnement et du développement durable",
        "mission": """Le département Environnement forme des spécialistes de la gestion durable
des ressources naturelles et de l'adaptation au changement climatique.
Il accompagne les politiques de transition écologique sur le continent africain.""",
        "active": True,
        "services": [
            ("Ressources naturelles", "Gestion des ressources naturelles et biodiversité"),
            ("Changement climatique", "Adaptation et atténuation du changement climatique"),
        ],
    },
    {
        "code": "DEP-ADM",
        "name": "Administration et Gestion",
        "description": "Département de l'administration publique et de la gestion des organisations",
        "mission": """Le département Administration et Gestion forme des hauts fonctionnaires
et managers capables de moderniser les administrations publiques africaines
et d'améliorer la qualité des services publics.""",
        "active": True,
        "services": [
            ("Management public", "Formation en management des organisations publiques"),
            ("Gouvernance locale", "Accompagnement de la décentralisation"),
            ("Ressources humaines", "Gestion des ressources humaines du secteur public"),
        ],
    },
    {
        "code": "DEP-SAN",
        "name": "Santé",
        "description": "Département de la santé publique et de la nutrition",
        "mission": """Le département Santé forme des cadres de la santé publique
capables de concevoir et mettre en œuvre des politiques de santé adaptées
aux contextes africains et aux enjeux sanitaires contemporains.""",
        "active": True,
        "services": [
            ("Santé publique", "Formation en politiques de santé publique"),
            ("Nutrition", "Programmes de nutrition et sécurité alimentaire"),
        ],
    },
    {
        "code": "DEP-EDU",
        "name": "Éducation",
        "description": "Département des sciences de l'éducation et de la formation",
        "mission": """Le département Éducation forme des experts en politiques éducatives,
ingénierie pédagogique et formation professionnelle pour accompagner
le développement des systèmes éducatifs africains.""",
        "active": True,
        "services": [
            ("Ingénierie pédagogique", "Conception de programmes de formation"),
            ("Politiques éducatives", "Analyse et évaluation des systèmes éducatifs"),
        ],
    },
    {
        "code": "DEP-JUR",
        "name": "Droit et Gouvernance",
        "description": "Département du droit, des institutions et de la gouvernance",
        "mission": """Le département Droit et Gouvernance forme des juristes et spécialistes
de la gouvernance capables d'accompagner les réformes institutionnelles
et de renforcer l'État de droit en Afrique.""",
        "active": True,
        "services": [],
    },
    {
        "code": "DEP-INT",
        "name": "Relations Internationales",
        "description": "Département des relations internationales et de la coopération",
        "mission": """Le département Relations Internationales forme des diplomates
et experts de la coopération internationale pour renforcer le positionnement
de l'Afrique sur la scène mondiale.""",
        "active": False,  # Département en cours de création
        "services": [],
    },
]


async def seed():
    """Insère les données de seed pour les départements."""
    async with async_session_maker() as db:
        # Vérifier si des départements existent déjà
        existing = (await db.execute(select(Department).limit(1))).scalar_one_or_none()

        if existing:
            print("[SKIP] Des départements existent déjà. Seed ignoré.")
            return

        # Créer les départements
        departments_created = []
        services_count = 0

        for order, data in enumerate(DEPARTMENTS_DATA, start=1):
            # Créer le département
            # Note: icon_external_id et cover_image_external_id restent à None
            # car ce sont des UUID référençant le service MEDIA
            department = Department(
                id=str(uuid4()),
                code=data["code"],
                name=data["name"],
                description=data["description"],
                mission=data["mission"],
                active=data["active"],
                display_order=order,
            )
            db.add(department)
            await db.flush()
            departments_created.append(department)

            # Ajouter les services
            for service_order, (name, description) in enumerate(data.get("services", []), start=1):
                service = Service(
                    id=str(uuid4()),
                    name=name,
                    description=description,
                    department_id=department.id,
                    active=True,
                    display_order=service_order,
                )
                db.add(service)
                services_count += 1

        await db.commit()

        print()
        print("=" * 50)
        print("Seed des départements terminé avec succès !")
        print("=" * 50)
        print(f"  Départements créés : {len(departments_created)}")
        print(f"  Services           : {services_count}")
        print()
        print("  Départements :")
        for d in departments_created:
            status = "✓" if d.active else "○"
            print(f"    {status} [{d.code}] {d.name}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
