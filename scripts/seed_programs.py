#!/usr/bin/env python3
"""
Seed script : Programmes (Programs)
===================================
Crée les données de simulation pour les programmes de formation
de l'Université Senghor.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_programs.py
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.academic import (
    Program,
    ProgramCareerOpportunity,
    ProgramCourse,
    ProgramSemester,
    ProgramSkill,
    ProgramType,
)
from app.models.base import PublicationStatus


# Programmes de l'Université Senghor
PROGRAMS_DATA = [
    {
        "code": "MDEV",
        "title": "Master en Développement",
        "subtitle": "Gestion du développement durable et gouvernance",
        "slug": "master-developpement",
        "description": """Le Master en Développement forme des cadres africains capables de concevoir,
piloter et évaluer des politiques et projets de développement durable.
Cette formation pluridisciplinaire combine économie, gestion, gouvernance et développement territorial.""",
        "type": ProgramType.MASTER,
        "duration_months": 24,
        "credits": 120,
        "degree_awarded": "Master en Développement",
        "required_degree": "Bac+4 minimum (Maîtrise ou équivalent)",
        "status": PublicationStatus.PUBLISHED,
        "skills": [
            ("Gestion de projet de développement", "Capacité à concevoir, planifier et piloter des projets de développement"),
            ("Analyse des politiques publiques", "Évaluation et conception de politiques de développement"),
            ("Leadership et management", "Compétences en gestion d'équipes et d'organisations"),
        ],
        "careers": [
            ("Chargé de programme", "Conception et suivi de programmes de développement"),
            ("Consultant en développement", "Expertise et conseil auprès d'organisations internationales"),
            ("Directeur de projet", "Pilotage de projets de développement à grande échelle"),
        ],
        "semesters": [
            ("Semestre 1", 30, [
                ("DEV101", "Économie du développement", 6),
                ("DEV102", "Gestion de projet", 6),
                ("DEV103", "Gouvernance et institutions", 6),
                ("DEV104", "Méthodologie de recherche", 6),
                ("DEV105", "Statistiques appliquées", 6),
            ]),
            ("Semestre 2", 30, [
                ("DEV201", "Développement territorial", 6),
                ("DEV202", "Financement du développement", 6),
                ("DEV203", "Évaluation de projets", 6),
                ("DEV204", "Droit du développement", 6),
                ("DEV205", "Communication institutionnelle", 6),
            ]),
        ],
    },
    {
        "code": "MGPC",
        "title": "Master en Gestion du Patrimoine Culturel",
        "subtitle": "Conservation et valorisation du patrimoine africain",
        "slug": "master-patrimoine-culturel",
        "description": """Le Master en Gestion du Patrimoine Culturel forme des spécialistes de la conservation,
de la valorisation et de la médiation du patrimoine culturel africain.
Il aborde les dimensions matérielles et immatérielles du patrimoine.""",
        "type": ProgramType.MASTER,
        "duration_months": 24,
        "credits": 120,
        "degree_awarded": "Master en Gestion du Patrimoine Culturel",
        "required_degree": "Bac+4 minimum en sciences humaines, histoire de l'art ou équivalent",
        "status": PublicationStatus.PUBLISHED,
        "skills": [
            ("Conservation du patrimoine", "Techniques de préservation et restauration"),
            ("Médiation culturelle", "Communication et valorisation auprès des publics"),
            ("Gestion de sites patrimoniaux", "Administration et développement de sites culturels"),
        ],
        "careers": [
            ("Conservateur de musée", "Direction et gestion de collections muséales"),
            ("Gestionnaire de site patrimonial", "Administration de sites classés"),
            ("Consultant en patrimoine", "Expertise pour organisations et collectivités"),
        ],
        "semesters": [
            ("Semestre 1", 30, [
                ("PAT101", "Histoire du patrimoine africain", 6),
                ("PAT102", "Muséologie et muséographie", 6),
                ("PAT103", "Conservation préventive", 6),
                ("PAT104", "Droit du patrimoine", 6),
                ("PAT105", "Anthropologie culturelle", 6),
            ]),
        ],
    },
    {
        "code": "MADP",
        "title": "Master en Administration Publique",
        "subtitle": "Gouvernance et management public",
        "slug": "master-administration-publique",
        "description": """Le Master en Administration Publique forme des hauts fonctionnaires et cadres
du secteur public capables de moderniser l'administration et d'améliorer
la qualité des services publics en Afrique.""",
        "type": ProgramType.MASTER,
        "duration_months": 24,
        "credits": 120,
        "degree_awarded": "Master en Administration Publique",
        "required_degree": "Bac+4 minimum, expérience dans le secteur public souhaitée",
        "status": PublicationStatus.PUBLISHED,
        "skills": [
            ("Management public", "Gestion et réforme des organisations publiques"),
            ("Finances publiques", "Gestion budgétaire et contrôle de gestion"),
            ("Gouvernance locale", "Décentralisation et développement territorial"),
        ],
        "careers": [
            ("Haut fonctionnaire", "Direction de services publics"),
            ("Secrétaire général", "Administration de collectivités"),
            ("Expert en réforme administrative", "Modernisation de l'État"),
        ],
        "semesters": [
            ("Semestre 1", 30, [
                ("ADM101", "Théorie de l'administration publique", 6),
                ("ADM102", "Management des organisations publiques", 6),
                ("ADM103", "Finances publiques", 6),
                ("ADM104", "Droit administratif", 6),
                ("ADM105", "Politiques publiques", 6),
            ]),
        ],
    },
    {
        "code": "MENV",
        "title": "Master en Environnement",
        "subtitle": "Gestion durable des ressources naturelles",
        "slug": "master-environnement",
        "description": """Le Master en Environnement forme des experts en gestion durable des ressources
naturelles et en politique environnementale. Il aborde les enjeux climatiques,
la biodiversité et le développement durable en contexte africain.""",
        "type": ProgramType.MASTER,
        "duration_months": 24,
        "credits": 120,
        "degree_awarded": "Master en Environnement",
        "required_degree": "Bac+4 minimum en sciences, géographie ou équivalent",
        "status": PublicationStatus.PUBLISHED,
        "skills": [
            ("Gestion des ressources naturelles", "Exploitation durable et conservation"),
            ("Évaluation environnementale", "Études d'impact et audits environnementaux"),
            ("Politique climatique", "Adaptation et atténuation du changement climatique"),
        ],
        "careers": [
            ("Expert environnement", "Conseil en politique environnementale"),
            ("Chargé de mission RSE", "Responsabilité sociétale des entreprises"),
            ("Gestionnaire d'aires protégées", "Conservation de la biodiversité"),
        ],
        "semesters": [],
    },
    {
        "code": "DUSENGHOR",
        "title": "Diplôme Universitaire Senghor",
        "subtitle": "Formation continue pour cadres",
        "slug": "diplome-universitaire-senghor",
        "description": """Le Diplôme Universitaire Senghor est une formation courte destinée aux cadres
en activité souhaitant renforcer leurs compétences en management et développement.""",
        "type": ProgramType.UNIVERSITY_DIPLOMA,
        "duration_months": 6,
        "credits": 30,
        "degree_awarded": "Diplôme Universitaire Senghor",
        "required_degree": "Bac+3 minimum avec expérience professionnelle",
        "status": PublicationStatus.PUBLISHED,
        "skills": [
            ("Management opérationnel", "Gestion d'équipes et de projets"),
            ("Communication professionnelle", "Techniques de communication efficace"),
        ],
        "careers": [
            ("Manager", "Encadrement d'équipes"),
            ("Chef de projet", "Pilotage de projets"),
        ],
        "semesters": [],
    },
    {
        "code": "CERTGOUV",
        "title": "Certificat en Gouvernance",
        "subtitle": "Formation certifiante en gouvernance",
        "slug": "certificat-gouvernance",
        "description": """Formation certifiante courte en gouvernance et transparence institutionnelle.""",
        "type": ProgramType.CERTIFICATE,
        "duration_months": 3,
        "credits": 15,
        "degree_awarded": "Certificat en Gouvernance",
        "required_degree": "Bac+2 minimum",
        "status": PublicationStatus.DRAFT,
        "skills": [],
        "careers": [],
        "semesters": [],
    },
]


async def seed():
    """Insère les données de seed pour les programmes."""
    async with async_session_maker() as db:
        # Vérifier si des programmes existent déjà
        existing = (await db.execute(select(Program).limit(1))).scalar_one_or_none()

        if existing:
            print("[SKIP] Des programmes existent déjà. Seed ignoré.")
            return

        # Créer les programmes
        programs_created = []
        skills_count = 0
        careers_count = 0
        semesters_count = 0
        courses_count = 0

        for order, data in enumerate(PROGRAMS_DATA, start=1):
            # Créer le programme
            program = Program(
                id=str(uuid4()),
                code=data["code"],
                title=data["title"],
                subtitle=data["subtitle"],
                slug=data["slug"],
                description=data["description"],
                type=data["type"],
                duration_months=data["duration_months"],
                credits=data["credits"],
                degree_awarded=data["degree_awarded"],
                required_degree=data["required_degree"],
                status=data["status"],
                display_order=order,
            )
            db.add(program)
            await db.flush()
            programs_created.append(program)

            # Ajouter les compétences
            for skill_order, (title, description) in enumerate(data.get("skills", []), start=1):
                skill = ProgramSkill(
                    id=str(uuid4()),
                    program_id=program.id,
                    title=title,
                    description=description,
                    display_order=skill_order,
                )
                db.add(skill)
                skills_count += 1

            # Ajouter les débouchés
            for career_order, (title, description) in enumerate(data.get("careers", []), start=1):
                career = ProgramCareerOpportunity(
                    id=str(uuid4()),
                    program_id=program.id,
                    title=title,
                    description=description,
                    display_order=career_order,
                )
                db.add(career)
                careers_count += 1

            # Ajouter les semestres et cours
            for sem_order, (sem_title, sem_credits, courses) in enumerate(data.get("semesters", []), start=1):
                semester = ProgramSemester(
                    id=str(uuid4()),
                    program_id=program.id,
                    number=sem_order,
                    title=sem_title,
                    credits=sem_credits,
                    display_order=sem_order,
                )
                db.add(semester)
                await db.flush()
                semesters_count += 1

                for course_order, (code, title, credits) in enumerate(courses, start=1):
                    course = ProgramCourse(
                        id=str(uuid4()),
                        semester_id=semester.id,
                        code=code,
                        title=title,
                        credits=credits,
                        display_order=course_order,
                    )
                    db.add(course)
                    courses_count += 1

        await db.commit()

        print()
        print("=" * 50)
        print("Seed des programmes terminé avec succès !")
        print("=" * 50)
        print(f"  Programmes créés : {len(programs_created)}")
        print(f"  Compétences      : {skills_count}")
        print(f"  Débouchés        : {careers_count}")
        print(f"  Semestres        : {semesters_count}")
        print(f"  Cours            : {courses_count}")
        print()
        print("  Programmes :")
        for p in programs_created:
            print(f"    - [{p.code}] {p.title}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
