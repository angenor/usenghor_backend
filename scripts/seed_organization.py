#!/usr/bin/env python3
"""
Seed script : Organisation
==========================
Crée les données de simulation pour les départements, services,
objectifs, réalisations et projets.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_organization.py
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


async def seed():
    """Insère les données de seed pour l'organisation."""
    async with async_session_maker() as db:
        # ================================================================
        # 1. Vérifier si des départements existent déjà
        # ================================================================
        existing_dept = (
            await db.execute(select(Department).limit(1))
        ).scalar_one_or_none()

        if existing_dept:
            print("[SKIP] Des départements existent déjà. Seed ignoré.")
            return

        # ================================================================
        # 2. Créer les départements
        # ================================================================
        departments_data = {
            "rectorat": {
                "id": str(uuid4()),
                "code": "DEP-RECT",
                "name": "Rectorat",
                "description": "Direction générale de l'Université et services rattachés.",
                "display_order": 1,
                "active": True,
            },
            "academique": {
                "id": str(uuid4()),
                "code": "DEP-ACAD",
                "name": "Services académiques",
                "description": "Services liés à l'enseignement, la recherche et la documentation.",
                "display_order": 2,
                "active": True,
            },
            "administratif": {
                "id": str(uuid4()),
                "code": "DEP-ADMIN",
                "name": "Services administratifs",
                "description": "Services de support et gestion administrative.",
                "display_order": 3,
                "active": True,
            },
        }

        departments = {}
        for key, data in departments_data.items():
            dept = Department(**data)
            db.add(dept)
            departments[key] = dept
            print(f"  [+] Département: {data['name']}")

        await db.flush()

        # ================================================================
        # 3. Créer les services
        # ================================================================
        services_data = [
            # === RECTORAT ===
            {
                "mock_id": "srv-cabinet",
                "department_key": "rectorat",
                "name": "Cabinet du Recteur",
                "description": "Le cabinet assure le secrétariat et la coordination des activités du Recteur.",
                "email": "cabinet@usenghor.org",
                "display_order": 1,
            },
            {
                "mock_id": "srv-communication",
                "department_key": "rectorat",
                "name": "Service Communication",
                "description": "Gestion de la communication interne et externe de l'Université.",
                "email": "communication@usenghor.org",
                "display_order": 2,
            },
            {
                "mock_id": "srv-direction-campus",
                "department_key": "rectorat",
                "name": "Direction des Campus",
                "description": "Coordination des campus externalisés et relations avec les partenaires locaux.",
                "display_order": 3,
            },
            {
                "mock_id": "srv-developpement",
                "department_key": "rectorat",
                "name": "Direction du Développement et de l'Entrepreneuriat",
                "display_order": 4,
            },
            {
                "mock_id": "srv-relations-ext",
                "department_key": "rectorat",
                "name": "Direction des Relations Extérieures",
                "display_order": 5,
            },
            {
                "mock_id": "srv-alumni",
                "department_key": "rectorat",
                "name": "Programme Alumni",
                "email": "alumni@usenghor.org",
                "display_order": 6,
            },
            # === SERVICES ACADÉMIQUES ===
            {
                "mock_id": "srv-cifip",
                "department_key": "academique",
                "name": "Centre d'Ingénierie de Formations et d'Innovation Pédagogique",
                "description": "Conception et innovation pédagogique des formations.",
                "display_order": 1,
            },
            {
                "mock_id": "srv-bibliotheque",
                "department_key": "academique",
                "name": "Bibliothèque",
                "description": "Ressources documentaires et espaces de travail pour étudiants et enseignants.",
                "email": "bibliotheque@usenghor.org",
                "display_order": 2,
            },
            {
                "mock_id": "srv-scolarite",
                "department_key": "academique",
                "name": "Service de Scolarité",
                "description": "Gestion des inscriptions, examens et diplômes.",
                "email": "scolarite@usenghor.org",
                "phone": "+20 3 xxx xxxx",
                "display_order": 3,
            },
            {
                "mock_id": "srv-informatique",
                "department_key": "academique",
                "name": "Service Informatique",
                "description": "Support technique et infrastructure numérique.",
                "email": "it@usenghor.org",
                "display_order": 4,
            },
            {
                "mock_id": "srv-audiovisuel",
                "department_key": "academique",
                "name": "Service Audiovisuel",
                "display_order": 5,
            },
            # === SERVICES ADMINISTRATIFS ===
            {
                "mock_id": "srv-comptabilite",
                "department_key": "administratif",
                "name": "Service de la Comptabilité",
                "email": "comptabilite@usenghor.org",
                "display_order": 1,
            },
            {
                "mock_id": "srv-personnel",
                "department_key": "administratif",
                "name": "Service du Personnel et des Achats",
                "email": "rh@usenghor.org",
                "display_order": 2,
            },
            {
                "mock_id": "srv-qualite",
                "department_key": "administratif",
                "name": "Service de l'Assurance Qualité et du Suivi-Évaluation",
                "display_order": 3,
            },
            {
                "mock_id": "srv-voyage",
                "department_key": "administratif",
                "name": "Bureau Voyage",
                "email": "voyage@usenghor.org",
                "display_order": 4,
            },
            {
                "mock_id": "srv-interieur",
                "department_key": "administratif",
                "name": "Service Intérieur",
                "display_order": 5,
            },
        ]

        # Mapping mock_id -> real UUID
        service_id_map = {}
        services_created = []

        for data in services_data:
            mock_id = data.pop("mock_id")
            department_key = data.pop("department_key")
            service_id = str(uuid4())
            service_id_map[mock_id] = service_id

            service = Service(
                id=service_id,
                department_id=departments[department_key].id,
                active=True,
                **data,
            )
            db.add(service)
            services_created.append(service)
            print(f"  [+] Service: {data['name']}")

        await db.flush()

        # ================================================================
        # 4. Créer les objectifs
        # ================================================================
        objectives_data = [
            # Cabinet du Recteur
            {
                "service_mock_id": "srv-cabinet",
                "title": "Assurer la coordination des activités stratégiques",
                "description": "Coordination et suivi des projets prioritaires de l'Université avec les parties prenantes.",
                "display_order": 1,
            },
            {
                "service_mock_id": "srv-cabinet",
                "title": "Renforcer les relations institutionnelles",
                "description": "Développer et maintenir les relations avec les partenaires institutionnels et académiques.",
                "display_order": 2,
            },
            # Communication
            {
                "service_mock_id": "srv-communication",
                "title": "Améliorer la visibilité de l'Université",
                "description": "Augmenter la présence médiatique et numérique de l'institution.",
                "display_order": 1,
            },
            {
                "service_mock_id": "srv-communication",
                "title": "Moderniser les outils de communication interne",
                "description": "Déployer de nouveaux canaux de communication pour le personnel et les étudiants.",
                "display_order": 2,
            },
            {
                "service_mock_id": "srv-communication",
                "title": "Développer la stratégie digitale",
                "description": "Optimiser la présence sur les réseaux sociaux et le site web.",
                "display_order": 3,
            },
            # Scolarité
            {
                "service_mock_id": "srv-scolarite",
                "title": "Digitaliser les processus d'inscription",
                "description": "Mettre en place un système d'inscription en ligne entièrement dématérialisé.",
                "display_order": 1,
            },
            {
                "service_mock_id": "srv-scolarite",
                "title": "Améliorer le suivi des étudiants",
                "description": "Développer des outils de suivi personnalisé du parcours académique.",
                "display_order": 2,
            },
            # Bibliothèque
            {
                "service_mock_id": "srv-bibliotheque",
                "title": "Enrichir le fonds documentaire numérique",
                "description": "Augmenter le catalogue de ressources numériques accessibles à distance.",
                "display_order": 1,
            },
            {
                "service_mock_id": "srv-bibliotheque",
                "title": "Créer des espaces de travail collaboratif",
                "description": "Aménager de nouveaux espaces de coworking pour les étudiants.",
                "display_order": 2,
            },
            # Relations extérieures
            {
                "service_mock_id": "srv-relations-ext",
                "title": "Développer les partenariats internationaux",
                "description": "Établir de nouvelles conventions avec des universités africaines et européennes.",
                "display_order": 1,
            },
            # CIFIP
            {
                "service_mock_id": "srv-cifip",
                "title": "Innover dans les pratiques pédagogiques",
                "description": "Expérimenter et déployer de nouvelles méthodes d'enseignement.",
                "display_order": 1,
            },
            {
                "service_mock_id": "srv-cifip",
                "title": "Former les enseignants aux outils numériques",
                "description": "Organiser des sessions de formation continue sur les technologies éducatives.",
                "display_order": 2,
            },
            # Informatique
            {
                "service_mock_id": "srv-informatique",
                "title": "Moderniser l'infrastructure réseau",
                "description": "Améliorer la couverture WiFi et la bande passante sur le campus.",
                "display_order": 1,
            },
            {
                "service_mock_id": "srv-informatique",
                "title": "Sécuriser les systèmes d'information",
                "description": "Renforcer la cybersécurité et la protection des données.",
                "display_order": 2,
            },
        ]

        objectives_created = []
        for data in objectives_data:
            service_mock_id = data.pop("service_mock_id")
            objective = ServiceObjective(
                id=str(uuid4()),
                service_id=service_id_map[service_mock_id],
                **data,
            )
            db.add(objective)
            objectives_created.append(objective)

        print(f"  [+] {len(objectives_created)} objectifs créés")
        await db.flush()

        # ================================================================
        # 5. Créer les réalisations
        # ================================================================
        achievements_data = [
            # Communication
            {
                "service_mock_id": "srv-communication",
                "title": "Refonte complète du site web institutionnel",
                "description": "Nouveau site web responsive avec une meilleure expérience utilisateur et un design moderne.",
                "type": "Innovation",
                "achievement_date": date(2024, 9, 15),
            },
            {
                "service_mock_id": "srv-communication",
                "title": "Lancement de la chaîne YouTube officielle",
                "description": "Création et animation d'une chaîne YouTube avec des contenus pédagogiques et institutionnels.",
                "type": "Digital",
                "achievement_date": date(2024, 6, 20),
            },
            {
                "service_mock_id": "srv-communication",
                "title": "Organisation du 30ème anniversaire de l'Université",
                "description": "Événement majeur célébrant les 30 ans de l'Université Senghor avec conférences et expositions.",
                "type": "Événement",
                "achievement_date": date(2024, 11, 10),
            },
            # Scolarité
            {
                "service_mock_id": "srv-scolarite",
                "title": "Déploiement du portail étudiant en ligne",
                "description": "Mise en service d'un portail permettant aux étudiants de suivre leur parcours et consulter leurs notes.",
                "type": "Digitalisation",
                "achievement_date": date(2024, 2, 1),
            },
            {
                "service_mock_id": "srv-scolarite",
                "title": "Certification ISO 9001",
                "description": "Obtention de la certification qualité pour les processus de gestion des inscriptions.",
                "type": "Certification",
                "achievement_date": date(2023, 12, 15),
            },
            # Bibliothèque
            {
                "service_mock_id": "srv-bibliotheque",
                "title": "Accès à 50 000 ressources numériques",
                "description": "Partenariat avec des éditeurs pour offrir un accès élargi aux bases de données scientifiques.",
                "type": "Partenariat",
                "achievement_date": date(2024, 3, 1),
            },
            {
                "service_mock_id": "srv-bibliotheque",
                "title": "Rénovation de l'espace de lecture",
                "description": "Modernisation de la salle de lecture principale avec nouveau mobilier et éclairage.",
                "type": "Infrastructure",
                "achievement_date": date(2024, 8, 25),
            },
            # Relations extérieures
            {
                "service_mock_id": "srv-relations-ext",
                "title": "Convention avec 10 nouvelles universités partenaires",
                "description": "Signature de conventions de coopération avec des universités en Afrique de l'Ouest.",
                "type": "Partenariat",
                "achievement_date": date(2024, 5, 15),
            },
            # CIFIP
            {
                "service_mock_id": "srv-cifip",
                "title": "Formation de 50 enseignants aux méthodes actives",
                "description": "Programme de formation intensive sur les pédagogies innovantes.",
                "type": "Formation",
                "achievement_date": date(2024, 7, 10),
            },
            {
                "service_mock_id": "srv-cifip",
                "title": "Création du studio de production e-learning",
                "description": "Mise en place d'un studio professionnel pour la création de contenus pédagogiques.",
                "type": "Infrastructure",
                "achievement_date": date(2024, 4, 20),
            },
            # Informatique
            {
                "service_mock_id": "srv-informatique",
                "title": "Couverture WiFi 100% du campus",
                "description": "Déploiement de bornes WiFi haute performance sur l'ensemble du campus.",
                "type": "Infrastructure",
                "achievement_date": date(2024, 1, 15),
            },
            # Cabinet
            {
                "service_mock_id": "srv-cabinet",
                "title": "Adoption du plan stratégique 2024-2028",
                "description": "Validation par le Conseil d'Administration du nouveau plan stratégique quinquennal.",
                "type": "Stratégie",
                "achievement_date": date(2024, 1, 20),
            },
        ]

        achievements_created = []
        for data in achievements_data:
            service_mock_id = data.pop("service_mock_id")
            achievement = ServiceAchievement(
                id=str(uuid4()),
                service_id=service_id_map[service_mock_id],
                **data,
            )
            db.add(achievement)
            achievements_created.append(achievement)

        print(f"  [+] {len(achievements_created)} réalisations créées")
        await db.flush()

        # ================================================================
        # 6. Créer les projets
        # ================================================================
        projects_data = [
            # Communication
            {
                "service_mock_id": "srv-communication",
                "title": "Refonte de l'identité visuelle",
                "description": "Modernisation du logo et de la charte graphique de l'Université.",
                "progress": 75,
                "status": ProjectStatus.ONGOING,
                "start_date": date(2024, 9, 1),
                "expected_end_date": date(2025, 3, 31),
            },
            {
                "service_mock_id": "srv-communication",
                "title": "Application mobile USenghor",
                "description": "Développement d'une application mobile pour les étudiants et le personnel.",
                "progress": 30,
                "status": ProjectStatus.ONGOING,
                "start_date": date(2024, 11, 1),
                "expected_end_date": date(2025, 6, 30),
            },
            # Scolarité
            {
                "service_mock_id": "srv-scolarite",
                "title": "Dématérialisation des diplômes",
                "description": "Mise en place de la certification numérique des diplômes avec blockchain.",
                "progress": 100,
                "status": ProjectStatus.COMPLETED,
                "start_date": date(2024, 3, 1),
                "expected_end_date": date(2024, 12, 31),
            },
            {
                "service_mock_id": "srv-scolarite",
                "title": "Système d'inscription en ligne v2",
                "description": "Amélioration du portail d'inscription avec paiement intégré.",
                "progress": 60,
                "status": ProjectStatus.ONGOING,
                "start_date": date(2024, 10, 1),
                "expected_end_date": date(2025, 4, 30),
            },
            # Bibliothèque
            {
                "service_mock_id": "srv-bibliotheque",
                "title": "Numérisation des archives",
                "description": "Numérisation et indexation des documents historiques de l'Université.",
                "progress": 45,
                "status": ProjectStatus.ONGOING,
                "start_date": date(2024, 6, 1),
                "expected_end_date": date(2025, 12, 31),
            },
            {
                "service_mock_id": "srv-bibliotheque",
                "title": "Extension des horaires d'ouverture",
                "description": "Étude et mise en place d'horaires étendus avec permanences.",
                "progress": 0,
                "status": ProjectStatus.PLANNED,
                "start_date": date(2025, 2, 1),
                "expected_end_date": date(2025, 5, 31),
            },
            # CIFIP
            {
                "service_mock_id": "srv-cifip",
                "title": "Plateforme de cours en ligne",
                "description": "Déploiement d'un LMS avec contenus interactifs.",
                "progress": 85,
                "status": ProjectStatus.ONGOING,
                "start_date": date(2024, 4, 1),
                "expected_end_date": date(2025, 2, 28),
            },
            {
                "service_mock_id": "srv-cifip",
                "title": "Programme de mentorat pédagogique",
                "description": "Mise en place d'un système de parrainage entre enseignants expérimentés et nouveaux.",
                "progress": 100,
                "status": ProjectStatus.COMPLETED,
                "start_date": date(2024, 1, 15),
                "expected_end_date": date(2024, 7, 31),
            },
            # Informatique
            {
                "service_mock_id": "srv-informatique",
                "title": "Migration vers le cloud",
                "description": "Migration des serveurs vers une infrastructure cloud hybride.",
                "progress": 50,
                "status": ProjectStatus.ONGOING,
                "start_date": date(2024, 7, 1),
                "expected_end_date": date(2025, 6, 30),
            },
            {
                "service_mock_id": "srv-informatique",
                "title": "Audit de cybersécurité",
                "description": "Audit complet et plan de remédiation des vulnérabilités.",
                "progress": 20,
                "status": ProjectStatus.SUSPENDED,
                "start_date": date(2024, 9, 1),
                "expected_end_date": date(2025, 1, 31),
            },
            # Relations extérieures
            {
                "service_mock_id": "srv-relations-ext",
                "title": "Réseau des universités francophones",
                "description": "Création d'un consortium avec 5 universités partenaires.",
                "progress": 65,
                "status": ProjectStatus.ONGOING,
                "start_date": date(2024, 5, 1),
                "expected_end_date": date(2025, 5, 31),
            },
            # Alumni
            {
                "service_mock_id": "srv-alumni",
                "title": "Plateforme de networking alumni",
                "description": "Développement d'une plateforme de mise en relation des anciens étudiants.",
                "progress": 40,
                "status": ProjectStatus.ONGOING,
                "start_date": date(2024, 8, 1),
                "expected_end_date": date(2025, 4, 30),
            },
        ]

        projects_created = []
        for data in projects_data:
            service_mock_id = data.pop("service_mock_id")
            project = ServiceProject(
                id=str(uuid4()),
                service_id=service_id_map[service_mock_id],
                **data,
            )
            db.add(project)
            projects_created.append(project)

        print(f"  [+] {len(projects_created)} projets créés")

        # ================================================================
        # Commit final
        # ================================================================
        await db.commit()

        # ================================================================
        # Résumé
        # ================================================================
        ongoing = sum(1 for p in projects_created if p.status == ProjectStatus.ONGOING)
        completed = sum(1 for p in projects_created if p.status == ProjectStatus.COMPLETED)
        planned = sum(1 for p in projects_created if p.status == ProjectStatus.PLANNED)
        suspended = sum(1 for p in projects_created if p.status == ProjectStatus.SUSPENDED)

        print()
        print("=" * 60)
        print("Seed organisation terminé avec succès !")
        print("=" * 60)
        print(f"  Départements créés  : {len(departments)}")
        print(f"  Services créés      : {len(services_created)}")
        print(f"  Objectifs créés     : {len(objectives_created)}")
        print(f"  Réalisations créées : {len(achievements_created)}")
        print(f"  Projets créés       : {len(projects_created)}")
        print(f"    - En cours        : {ongoing}")
        print(f"    - Terminés        : {completed}")
        print(f"    - Planifiés       : {planned}")
        print(f"    - Suspendus       : {suspended}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
