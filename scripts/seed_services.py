#!/usr/bin/env python3
"""
Seed script : Services et Départements
=======================================
Crée les données de simulation pour les départements et services
de l'Université Senghor.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_services.py
"""

import asyncio
import sys
from datetime import date
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.organization import (
    Department,
    ProjectStatus,
    Service,
    ServiceAchievement,
    ServiceObjective,
    ServiceProject,
)


# Départements de l'Université Senghor
DEPARTMENTS_DATA = [
    {
        "code": "RECT",
        "name": "Rectorat",
        "description": "Direction générale de l'université, pilotage stratégique et coordination des activités.",
        "mission": """Le Rectorat assure la gouvernance générale de l'Université Senghor.
Il coordonne l'ensemble des activités académiques, administratives et de recherche,
et veille à la réalisation de la mission de l'université au service du développement africain.""",
        "icon_external_id": None,
        "services": [
            {
                "name": "Cabinet du Recteur",
                "description": "Coordination des activités du Rectorat et gestion des relations institutionnelles.",
                "mission": "Assurer le bon fonctionnement de la gouvernance universitaire et la représentation de l'institution.",
                "email": "cabinet.recteur@usenghor.org",
                "phone": "+20 3 484 5650",
                "objectives": [
                    ("Coordination stratégique", "Assurer la coordination des activités stratégiques de l'université"),
                    ("Relations institutionnelles", "Développer et maintenir les partenariats institutionnels"),
                    ("Communication interne", "Faciliter la communication entre les différents services"),
                ],
                "achievements": [
                    ("Signature de partenariats", "Signature de 15 nouveaux accords de partenariat", "Partenariat", "2024-06-15"),
                    ("Réorganisation", "Mise en place d'une nouvelle organisation administrative", "Gouvernance", "2024-03-01"),
                ],
                "projects": [
                    ("Plan stratégique 2025-2030", "Élaboration du nouveau plan stratégique quinquennal", 60, "ongoing", "2024-09-01", "2025-06-30"),
                ],
            },
            {
                "name": "Service Communication",
                "description": "Gestion de la communication institutionnelle et de l'image de l'université.",
                "mission": "Promouvoir l'image de l'Université Senghor et assurer la diffusion d'informations.",
                "email": "communication@usenghor.org",
                "phone": "+20 3 484 5651",
                "objectives": [
                    ("Visibilité internationale", "Renforcer la visibilité de l'université à l'international"),
                    ("Communication digitale", "Développer la présence numérique de l'université"),
                    ("Relations presse", "Gérer les relations avec les médias"),
                ],
                "achievements": [
                    ("Refonte site web", "Refonte complète du site web institutionnel", "Digital", "2024-09-15"),
                    ("Campagne réseaux sociaux", "Lancement d'une campagne sur les réseaux sociaux", "Communication", "2024-05-01"),
                ],
                "projects": [
                    ("Nouvelle identité visuelle", "Refonte de l'identité visuelle de l'université", 75, "ongoing", "2024-03-01", "2025-01-31"),
                    ("Plateforme média", "Création d'une plateforme média interne", 30, "planned", "2025-02-01", "2025-09-30"),
                ],
            },
            {
                "name": "Direction des Campus",
                "description": "Coordination des campus externalisés et des formations délocalisées.",
                "mission": "Piloter le développement et le suivi des campus externalisés en Afrique.",
                "email": "campus@usenghor.org",
                "phone": "+20 3 484 5652",
                "objectives": [
                    ("Coordination des campus", "Assurer la coordination pédagogique entre les campus"),
                    ("Qualité des formations", "Garantir la qualité des formations délocalisées"),
                ],
                "achievements": [],
                "projects": [
                    ("Expansion Afrique de l'Ouest", "Projet d'ouverture de nouveaux campus", 20, "planned", "2025-01-01", "2026-12-31"),
                ],
            },
        ],
    },
    {
        "code": "CULT",
        "name": "Département Culture",
        "description": "Gestion du patrimoine culturel et promotion de la culture africaine.",
        "mission": """Le Département Culture forme des spécialistes de la gestion du patrimoine
et de l'action culturelle. Il contribue à la valorisation du patrimoine africain
et à la promotion des industries culturelles sur le continent.""",
        "icon_external_id": None,
        "services": [
            {
                "name": "CIFIP - Centre International de Formation en Industries du Patrimoine",
                "description": "Formation aux métiers du patrimoine et des industries culturelles.",
                "mission": "Former les futurs professionnels du patrimoine et des industries culturelles africaines.",
                "email": "cifip@usenghor.org",
                "phone": "+20 3 484 5660",
                "objectives": [
                    ("Formation professionnelle", "Offrir des formations de qualité aux professionnels du patrimoine"),
                    ("Recherche appliquée", "Développer la recherche sur le patrimoine africain"),
                    ("Coopération internationale", "Établir des partenariats avec les institutions culturelles"),
                ],
                "achievements": [
                    ("Accréditation UNESCO", "Obtention de l'accréditation UNESCO pour les formations", "Certification", "2024-01-20"),
                    ("Exposition itinérante", "Organisation d'une exposition sur le patrimoine immatériel", "Événement", "2024-04-15"),
                ],
                "projects": [
                    ("Musée numérique", "Création d'un musée numérique du patrimoine africain", 45, "ongoing", "2024-06-01", "2025-12-31"),
                    ("Base de données patrimoine", "Constitution d'une base de données patrimoniales", 80, "ongoing", "2023-09-01", "2025-03-31"),
                ],
            },
            {
                "name": "Bibliothèque Universitaire",
                "description": "Gestion des ressources documentaires et accompagnement des étudiants.",
                "mission": "Mettre à disposition des ressources documentaires de qualité pour la communauté universitaire.",
                "email": "bibliotheque@usenghor.org",
                "phone": "+20 3 484 5661",
                "objectives": [
                    ("Enrichissement des collections", "Développer les collections documentaires"),
                    ("Services numériques", "Développer l'accès aux ressources numériques"),
                    ("Formation documentaire", "Former les étudiants à la recherche documentaire"),
                ],
                "achievements": [
                    ("Numérisation des archives", "Numérisation de 5000 documents d'archives", "Innovation", "2024-07-30"),
                ],
                "projects": [
                    ("Bibliothèque numérique", "Développement d'une bibliothèque numérique accessible en ligne", 55, "ongoing", "2024-02-01", "2025-06-30"),
                ],
            },
        ],
    },
    {
        "code": "ENV",
        "name": "Département Environnement",
        "description": "Formation et recherche en gestion durable de l'environnement.",
        "mission": """Le Département Environnement forme des experts en gestion des ressources naturelles
et en politique environnementale. Il répond aux enjeux du développement durable en Afrique.""",
        "icon_external_id": None,
        "services": [
            {
                "name": "Service Recherche Environnement",
                "description": "Coordination des activités de recherche en environnement.",
                "mission": "Développer la recherche sur les enjeux environnementaux africains.",
                "email": "recherche.env@usenghor.org",
                "phone": "+20 3 484 5670",
                "objectives": [
                    ("Publications scientifiques", "Augmenter le nombre de publications de recherche"),
                    ("Partenariats recherche", "Développer les collaborations avec les centres de recherche"),
                ],
                "achievements": [
                    ("Projet climat", "Participation au projet régional sur le changement climatique", "Recherche", "2024-02-28"),
                ],
                "projects": [
                    ("Observatoire du climat", "Création d'un observatoire du changement climatique", 35, "ongoing", "2024-04-01", "2026-03-31"),
                ],
            },
        ],
    },
    {
        "code": "ADM",
        "name": "Administration Générale",
        "description": "Services administratifs et logistiques de l'université.",
        "mission": """L'Administration Générale assure le fonctionnement quotidien de l'université,
la gestion des ressources humaines, financières et matérielles.""",
        "icon_external_id": None,
        "services": [
            {
                "name": "Service Scolarité",
                "description": "Gestion des inscriptions, des parcours étudiants et des diplômes.",
                "mission": "Accompagner les étudiants tout au long de leur parcours académique.",
                "email": "scolarite@usenghor.org",
                "phone": "+20 3 484 5680",
                "objectives": [
                    ("Qualité de service", "Améliorer l'accueil et le suivi des étudiants"),
                    ("Dématérialisation", "Dématérialiser les procédures administratives"),
                    ("Suivi des diplômés", "Mettre en place un suivi des diplômés"),
                ],
                "achievements": [
                    ("Portail étudiant", "Mise en ligne du portail étudiant", "Digital", "2024-08-01"),
                    ("Certification ISO", "Obtention de la certification qualité ISO 9001", "Certification", "2024-05-15"),
                ],
                "projects": [
                    ("Application mobile", "Développement d'une application mobile pour les étudiants", 40, "ongoing", "2024-09-01", "2025-04-30"),
                ],
            },
            {
                "name": "Service Informatique",
                "description": "Gestion des systèmes d'information et du parc informatique.",
                "mission": "Assurer le bon fonctionnement des infrastructures numériques de l'université.",
                "email": "informatique@usenghor.org",
                "phone": "+20 3 484 5681",
                "objectives": [
                    ("Disponibilité des systèmes", "Garantir une disponibilité maximale des systèmes"),
                    ("Sécurité informatique", "Renforcer la cybersécurité"),
                    ("Support utilisateurs", "Améliorer le support aux utilisateurs"),
                ],
                "achievements": [
                    ("Migration cloud", "Migration des serveurs vers le cloud", "Infrastructure", "2024-03-15"),
                    ("Nouvelle salle serveur", "Mise en service de la nouvelle salle serveur", "Infrastructure", "2024-01-10"),
                ],
                "projects": [
                    ("Système de gestion intégré", "Mise en place d'un ERP universitaire", 25, "ongoing", "2024-06-01", "2026-05-31"),
                    ("Réseau Wi-Fi campus", "Extension de la couverture Wi-Fi", 90, "ongoing", "2024-01-01", "2025-01-31"),
                ],
            },
            {
                "name": "Service Comptabilité et Finances",
                "description": "Gestion comptable et financière de l'université.",
                "mission": "Assurer la bonne gestion des ressources financières et le respect des procédures.",
                "email": "comptabilite@usenghor.org",
                "phone": "+20 3 484 5682",
                "objectives": [
                    ("Transparence financière", "Garantir la transparence de la gestion financière"),
                    ("Optimisation budgétaire", "Optimiser l'utilisation des ressources"),
                ],
                "achievements": [
                    ("Audit externe", "Validation de l'audit externe sans réserves", "Gouvernance", "2024-06-30"),
                ],
                "projects": [],
            },
            {
                "name": "Service Ressources Humaines",
                "description": "Gestion du personnel et développement des compétences.",
                "mission": "Gérer les ressources humaines et accompagner le développement professionnel.",
                "email": "rh@usenghor.org",
                "phone": "+20 3 484 5683",
                "objectives": [
                    ("Gestion des carrières", "Accompagner le développement des carrières"),
                    ("Formation continue", "Développer la formation continue du personnel"),
                    ("Climat social", "Maintenir un bon climat social"),
                ],
                "achievements": [
                    ("Plan de formation", "Mise en place du nouveau plan de formation", "Formation", "2024-02-01"),
                ],
                "projects": [
                    ("SIRH", "Mise en place d'un système d'information RH", 15, "planned", "2025-03-01", "2026-02-28"),
                ],
            },
            {
                "name": "Service des Affaires Juridiques",
                "description": "Conseil juridique et gestion des contrats.",
                "mission": "Assurer la sécurité juridique des actes de l'université.",
                "email": "juridique@usenghor.org",
                "phone": "+20 3 484 5684",
                "objectives": [
                    ("Sécurité juridique", "Garantir la conformité juridique des actes"),
                    ("Conseil aux services", "Apporter un conseil juridique aux services"),
                ],
                "achievements": [],
                "projects": [],
            },
        ],
    },
]


async def seed():
    """Insère les données de seed pour les départements et services."""
    async with async_session_maker() as db:
        # Vérifier si des départements existent déjà
        existing = (await db.execute(select(Department).limit(1))).scalar_one_or_none()

        if existing:
            print("[SKIP] Des départements/services existent déjà. Seed ignoré.")
            return

        # Compteurs
        departments_created = []
        services_count = 0
        objectives_count = 0
        achievements_count = 0
        projects_count = 0

        for dept_order, dept_data in enumerate(DEPARTMENTS_DATA, start=1):
            # Créer le département
            department = Department(
                id=str(uuid4()),
                code=dept_data["code"],
                name=dept_data["name"],
                description=dept_data["description"],
                mission=dept_data["mission"],
                icon_external_id=dept_data.get("icon_external_id"),
                display_order=dept_order,
                active=True,
            )
            db.add(department)
            await db.flush()
            departments_created.append(department)

            # Créer les services du département
            for svc_order, svc_data in enumerate(dept_data.get("services", []), start=1):
                service = Service(
                    id=str(uuid4()),
                    department_id=department.id,
                    name=svc_data["name"],
                    description=svc_data.get("description"),
                    mission=svc_data.get("mission"),
                    email=svc_data.get("email"),
                    phone=svc_data.get("phone"),
                    display_order=svc_order,
                    active=True,
                )
                db.add(service)
                await db.flush()
                services_count += 1

                # Créer les objectifs du service
                for obj_order, (title, description) in enumerate(svc_data.get("objectives", []), start=1):
                    objective = ServiceObjective(
                        id=str(uuid4()),
                        service_id=service.id,
                        title=title,
                        description=description,
                        display_order=obj_order,
                    )
                    db.add(objective)
                    objectives_count += 1

                # Créer les réalisations du service
                for ach_data in svc_data.get("achievements", []):
                    title, description, ach_type, ach_date_str = ach_data
                    ach_date = date.fromisoformat(ach_date_str) if ach_date_str else None
                    achievement = ServiceAchievement(
                        id=str(uuid4()),
                        service_id=service.id,
                        title=title,
                        description=description,
                        type=ach_type,
                        achievement_date=ach_date,
                    )
                    db.add(achievement)
                    achievements_count += 1

                # Créer les projets du service
                for proj_data in svc_data.get("projects", []):
                    title, description, progress, status_str, start_str, end_str = proj_data
                    status = ProjectStatus(status_str)
                    start_date = date.fromisoformat(start_str) if start_str else None
                    expected_end = date.fromisoformat(end_str) if end_str else None
                    project = ServiceProject(
                        id=str(uuid4()),
                        service_id=service.id,
                        title=title,
                        description=description,
                        progress=progress,
                        status=status,
                        start_date=start_date,
                        expected_end_date=expected_end,
                    )
                    db.add(project)
                    projects_count += 1

        await db.commit()

        print()
        print("=" * 60)
        print("Seed des départements et services terminé avec succès !")
        print("=" * 60)
        print(f"  Départements créés : {len(departments_created)}")
        print(f"  Services           : {services_count}")
        print(f"  Objectifs          : {objectives_count}")
        print(f"  Réalisations       : {achievements_count}")
        print(f"  Projets            : {projects_count}")
        print()
        print("  Départements :")
        for d in departments_created:
            print(f"    - [{d.code}] {d.name}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
