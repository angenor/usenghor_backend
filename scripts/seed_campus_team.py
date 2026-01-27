#!/usr/bin/env python3
"""
Seed script : Équipes Campus
============================
Crée les données de simulation pour les membres des équipes campus.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_campus_team.py

Prérequis:
  - Le script seed_campuses.py doit avoir été exécuté au préalable
  - Le script seed_users.py doit avoir été exécuté au préalable (ou des utilisateurs existent)
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
from app.models.campus import Campus, CampusTeam
from app.models.identity import User


# Données des équipes par campus (code campus -> liste de membres)
# Les positions sont variées pour refléter la structure réelle
CAMPUS_TEAM_DATA = {
    "ALX": [
        {
            "position": "Recteur",
            "display_order": 1,
            "start_date": "2018-09-01",
        },
        {
            "position": "Secrétaire Général",
            "display_order": 2,
            "start_date": "2019-03-15",
        },
        {
            "position": "Vice-Recteur chargé des Affaires Académiques",
            "display_order": 3,
            "start_date": "2020-01-10",
        },
        {
            "position": "Directrice des Études",
            "display_order": 4,
            "start_date": "2021-09-01",
        },
        {
            "position": "Responsable Administratif et Financier",
            "display_order": 5,
            "start_date": "2019-06-01",
        },
    ],
    "ABJ": [
        {
            "position": "Directeur du Campus",
            "display_order": 1,
            "start_date": "2019-09-01",
        },
        {
            "position": "Coordinatrice Pédagogique",
            "display_order": 2,
            "start_date": "2020-02-15",
        },
        {
            "position": "Responsable Administratif",
            "display_order": 3,
            "start_date": "2021-01-10",
        },
    ],
    "DKR": [
        {
            "position": "Directrice du Campus",
            "display_order": 1,
            "start_date": "2017-09-01",
        },
        {
            "position": "Coordinateur des Formations",
            "display_order": 2,
            "start_date": "2019-03-01",
        },
        {
            "position": "Assistante Administrative",
            "display_order": 3,
            "start_date": "2022-09-01",
        },
    ],
    "YAO": [
        {
            "position": "Directeur du Campus",
            "display_order": 1,
            "start_date": "2020-09-01",
        },
        {
            "position": "Responsable des Partenariats",
            "display_order": 2,
            "start_date": "2021-06-15",
        },
    ],
    "LBV": [
        {
            "position": "Directeur du Campus",
            "display_order": 1,
            "start_date": "2018-02-01",
        },
        {
            "position": "Coordinatrice Pédagogique",
            "display_order": 2,
            "start_date": "2020-09-01",
        },
    ],
    "TNR": [
        {
            "position": "Directrice du Campus",
            "display_order": 1,
            "start_date": "2019-09-01",
        },
        {
            "position": "Responsable Administratif",
            "display_order": 2,
            "start_date": "2021-01-15",
        },
    ],
    "RBA": [
        {
            "position": "Directeur du Campus",
            "display_order": 1,
            "start_date": "2016-09-01",
        },
        {
            "position": "Vice-Directrice",
            "display_order": 2,
            "start_date": "2018-03-01",
        },
        {
            "position": "Coordinateur des Admissions",
            "display_order": 3,
            "start_date": "2022-02-01",
        },
    ],
}


async def get_campus_by_code(db, code: str) -> Campus | None:
    """Récupère un campus par son code."""
    result = await db.execute(select(Campus).where(Campus.code == code))
    return result.scalar_one_or_none()


async def get_available_users(db) -> list[User]:
    """Récupère les utilisateurs disponibles pour être assignés aux équipes."""
    result = await db.execute(
        select(User).where(User.active == True).order_by(User.created_at)
    )
    return list(result.scalars().all())


async def seed():
    """Insère les données de seed pour les équipes campus."""
    async with async_session_maker() as db:
        # Vérifier si des membres d'équipe existent déjà
        existing = (await db.execute(select(CampusTeam).limit(1))).scalar_one_or_none()

        if existing:
            print("[SKIP] Des membres d'équipe campus existent déjà. Seed ignoré.")
            print("       Pour réinitialiser, supprimez les données existantes.")
            return

        # Vérifier que les campus existent
        campus_check = (await db.execute(select(Campus).limit(1))).scalar_one_or_none()
        if not campus_check:
            print("[ERREUR] Aucun campus trouvé dans la base de données.")
            print("         Veuillez d'abord exécuter: python scripts/seed_campuses.py")
            return

        # Récupérer les utilisateurs disponibles
        users = await get_available_users(db)
        if len(users) < 5:
            print(f"[WARN] Seulement {len(users)} utilisateur(s) disponible(s).")
            print("       Certains membres d'équipe seront créés avec des UUIDs fictifs.")

        # Index pour distribuer les utilisateurs
        user_index = 0
        members_created = []
        campus_stats = {}

        for campus_code, members_data in CAMPUS_TEAM_DATA.items():
            campus = await get_campus_by_code(db, campus_code)
            if not campus:
                print(f"[WARN] Campus non trouvé: {campus_code} - Membres ignorés")
                continue

            campus_members = 0
            for member_data in members_data:
                # Utiliser un utilisateur existant ou générer un UUID fictif
                if user_index < len(users):
                    user_external_id = users[user_index].id
                    user_index += 1
                else:
                    # Générer un UUID fictif si pas assez d'utilisateurs
                    user_external_id = str(uuid4())

                # Parser la date de début
                start_date_str = member_data.get("start_date")
                start_date = date.fromisoformat(start_date_str) if start_date_str else None

                team_member = CampusTeam(
                    id=str(uuid4()),
                    campus_id=campus.id,
                    user_external_id=user_external_id,
                    position=member_data["position"],
                    display_order=member_data.get("display_order", 0),
                    start_date=start_date,
                    end_date=None,
                    active=True,
                )
                db.add(team_member)
                members_created.append((campus_code, team_member))
                campus_members += 1

            campus_stats[campus_code] = campus_members

        await db.commit()

        print()
        print("=" * 60)
        print("Seed des équipes campus terminé avec succès !")
        print("=" * 60)
        print(f"  Membres créés : {len(members_created)}")
        print()
        print("  Répartition par campus :")
        for code, count in campus_stats.items():
            print(f"    - {code}: {count} membre(s)")
        print()
        print("  Détail des membres :")
        for campus_code, member in members_created:
            print(f"    [{campus_code}] {member.position}")
        print()
        if user_index < len(members_created):
            print(f"  [INFO] {len(members_created) - user_index} membre(s) ont des UUIDs fictifs")
            print("         (pas assez d'utilisateurs en base)")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
