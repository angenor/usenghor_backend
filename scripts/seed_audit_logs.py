#!/usr/bin/env python3
"""
Seed script : Logs d'audit
==========================
Crée des données de simulation pour les logs d'audit.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_audit_logs.py
"""

import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.identity import AuditLog


# =============================================================================
# Données de simulation
# =============================================================================

# Utilisateurs fictifs (simulés)
MOCK_USERS = [
    {"id": str(uuid4()), "name": "Marie Dupont", "email": "marie.dupont@usenghor.org"},
    {"id": str(uuid4()), "name": "Ahmed Hassan", "email": "ahmed.hassan@usenghor.org"},
    {"id": str(uuid4()), "name": "Fatou Diallo", "email": "fatou.diallo@usenghor.org"},
    {"id": str(uuid4()), "name": "Jean-Pierre Kouadio", "email": "jp.kouadio@usenghor.org"},
    {"id": str(uuid4()), "name": "Sophie Martin", "email": "sophie.martin@usenghor.org"},
    {"id": str(uuid4()), "name": "Amadou Bah", "email": "amadou.bah@usenghor.org"},
]

# Adresses IP réalistes
IP_ADDRESSES = [
    "192.168.1.45",
    "10.0.0.128",
    "172.16.0.55",
    "41.202.219.73",    # Égypte
    "196.46.210.15",    # Sénégal
    "154.126.48.200",   # Côte d'Ivoire
    "105.235.120.89",   # Cameroun
]

# User agents réalistes
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]


def random_datetime(days_back: int = 30) -> datetime:
    """Génère une date aléatoire dans les N derniers jours."""
    now = datetime.now(timezone.utc)
    random_seconds = random.randint(0, days_back * 24 * 60 * 60)
    return now - timedelta(seconds=random_seconds)


async def seed():
    """Insère les données de seed pour les logs d'audit."""
    async with async_session_maker() as db:
        # ================================================================
        # 1. Vérifier si des logs d'audit existent déjà
        # ================================================================
        existing_logs = (
            await db.execute(select(AuditLog).limit(1))
        ).scalar_one_or_none()

        if existing_logs:
            print("[SKIP] Des logs d'audit existent déjà. Seed ignoré.")
            return

        # ================================================================
        # 2. Créer les logs d'audit
        # ================================================================
        print("[INFO] Création des logs d'audit...")

        logs_data = []

        # --- Connexions et déconnexions ---
        for _ in range(8):
            user = random.choice(MOCK_USERS)
            created_at = random_datetime(30)

            # Connexion
            logs_data.append({
                "user_id": user["id"],
                "action": "login",
                "table_name": None,
                "record_id": None,
                "old_values": None,
                "new_values": None,
                "ip_address": random.choice(IP_ADDRESSES),
                "user_agent": random.choice(USER_AGENTS),
                "created_at": created_at,
            })

            # Déconnexion (quelques heures après)
            if random.random() > 0.3:
                logs_data.append({
                    "user_id": user["id"],
                    "action": "logout",
                    "table_name": None,
                    "record_id": None,
                    "old_values": None,
                    "new_values": None,
                    "ip_address": random.choice(IP_ADDRESSES),
                    "user_agent": random.choice(USER_AGENTS),
                    "created_at": created_at + timedelta(hours=random.randint(1, 8)),
                })

        # --- Création d'actualités ---
        for i in range(5):
            user = random.choice(MOCK_USERS)
            record_id = str(uuid4())
            logs_data.append({
                "user_id": user["id"],
                "action": "create",
                "table_name": "news",
                "record_id": record_id,
                "old_values": None,
                "new_values": {
                    "id": record_id,
                    "title": f"Nouvelle actualité #{i+1}",
                    "slug": f"nouvelle-actualite-{i+1}",
                    "status": "draft",
                    "author_external_id": user["id"],
                },
                "ip_address": random.choice(IP_ADDRESSES),
                "user_agent": random.choice(USER_AGENTS),
                "created_at": random_datetime(25),
            })

        # --- Modification d'actualités ---
        for _ in range(4):
            user = random.choice(MOCK_USERS)
            record_id = str(uuid4())
            logs_data.append({
                "user_id": user["id"],
                "action": "update",
                "table_name": "news",
                "record_id": record_id,
                "old_values": {
                    "title": "Ancien titre",
                    "status": "draft",
                },
                "new_values": {
                    "title": "Nouveau titre mis à jour",
                    "status": "published",
                },
                "ip_address": random.choice(IP_ADDRESSES),
                "user_agent": random.choice(USER_AGENTS),
                "created_at": random_datetime(20),
            })

        # --- Création d'événements ---
        for i in range(3):
            user = random.choice(MOCK_USERS)
            record_id = str(uuid4())
            logs_data.append({
                "user_id": user["id"],
                "action": "create",
                "table_name": "events",
                "record_id": record_id,
                "old_values": None,
                "new_values": {
                    "id": record_id,
                    "title": f"Conférence internationale #{i+1}",
                    "slug": f"conference-internationale-{i+1}",
                    "type": "conference",
                    "city": "Alexandrie",
                    "status": "published",
                },
                "ip_address": random.choice(IP_ADDRESSES),
                "user_agent": random.choice(USER_AGENTS),
                "created_at": random_datetime(15),
            })

        # --- Modification de formations ---
        for _ in range(3):
            user = random.choice(MOCK_USERS)
            record_id = str(uuid4())
            logs_data.append({
                "user_id": user["id"],
                "action": "update",
                "table_name": "programs",
                "record_id": record_id,
                "old_values": {
                    "credits": 60,
                    "duration_months": 12,
                },
                "new_values": {
                    "credits": 90,
                    "duration_months": 18,
                },
                "ip_address": random.choice(IP_ADDRESSES),
                "user_agent": random.choice(USER_AGENTS),
                "created_at": random_datetime(18),
            })

        # --- Création de partenariats ---
        for i in range(2):
            user = random.choice(MOCK_USERS)
            record_id = str(uuid4())
            logs_data.append({
                "user_id": user["id"],
                "action": "create",
                "table_name": "partners",
                "record_id": record_id,
                "old_values": None,
                "new_values": {
                    "id": record_id,
                    "name": f"Université Partenaire {i+1}",
                    "type": "university",
                    "country": "France",
                },
                "ip_address": random.choice(IP_ADDRESSES),
                "user_agent": random.choice(USER_AGENTS),
                "created_at": random_datetime(12),
            })

        # --- Suppression d'actualités ---
        for _ in range(2):
            user = random.choice(MOCK_USERS)
            record_id = str(uuid4())
            logs_data.append({
                "user_id": user["id"],
                "action": "delete",
                "table_name": "news",
                "record_id": record_id,
                "old_values": {
                    "id": record_id,
                    "title": "Actualité supprimée",
                    "slug": "actualite-supprimee",
                    "status": "draft",
                },
                "new_values": None,
                "ip_address": random.choice(IP_ADDRESSES),
                "user_agent": random.choice(USER_AGENTS),
                "created_at": random_datetime(10),
            })

        # --- Création de candidatures ---
        for i in range(4):
            user = random.choice(MOCK_USERS)
            record_id = str(uuid4())
            logs_data.append({
                "user_id": user["id"],
                "action": "create",
                "table_name": "applications",
                "record_id": record_id,
                "old_values": None,
                "new_values": {
                    "id": record_id,
                    "applicant_name": f"Candidat {i+1}",
                    "program": "Master en Administration",
                    "status": "submitted",
                },
                "ip_address": random.choice(IP_ADDRESSES),
                "user_agent": random.choice(USER_AGENTS),
                "created_at": random_datetime(8),
            })

        # --- Modification de rôles utilisateurs ---
        user = random.choice(MOCK_USERS)
        logs_data.append({
            "user_id": user["id"],
            "action": "update",
            "table_name": "users",
            "record_id": str(uuid4()),
            "old_values": {
                "role": "editor",
            },
            "new_values": {
                "role": "admin",
            },
            "ip_address": random.choice(IP_ADDRESSES),
            "user_agent": random.choice(USER_AGENTS),
            "created_at": random_datetime(5),
        })

        # --- Création de fichiers média ---
        for i in range(3):
            user = random.choice(MOCK_USERS)
            record_id = str(uuid4())
            logs_data.append({
                "user_id": user["id"],
                "action": "create",
                "table_name": "media_files",
                "record_id": record_id,
                "old_values": None,
                "new_values": {
                    "id": record_id,
                    "filename": f"document_{i+1}.pdf",
                    "mime_type": "application/pdf",
                    "size_bytes": random.randint(100000, 5000000),
                },
                "ip_address": random.choice(IP_ADDRESSES),
                "user_agent": random.choice(USER_AGENTS),
                "created_at": random_datetime(7),
            })

        # --- Modification de campus ---
        user = random.choice(MOCK_USERS)
        logs_data.append({
            "user_id": user["id"],
            "action": "update",
            "table_name": "campuses",
            "record_id": str(uuid4()),
            "old_values": {
                "name": "Campus Principal",
                "address": "1 Rue des Sciences",
            },
            "new_values": {
                "name": "Campus Principal - Alexandrie",
                "address": "1 Place Ahmed Orabi",
            },
            "ip_address": random.choice(IP_ADDRESSES),
            "user_agent": random.choice(USER_AGENTS),
            "created_at": random_datetime(3),
        })

        # --- Création de projets ---
        for i in range(2):
            user = random.choice(MOCK_USERS)
            record_id = str(uuid4())
            logs_data.append({
                "user_id": user["id"],
                "action": "create",
                "table_name": "projects",
                "record_id": record_id,
                "old_values": None,
                "new_values": {
                    "id": record_id,
                    "title": f"Projet de recherche #{i+1}",
                    "status": "active",
                    "budget": random.randint(50000, 200000),
                },
                "ip_address": random.choice(IP_ADDRESSES),
                "user_agent": random.choice(USER_AGENTS),
                "created_at": random_datetime(6),
            })

        # ================================================================
        # 3. Insérer les logs dans la base de données
        # ================================================================
        created_logs = []
        for data in logs_data:
            log = AuditLog(
                id=str(uuid4()),
                **data,
            )
            db.add(log)
            created_logs.append(log)

        await db.commit()

        # ================================================================
        # Résumé
        # ================================================================
        action_counts = {}
        for log in created_logs:
            action_counts[log.action] = action_counts.get(log.action, 0) + 1

        print()
        print("=" * 50)
        print("Seed logs d'audit terminé avec succès !")
        print("=" * 50)
        print(f"  Total créés   : {len(created_logs)}")
        for action, count in sorted(action_counts.items()):
            print(f"  - {action.capitalize():12} : {count}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
