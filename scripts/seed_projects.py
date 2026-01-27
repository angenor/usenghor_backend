#!/usr/bin/env python3
"""
Seed script : Projets Institutionnels
=====================================
Crée des données de simulation pour les projets.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_projects.py
"""

import asyncio
import json
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.base import PublicationStatus
from app.models.organization import ProjectStatus
from app.models.project import (
    Project,
    ProjectCall,
    ProjectCallStatus,
    ProjectCallType,
    ProjectCategory,
    ProjectCategoryLink,
)


async def seed():
    """Insère les données de seed pour les projets."""
    async with async_session_maker() as db:
        # ================================================================
        # 1. Vérifier si des projets existent déjà
        # ================================================================
        existing_projects = (
            await db.execute(select(Project).limit(1))
        ).scalar_one_or_none()

        if existing_projects:
            print("[SKIP] Des projets existent déjà. Seed ignoré.")
            return

        # ================================================================
        # 2. Créer les catégories
        # ================================================================
        categories_data = [
            {
                "name": "Développement durable",
                "slug": "developpement-durable",
                "description": "Projets liés aux objectifs de développement durable",
                "icon": "fa-leaf",
            },
            {
                "name": "Formation professionnelle",
                "slug": "formation-professionnelle",
                "description": "Programmes de formation et de renforcement des capacités",
                "icon": "fa-graduation-cap",
            },
            {
                "name": "Industries culturelles",
                "slug": "industries-culturelles",
                "description": "Projets dans le domaine culturel et créatif",
                "icon": "fa-theater-masks",
            },
            {
                "name": "Recherche",
                "slug": "recherche",
                "description": "Programmes de recherche et réseaux académiques",
                "icon": "fa-microscope",
            },
            {
                "name": "Numérique",
                "slug": "numerique",
                "description": "Transformation digitale et technologies",
                "icon": "fa-laptop-code",
            },
            {
                "name": "Gouvernance",
                "slug": "gouvernance",
                "description": "Gouvernance et administration publique",
                "icon": "fa-landmark",
            },
            {
                "name": "Santé",
                "slug": "sante",
                "description": "Projets dans le domaine de la santé",
                "icon": "fa-heartbeat",
            },
            {
                "name": "Bourses et aide",
                "slug": "bourses-aide",
                "description": "Programmes de bourses et d'aide aux étudiants",
                "icon": "fa-hand-holding-usd",
            },
        ]

        categories = []
        for cat_data in categories_data:
            category = ProjectCategory(
                id=str(uuid4()),
                **cat_data,
            )
            db.add(category)
            categories.append(category)

        await db.flush()  # Pour obtenir les IDs des catégories

        # ================================================================
        # 3. Créer les projets
        # ================================================================
        now = datetime.now(timezone.utc)
        today = date.today()

        projects_data = [
            # --- 1. Transform'Action Africa (ongoing, published, featured) ---
            {
                "title": "Transform'Action Africa",
                "slug": "transformaction-africa",
                "summary": "Parcours pédagogique pour les leaders qui conduisent des dynamiques de transformation structurelle au sein des organisations publiques africaines.",
                "description": json.dumps({
                    "blocks": [
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "<b>Transform'Action Africa</b> est un parcours pédagogique, collectif et créatif, conçu pour les leaders qui conduisent des dynamiques de transformation structurelle au sein des organisations publiques africaines, au service de la transition sociale et écologique."
                            }
                        },
                        {
                            "type": "header",
                            "data": {"text": "Notre mission", "level": 2}
                        },
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "Former les cadres publics qui transforment l'Afrique en renforçant les compétences managériales et de leadership des cadres du secteur public en Afrique francophone."
                            }
                        }
                    ]
                }),
                "cover_image_external_id": str(uuid4()),
                "start_date": date(2022, 1, 15),
                "budget": Decimal("5000000.00"),
                "currency": "EUR",
                "beneficiaries": "Cadres dirigeants des organisations publiques africaines",
                "status": ProjectStatus.ONGOING,
                "publication_status": PublicationStatus.PUBLISHED,
                "category_indices": [0, 5],  # Développement durable, Gouvernance
            },
            # --- 2. KreAfrika (ongoing, published) ---
            {
                "title": "KreAfrika",
                "slug": "kreafrika",
                "summary": "Renforcement des compétences des professionnels des Industries Culturelles et Créatives en Afrique.",
                "description": json.dumps({
                    "blocks": [
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "<b>KreAfrika</b> est un projet mis en œuvre par l'Université Senghor, le groupe médiatique TRACE et le Campus Groupe AFD, qui vise à renforcer les compétences des professionnels des Industries Culturelles et Créatives (ICC) en Afrique."
                            }
                        }
                    ]
                }),
                "cover_image_external_id": str(uuid4()),
                "start_date": date(2021, 1, 1),
                "budget": Decimal("2500000.00"),
                "currency": "EUR",
                "beneficiaries": "Professionnels des Industries Culturelles et Créatives",
                "status": ProjectStatus.ONGOING,
                "publication_status": PublicationStatus.PUBLISHED,
                "category_indices": [2],  # Industries culturelles
            },
            # --- 3. Campagne de levée de fonds (ongoing, published) ---
            {
                "title": "Campagne de levée de fonds",
                "slug": "campagne-levee-fonds",
                "summary": "Mobilisation de ressources pour soutenir les bourses d'excellence et les projets d'innovation.",
                "description": json.dumps({
                    "blocks": [
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "La campagne de levée de fonds de l'Université Senghor vise à mobiliser des ressources pour soutenir ses missions fondamentales."
                            }
                        }
                    ]
                }),
                "cover_image_external_id": str(uuid4()),
                "start_date": date(2024, 1, 1),
                "budget": Decimal("1000000.00"),
                "currency": "EUR",
                "beneficiaries": "100 boursiers/an",
                "status": ProjectStatus.ONGOING,
                "publication_status": PublicationStatus.PUBLISHED,
                "category_indices": [7],  # Bourses et aide
            },
            # --- 4. Programme de bourses d'excellence (ongoing, published) ---
            {
                "title": "Programme de bourses d'excellence",
                "slug": "bourses-excellence",
                "summary": "Bourses destinées aux étudiants les plus méritants de l'espace francophone africain.",
                "description": json.dumps({
                    "blocks": [
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "Le programme de bourses d'excellence de l'Université Senghor permet chaque année à des étudiants talentueux de poursuivre leurs études."
                            }
                        },
                        {
                            "type": "header",
                            "data": {"text": "Critères d'éligibilité", "level": 2}
                        },
                        {
                            "type": "list",
                            "data": {
                                "style": "unordered",
                                "items": [
                                    "Excellence académique",
                                    "Projet professionnel cohérent",
                                    "Engagement citoyen démontré"
                                ]
                            }
                        }
                    ]
                }),
                "cover_image_external_id": str(uuid4()),
                "start_date": date(2020, 9, 1),
                "currency": "EUR",
                "beneficiaries": "200 boursiers actuels",
                "status": ProjectStatus.ONGOING,
                "publication_status": PublicationStatus.PUBLISHED,
                "category_indices": [7],  # Bourses et aide
            },
            # --- 5. Réseau de recherche francophone (ongoing, published) ---
            {
                "title": "Réseau de recherche francophone",
                "slug": "reseau-recherche-francophone",
                "summary": "Réseau collaboratif sur les grands défis du développement en Afrique francophone.",
                "description": json.dumps({
                    "blocks": [
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "Le Réseau de recherche francophone rassemble des chercheurs de l'espace francophone autour de thématiques communes."
                            }
                        }
                    ]
                }),
                "cover_image_external_id": str(uuid4()),
                "start_date": date(2018, 1, 1),
                "currency": "EUR",
                "beneficiaries": "150 chercheurs",
                "status": ProjectStatus.ONGOING,
                "publication_status": PublicationStatus.PUBLISHED,
                "category_indices": [3],  # Recherche
            },
            # --- 6. Africa Digital Leaders (planned, published) ---
            {
                "title": "Africa Digital Leaders",
                "slug": "africa-digital-leaders",
                "summary": "Programme de formation des futurs leaders du numérique en Afrique.",
                "description": json.dumps({
                    "blocks": [
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "Africa Digital Leaders est un programme intensif de formation au leadership numérique."
                            }
                        }
                    ]
                }),
                "cover_image_external_id": str(uuid4()),
                "start_date": today + timedelta(days=180),
                "currency": "EUR",
                "beneficiaries": "50 leaders/an",
                "status": ProjectStatus.PLANNED,
                "publication_status": PublicationStatus.PUBLISHED,
                "category_indices": [4],  # Numérique
            },
            # --- 7. Santé numérique (planned, draft) ---
            {
                "title": "Santé numérique en Afrique",
                "slug": "sante-numerique-afrique",
                "summary": "Renforcement des capacités en santé numérique pour les professionnels de santé africains.",
                "cover_image_external_id": str(uuid4()),
                "start_date": today + timedelta(days=365),
                "currency": "EUR",
                "beneficiaries": "Professionnels de santé",
                "status": ProjectStatus.PLANNED,
                "publication_status": PublicationStatus.DRAFT,
                "category_indices": [6, 4],  # Santé, Numérique
            },
            # --- 8. Formation gouvernance 2023 (completed, published) ---
            {
                "title": "Formation en gouvernance publique 2023",
                "slug": "formation-gouvernance-2023",
                "summary": "Programme de formation intensive en gouvernance publique - Cohorte 2023.",
                "description": json.dumps({
                    "blocks": [
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "La cohorte 2023 du programme de formation en gouvernance publique a permis de former 45 cadres dirigeants issus de 15 pays africains."
                            }
                        }
                    ]
                }),
                "cover_image_external_id": str(uuid4()),
                "start_date": date(2023, 1, 15),
                "end_date": date(2023, 12, 15),
                "budget": Decimal("800000.00"),
                "currency": "EUR",
                "beneficiaries": "45 cadres dirigeants formés",
                "status": ProjectStatus.COMPLETED,
                "publication_status": PublicationStatus.PUBLISHED,
                "category_indices": [5, 1],  # Gouvernance, Formation professionnelle
            },
            # --- 9. Campus virtuel (suspended, draft) ---
            {
                "title": "Campus virtuel Senghor",
                "slug": "campus-virtuel-senghor",
                "summary": "Développement d'une plateforme de formation en ligne pour tous les programmes.",
                "cover_image_external_id": str(uuid4()),
                "start_date": date(2023, 6, 1),
                "currency": "EUR",
                "beneficiaries": "Étudiants et professeurs",
                "status": ProjectStatus.SUSPENDED,
                "publication_status": PublicationStatus.DRAFT,
                "category_indices": [4, 1],  # Numérique, Formation professionnelle
            },
            # --- 10. Programme Alumni Connect (ongoing, published) ---
            {
                "title": "Alumni Connect Africa",
                "slug": "alumni-connect-africa",
                "summary": "Réseau professionnel des anciens étudiants de l'Université Senghor.",
                "description": json.dumps({
                    "blocks": [
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "Alumni Connect Africa vise à créer un réseau dynamique d'anciens étudiants pour favoriser les échanges professionnels et le mentorat."
                            }
                        }
                    ]
                }),
                "cover_image_external_id": str(uuid4()),
                "start_date": date(2022, 9, 1),
                "currency": "EUR",
                "beneficiaries": "5000+ alumni",
                "status": ProjectStatus.ONGOING,
                "publication_status": PublicationStatus.PUBLISHED,
                "category_indices": [1],  # Formation professionnelle
            },
        ]

        created_projects = []
        for data in projects_data:
            category_indices = data.pop("category_indices", [])

            project = Project(
                id=str(uuid4()),
                **data,
            )
            db.add(project)
            created_projects.append((project, category_indices))

        await db.flush()  # Pour obtenir les IDs des projets

        # ================================================================
        # 4. Créer les liens projets-catégories
        # ================================================================
        for project, category_indices in created_projects:
            for idx in category_indices:
                link = ProjectCategoryLink(
                    project_id=project.id,
                    category_id=categories[idx].id,
                )
                db.add(link)

        # ================================================================
        # 5. Créer quelques appels de projets
        # ================================================================
        calls_data = [
            # Appel pour Transform'Action Africa
            {
                "project": created_projects[0][0],
                "title": "Appel à candidatures - Cohorte 2026",
                "description": "Candidature ouverte pour la nouvelle cohorte du programme Transform'Action Africa.",
                "status": ProjectCallStatus.ONGOING,
                "type": ProjectCallType.APPLICATION,
                "deadline": now + timedelta(days=90),
            },
            # Appel bourse
            {
                "project": created_projects[3][0],
                "title": "Bourses d'excellence 2026-2027",
                "description": "Appel à candidatures pour les bourses d'excellence de l'année académique 2026-2027.",
                "status": ProjectCallStatus.UPCOMING,
                "type": ProjectCallType.SCHOLARSHIP,
                "deadline": now + timedelta(days=120),
            },
            # Appel recrutement Digital Leaders
            {
                "project": created_projects[5][0],
                "title": "Recrutement formateurs - Africa Digital Leaders",
                "description": "Recherche de formateurs experts en transformation digitale.",
                "status": ProjectCallStatus.ONGOING,
                "type": ProjectCallType.RECRUITMENT,
                "deadline": now + timedelta(days=45),
            },
            # Appel clôturé
            {
                "project": created_projects[7][0],
                "title": "Candidatures Formation Gouvernance 2023",
                "description": "Appel clôturé pour la cohorte 2023.",
                "status": ProjectCallStatus.CLOSED,
                "type": ProjectCallType.TRAINING,
                "deadline": now - timedelta(days=365),
            },
        ]

        created_calls = []
        for call_data in calls_data:
            project = call_data.pop("project")
            call = ProjectCall(
                id=str(uuid4()),
                project_id=project.id,
                **call_data,
            )
            db.add(call)
            created_calls.append(call)

        await db.commit()

        # ================================================================
        # Résumé
        # ================================================================
        projects = [p[0] for p in created_projects]
        ongoing = sum(1 for p in projects if p.status == ProjectStatus.ONGOING)
        completed = sum(1 for p in projects if p.status == ProjectStatus.COMPLETED)
        planned = sum(1 for p in projects if p.status == ProjectStatus.PLANNED)
        suspended = sum(1 for p in projects if p.status == ProjectStatus.SUSPENDED)

        published = sum(1 for p in projects if p.publication_status == PublicationStatus.PUBLISHED)
        draft = sum(1 for p in projects if p.publication_status == PublicationStatus.DRAFT)

        print()
        print("=" * 60)
        print("Seed projets institutionnels terminé avec succès !")
        print("=" * 60)
        print(f"  Catégories créées : {len(categories)}")
        print(f"  Projets créés     : {len(projects)}")
        print(f"    - En cours      : {ongoing}")
        print(f"    - Terminés      : {completed}")
        print(f"    - Planifiés     : {planned}")
        print(f"    - Suspendus     : {suspended}")
        print(f"  Publication:")
        print(f"    - Publiés       : {published}")
        print(f"    - Brouillons    : {draft}")
        print(f"  Appels créés      : {len(created_calls)}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
