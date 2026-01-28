#!/usr/bin/env python3
"""
Seed script : Identity (Utilisateurs, Rôles, Permissions)
=========================================================
Crée les données de simulation pour le système d'identité.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_identity.py
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.security import get_password_hash
from app.database import async_session_maker
from app.models.identity import Permission, Role, RolePermission, User, UserRole


# =============================================================================
# PERMISSIONS
# =============================================================================

PERMISSIONS_DATA = [
    # Utilisateurs
    {"code": "users.view", "name_fr": "Voir les utilisateurs", "category": "users"},
    {"code": "users.create", "name_fr": "Créer des utilisateurs", "category": "users"},
    {"code": "users.edit", "name_fr": "Modifier les utilisateurs", "category": "users"},
    {"code": "users.delete", "name_fr": "Supprimer les utilisateurs", "category": "users"},
    {"code": "users.roles", "name_fr": "Gérer les rôles des utilisateurs", "category": "users"},
    # Contenu éditorial
    {"code": "editorial.view", "name_fr": "Voir le contenu éditorial", "category": "editorial"},
    {"code": "editorial.edit", "name_fr": "Modifier le contenu éditorial", "category": "editorial"},
    {"code": "editorial.delete", "name_fr": "Supprimer le contenu éditorial", "category": "editorial"},
    # Actualités
    {"code": "news.view", "name_fr": "Voir les actualités", "category": "news"},
    {"code": "news.create", "name_fr": "Créer des actualités", "category": "news"},
    {"code": "news.edit", "name_fr": "Modifier les actualités", "category": "news"},
    {"code": "news.delete", "name_fr": "Supprimer les actualités", "category": "news"},
    {"code": "news.publish", "name_fr": "Publier les actualités", "category": "news"},
    # Événements
    {"code": "events.view", "name_fr": "Voir les événements", "category": "events"},
    {"code": "events.create", "name_fr": "Créer des événements", "category": "events"},
    {"code": "events.edit", "name_fr": "Modifier les événements", "category": "events"},
    {"code": "events.delete", "name_fr": "Supprimer les événements", "category": "events"},
    {"code": "events.publish", "name_fr": "Publier les événements", "category": "events"},
    # Formations
    {"code": "programs.view", "name_fr": "Voir les formations", "category": "programs"},
    {"code": "programs.create", "name_fr": "Créer des formations", "category": "programs"},
    {"code": "programs.edit", "name_fr": "Modifier les formations", "category": "programs"},
    {"code": "programs.delete", "name_fr": "Supprimer les formations", "category": "programs"},
    # Candidatures
    {"code": "applications.view", "name_fr": "Voir les candidatures", "category": "applications"},
    {"code": "applications.evaluate", "name_fr": "Évaluer les candidatures", "category": "applications"},
    {"code": "applications.manage", "name_fr": "Gérer les candidatures", "category": "applications"},
    # Médias
    {"code": "media.view", "name_fr": "Voir les médias", "category": "media"},
    {"code": "media.upload", "name_fr": "Téléverser des médias", "category": "media"},
    {"code": "media.delete", "name_fr": "Supprimer les médias", "category": "media"},
    # Campus
    {"code": "campuses.view", "name_fr": "Voir les campus", "category": "campuses"},
    {"code": "campuses.edit", "name_fr": "Modifier les campus", "category": "campuses"},
    # Partenaires
    {"code": "partners.view", "name_fr": "Voir les partenaires", "category": "partners"},
    {"code": "partners.create", "name_fr": "Créer des partenaires", "category": "partners"},
    {"code": "partners.edit", "name_fr": "Modifier les partenaires", "category": "partners"},
    {"code": "partners.delete", "name_fr": "Supprimer les partenaires", "category": "partners"},
    # Newsletter
    {"code": "newsletter.view", "name_fr": "Voir les newsletters", "category": "newsletter"},
    {"code": "newsletter.send", "name_fr": "Envoyer des newsletters", "category": "newsletter"},
    {"code": "newsletter.manage", "name_fr": "Gérer les abonnés", "category": "newsletter"},
    # Statistiques
    {"code": "stats.view", "name_fr": "Voir les statistiques", "category": "stats"},
    {"code": "stats.export", "name_fr": "Exporter les statistiques", "category": "stats"},
    # Configuration
    {"code": "settings.view", "name_fr": "Voir les paramètres", "category": "settings"},
    {"code": "settings.edit", "name_fr": "Modifier les paramètres", "category": "settings"},
]


# =============================================================================
# RÔLES
# =============================================================================

ROLES_DATA = [
    {
        "code": "super_admin",
        "name_fr": "Super Administrateur",
        "description": "Accès complet à toutes les fonctionnalités",
        "hierarchy_level": 100,
        "permissions": ["*"],  # Toutes les permissions
    },
    {
        "code": "admin",
        "name_fr": "Administrateur",
        "description": "Administration générale du site",
        "hierarchy_level": 90,
        "permissions": [
            "users.view", "users.create", "users.edit",
            "editorial.view", "editorial.edit",
            "news.view", "news.create", "news.edit", "news.delete", "news.publish",
            "events.view", "events.create", "events.edit", "events.delete", "events.publish",
            "programs.view", "programs.create", "programs.edit",
            "applications.view", "applications.manage",
            "media.view", "media.upload", "media.delete",
            "campuses.view", "campuses.edit",
            "partners.view", "partners.create", "partners.edit", "partners.delete",
            "newsletter.view", "newsletter.send", "newsletter.manage",
            "stats.view", "stats.export",
            "settings.view",
        ],
    },
    {
        "code": "editor",
        "name_fr": "Éditeur",
        "description": "Gestion du contenu éditorial",
        "hierarchy_level": 50,
        "permissions": [
            "editorial.view", "editorial.edit",
            "news.view", "news.create", "news.edit", "news.publish",
            "events.view", "events.create", "events.edit", "events.publish",
            "media.view", "media.upload",
            "partners.view",
        ],
    },
    {
        "code": "evaluator",
        "name_fr": "Évaluateur",
        "description": "Évaluation des candidatures",
        "hierarchy_level": 40,
        "permissions": [
            "applications.view", "applications.evaluate",
            "programs.view",
        ],
    },
    {
        "code": "campus_manager",
        "name_fr": "Responsable Campus",
        "description": "Gestion d'un campus spécifique",
        "hierarchy_level": 60,
        "permissions": [
            "campuses.view", "campuses.edit",
            "events.view", "events.create", "events.edit",
            "news.view", "news.create", "news.edit",
            "media.view", "media.upload",
            "stats.view",
        ],
    },
    {
        "code": "viewer",
        "name_fr": "Lecteur",
        "description": "Accès en lecture seule",
        "hierarchy_level": 10,
        "permissions": [
            "editorial.view",
            "news.view",
            "events.view",
            "programs.view",
            "campuses.view",
            "partners.view",
            "stats.view",
        ],
    },
    {
        "code": "newsletter_manager",
        "name_fr": "Gestionnaire Newsletter",
        "description": "Gestion des newsletters et abonnés",
        "hierarchy_level": 30,
        "permissions": [
            "newsletter.view", "newsletter.send", "newsletter.manage",
            "stats.view",
        ],
    },
]


# =============================================================================
# UTILISATEURS
# =============================================================================

USERS_DATA = [
    {
        "email": "marie.dupont@usenghor.org",
        "password": "Admin123!",
        "last_name": "Dupont",
        "first_name": "Marie",
        "salutation": "Mrs",
        "birth_date": "1980-05-15",
        "phone": "+33 6 12 34 56 78",
        "phone_whatsapp": "+33 6 12 34 56 78",
        "linkedin": "https://linkedin.com/in/marie-dupont",
        "city": "Alexandrie",
        "address": "1 rue de l'Université",
        "active": True,
        "email_verified": True,
        "roles": ["super_admin"],
    },
    {
        "email": "jean.martin@usenghor.org",
        "password": "Admin123!",
        "last_name": "Martin",
        "first_name": "Jean",
        "salutation": "Mr",
        "birth_date": "1975-08-22",
        "phone": "+33 6 98 76 54 32",
        "linkedin": "https://linkedin.com/in/jean-martin",
        "city": "Paris",
        "address": "15 avenue des Champs-Élysées",
        "active": True,
        "email_verified": True,
        "roles": ["admin"],
    },
    {
        "email": "sophie.bernard@usenghor.org",
        "password": "Editor123!",
        "last_name": "Bernard",
        "first_name": "Sophie",
        "salutation": "Mrs",
        "birth_date": "1985-03-10",
        "phone": "+33 6 55 44 33 22",
        "phone_whatsapp": "+33 6 55 44 33 22",
        "city": "Alexandrie",
        "active": True,
        "email_verified": True,
        "roles": ["editor"],
    },
    {
        "email": "pierre.durand@usenghor.org",
        "password": "Eval123!",
        "last_name": "Durand",
        "first_name": "Pierre",
        "salutation": "Dr",
        "birth_date": "1970-11-05",
        "phone": "+33 6 11 22 33 44",
        "linkedin": "https://linkedin.com/in/pierre-durand",
        "city": "Lyon",
        "address": "8 place Bellecour",
        "active": True,
        "email_verified": True,
        "roles": ["evaluator"],
    },
    {
        "email": "aminata.kone@usenghor.org",
        "password": "Campus123!",
        "last_name": "Koné",
        "first_name": "Aminata",
        "salutation": "Mrs",
        "birth_date": "1988-07-20",
        "phone": "+225 07 12 34 56 78",
        "phone_whatsapp": "+225 07 12 34 56 78",
        "linkedin": "https://linkedin.com/in/aminata-kone",
        "city": "Alexandrie",
        "address": "5 rue du Nil",
        "active": True,
        "email_verified": True,
        "roles": ["campus_manager"],
    },
    {
        "email": "ibrahim.toure@usenghor.org",
        "password": "Campus123!",
        "last_name": "Touré",
        "first_name": "Ibrahim",
        "salutation": "Mr",
        "birth_date": "1982-12-01",
        "phone": "+221 77 123 45 67",
        "phone_whatsapp": "+221 77 123 45 67",
        "city": "Dakar",
        "address": "25 avenue Léopold Sédar Senghor",
        "active": True,
        "email_verified": True,
        "roles": ["campus_manager"],
    },
    {
        "email": "fatima.benali@usenghor.org",
        "password": "Viewer123!",
        "last_name": "Benali",
        "first_name": "Fatima",
        "salutation": "Mrs",
        "birth_date": "1992-04-18",
        "phone": "+212 6 61 23 45 67",
        "phone_whatsapp": "+212 6 61 23 45 67",
        "city": "Casablanca",
        "active": True,
        "email_verified": True,
        "roles": ["viewer"],
    },
    {
        "email": "ousmane.diallo@usenghor.org",
        "password": "News123!",
        "last_name": "Diallo",
        "first_name": "Ousmane",
        "salutation": "Mr",
        "birth_date": "1990-09-25",
        "phone": "+224 622 12 34 56",
        "phone_whatsapp": "+224 622 12 34 56",
        "linkedin": "https://linkedin.com/in/ousmane-diallo",
        "city": "Alexandrie",
        "address": "12 rue des Pharaons",
        "active": True,
        "email_verified": True,
        "roles": ["newsletter_manager"],
    },
    {
        "email": "claire.moreau@usenghor.org",
        "password": "Multi123!",
        "last_name": "Moreau",
        "first_name": "Claire",
        "salutation": "Mrs",
        "birth_date": "1987-01-30",
        "phone": "+33 6 77 88 99 00",
        "linkedin": "https://linkedin.com/in/claire-moreau",
        "city": "Alexandrie",
        "active": True,
        "email_verified": True,
        "roles": ["editor", "evaluator"],  # Multi-rôle
    },
    {
        "email": "kofi.mensah@usenghor.org",
        "password": "Campus123!",
        "last_name": "Mensah",
        "first_name": "Kofi",
        "salutation": "Mr",
        "birth_date": "1984-06-12",
        "phone": "+233 24 123 4567",
        "phone_whatsapp": "+233 24 123 4567",
        "city": "Abidjan",
        "address": "7 boulevard de la République",
        "active": True,
        "email_verified": True,
        "roles": ["campus_manager"],
    },
    {
        "email": "youssef.elfassi@usenghor.org",
        "password": "Admin123!",
        "last_name": "El Fassi",
        "first_name": "Youssef",
        "salutation": "Dr",
        "birth_date": "1978-02-14",
        "phone": "+20 10 1234 5678",
        "phone_whatsapp": "+20 10 1234 5678",
        "linkedin": "https://linkedin.com/in/youssef-elfassi",
        "city": "Alexandrie",
        "address": "30 corniche",
        "active": True,
        "email_verified": True,
        "roles": ["admin"],
    },
    {
        "email": "amara.traore@usenghor.org",
        "password": "Viewer123!",
        "last_name": "Traoré",
        "first_name": "Amara",
        "salutation": "Mr",
        "birth_date": "1995-10-08",
        "phone": "+223 76 12 34 56",
        "phone_whatsapp": "+223 76 12 34 56",
        "city": "Bamako",
        "active": True,
        "email_verified": False,  # Email non vérifié
        "roles": ["viewer"],
    },
    {
        "email": "nadia.koffi@usenghor.org",
        "password": "Multi123!",
        "last_name": "Koffi",
        "first_name": "Nadia",
        "salutation": "Mrs",
        "birth_date": "1993-08-03",
        "phone": "+229 97 12 34 56",
        "phone_whatsapp": "+229 97 12 34 56",
        "linkedin": "https://linkedin.com/in/nadia-koffi",
        "city": "Cotonou",
        "address": "45 avenue de la Marina",
        "active": True,
        "email_verified": True,
        "roles": ["newsletter_manager", "viewer"],
    },
    {
        "email": "hassan.diop@usenghor.org",
        "password": "Eval123!",
        "last_name": "Diop",
        "first_name": "Hassan",
        "salutation": "Pr",
        "birth_date": "1965-04-22",
        "phone": "+221 77 987 65 43",
        "linkedin": "https://linkedin.com/in/hassan-diop",
        "city": "Saint-Louis",
        "address": "100 rue Blaise Diagne",
        "active": True,
        "email_verified": True,
        "roles": ["evaluator"],
    },
    {
        "email": "paul.ndong@usenghor.org",
        "password": "Inactive123!",
        "last_name": "Ndong",
        "first_name": "Paul",
        "salutation": "Mr",
        "birth_date": "1991-12-25",
        "phone": "+241 07 12 34 56",
        "city": "Libreville",
        "active": False,  # Compte inactif
        "email_verified": False,
        "roles": ["viewer"],
    },
]


async def seed():
    """Insère les données de seed pour le système d'identité."""
    async with async_session_maker() as db:
        # Vérifier si des permissions existent déjà
        existing = (await db.execute(select(Permission).limit(1))).scalar_one_or_none()

        if existing:
            print("[SKIP] Des permissions existent déjà. Seed ignoré.")
            print("       Pour réinitialiser, supprimez les données existantes.")
            return

        # =====================================================================
        # PERMISSIONS
        # =====================================================================
        print("\n[INFO] Création des permissions...")
        permissions_map = {}
        permissions_created = []

        for perm_data in PERMISSIONS_DATA:
            permission = Permission(
                id=str(uuid4()),
                code=perm_data["code"],
                name_fr=perm_data["name_fr"],
                description=perm_data.get("description"),
                category=perm_data.get("category"),
            )
            db.add(permission)
            permissions_map[perm_data["code"]] = permission
            permissions_created.append(permission)

        await db.flush()
        print(f"[OK] {len(permissions_created)} permissions créées")

        # =====================================================================
        # RÔLES
        # =====================================================================
        print("\n[INFO] Création des rôles...")
        roles_map = {}
        roles_created = []

        for role_data in ROLES_DATA:
            role = Role(
                id=str(uuid4()),
                code=role_data["code"],
                name_fr=role_data["name_fr"],
                description=role_data.get("description"),
                hierarchy_level=role_data.get("hierarchy_level", 0),
                active=True,
            )
            db.add(role)
            roles_map[role_data["code"]] = role
            roles_created.append(role)

        await db.flush()
        print(f"[OK] {len(roles_created)} rôles créés")

        # =====================================================================
        # PERMISSIONS DES RÔLES
        # =====================================================================
        print("\n[INFO] Attribution des permissions aux rôles...")
        role_perms_created = 0

        for role_data in ROLES_DATA:
            role = roles_map[role_data["code"]]
            perm_codes = role_data.get("permissions", [])

            # Si "*" → toutes les permissions
            if "*" in perm_codes:
                perm_codes = list(permissions_map.keys())

            for perm_code in perm_codes:
                if perm_code in permissions_map:
                    role_perm = RolePermission(
                        role_id=role.id,
                        permission_id=permissions_map[perm_code].id,
                    )
                    db.add(role_perm)
                    role_perms_created += 1

        await db.flush()
        print(f"[OK] {role_perms_created} attributions role-permission créées")

        # =====================================================================
        # UTILISATEURS
        # =====================================================================
        print("\n[INFO] Création des utilisateurs...")
        users_map = {}
        users_created = []

        for user_data in USERS_DATA:
            user = User(
                id=str(uuid4()),
                email=user_data["email"],
                password_hash=get_password_hash(user_data["password"]),
                last_name=user_data["last_name"],
                first_name=user_data["first_name"],
                salutation=user_data.get("salutation"),
                birth_date=user_data.get("birth_date"),
                phone=user_data.get("phone"),
                phone_whatsapp=user_data.get("phone_whatsapp"),
                linkedin=user_data.get("linkedin"),
                city=user_data.get("city"),
                address=user_data.get("address"),
                active=user_data.get("active", True),
                email_verified=user_data.get("email_verified", False),
            )
            db.add(user)
            users_map[user_data["email"]] = user
            users_created.append(user)

        await db.flush()
        print(f"[OK] {len(users_created)} utilisateurs créés")

        # =====================================================================
        # RÔLES DES UTILISATEURS
        # =====================================================================
        print("\n[INFO] Attribution des rôles aux utilisateurs...")
        user_roles_created = 0
        super_admin = next((u for u in users_created if u.email == "marie.dupont@usenghor.org"), None)

        for user_data in USERS_DATA:
            user = users_map[user_data["email"]]
            role_codes = user_data.get("roles", [])

            for role_code in role_codes:
                if role_code in roles_map:
                    user_role = UserRole(
                        user_id=user.id,
                        role_id=roles_map[role_code].id,
                        assigned_by=super_admin.id if super_admin and user != super_admin else None,
                    )
                    db.add(user_role)
                    user_roles_created += 1

        await db.flush()
        print(f"[OK] {user_roles_created} attributions user-role créées")

        await db.commit()

        # =====================================================================
        # RÉSUMÉ
        # =====================================================================
        print()
        print("=" * 60)
        print("[SUCCESS] Seed du système d'identité terminé !")
        print("=" * 60)
        print(f"  Permissions créées : {len(permissions_created)}")
        print()
        print("  Catégories de permissions :")
        categories = {}
        for p in permissions_created:
            cat = p.category or "autres"
            categories[cat] = categories.get(cat, 0) + 1
        for cat, count in sorted(categories.items()):
            print(f"    - {cat}: {count}")
        print()
        print(f"  Rôles créés : {len(roles_created)}")
        for role in roles_created:
            print(f"    - {role.code}: {role.name_fr} (niveau {role.hierarchy_level})")
        print()
        print(f"  Utilisateurs créés : {len(users_created)}")
        active_count = sum(1 for u in users_created if u.active)
        verified_count = sum(1 for u in users_created if u.email_verified)
        print(f"    - Actifs: {active_count}")
        print(f"    - Emails vérifiés: {verified_count}")
        print()
        print("  Comptes de test :")
        print("    - Super Admin: marie.dupont@usenghor.org / Admin123!")
        print("    - Admin: jean.martin@usenghor.org / Admin123!")
        print("    - Éditeur: sophie.bernard@usenghor.org / Editor123!")
        print("    - Évaluateur: pierre.durand@usenghor.org / Eval123!")
        print()
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
