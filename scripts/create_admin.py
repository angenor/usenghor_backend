#!/usr/bin/env python3
"""
Script pour créer un utilisateur administrateur
================================================

Usage:
  python scripts/create_admin.py

Ce script crée un utilisateur admin@usenghor.org avec le rôle super_admin.
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


async def create_admin():
    """Crée l'utilisateur admin avec le rôle super_admin."""
    async with async_session_maker() as db:
        # Vérifier si l'utilisateur existe déjà
        existing_user = (
            await db.execute(
                select(User).where(User.email == "admin@usenghor.org")
            )
        ).scalar_one_or_none()

        if existing_user:
            print("[INFO] L'utilisateur admin@usenghor.org existe déjà.")
            return

        # Vérifier si le rôle super_admin existe
        super_admin_role = (
            await db.execute(
                select(Role).where(Role.code == "super_admin")
            )
        ).scalar_one_or_none()

        # Si le rôle n'existe pas, on doit d'abord créer les permissions et rôles de base
        if not super_admin_role:
            print("[INFO] Création des permissions et rôles de base...")

            # Créer les permissions de base
            permissions_data = [
                {"code": "users.view", "name_fr": "Voir les utilisateurs", "category": "users"},
                {"code": "users.create", "name_fr": "Créer des utilisateurs", "category": "users"},
                {"code": "users.edit", "name_fr": "Modifier les utilisateurs", "category": "users"},
                {"code": "users.delete", "name_fr": "Supprimer les utilisateurs", "category": "users"},
                {"code": "users.roles", "name_fr": "Gérer les rôles des utilisateurs", "category": "users"},
                {"code": "editorial.view", "name_fr": "Voir le contenu éditorial", "category": "editorial"},
                {"code": "editorial.edit", "name_fr": "Modifier le contenu éditorial", "category": "editorial"},
                {"code": "news.view", "name_fr": "Voir les actualités", "category": "news"},
                {"code": "news.create", "name_fr": "Créer des actualités", "category": "news"},
                {"code": "news.edit", "name_fr": "Modifier les actualités", "category": "news"},
                {"code": "news.delete", "name_fr": "Supprimer les actualités", "category": "news"},
                {"code": "news.publish", "name_fr": "Publier les actualités", "category": "news"},
                {"code": "events.view", "name_fr": "Voir les événements", "category": "events"},
                {"code": "events.create", "name_fr": "Créer des événements", "category": "events"},
                {"code": "events.edit", "name_fr": "Modifier les événements", "category": "events"},
                {"code": "events.delete", "name_fr": "Supprimer les événements", "category": "events"},
                {"code": "events.publish", "name_fr": "Publier les événements", "category": "events"},
                {"code": "programs.view", "name_fr": "Voir les formations", "category": "programs"},
                {"code": "programs.create", "name_fr": "Créer des formations", "category": "programs"},
                {"code": "programs.edit", "name_fr": "Modifier les formations", "category": "programs"},
                {"code": "programs.delete", "name_fr": "Supprimer les formations", "category": "programs"},
                {"code": "applications.view", "name_fr": "Voir les candidatures", "category": "applications"},
                {"code": "applications.evaluate", "name_fr": "Évaluer les candidatures", "category": "applications"},
                {"code": "applications.manage", "name_fr": "Gérer les candidatures", "category": "applications"},
                {"code": "media.view", "name_fr": "Voir les médias", "category": "media"},
                {"code": "media.upload", "name_fr": "Téléverser des médias", "category": "media"},
                {"code": "media.delete", "name_fr": "Supprimer les médias", "category": "media"},
                {"code": "campuses.view", "name_fr": "Voir les campus", "category": "campuses"},
                {"code": "campuses.edit", "name_fr": "Modifier les campus", "category": "campuses"},
                {"code": "partners.view", "name_fr": "Voir les partenaires", "category": "partners"},
                {"code": "partners.create", "name_fr": "Créer des partenaires", "category": "partners"},
                {"code": "partners.edit", "name_fr": "Modifier les partenaires", "category": "partners"},
                {"code": "partners.delete", "name_fr": "Supprimer les partenaires", "category": "partners"},
                {"code": "newsletter.view", "name_fr": "Voir les newsletters", "category": "newsletter"},
                {"code": "newsletter.send", "name_fr": "Envoyer des newsletters", "category": "newsletter"},
                {"code": "newsletter.manage", "name_fr": "Gérer les abonnés", "category": "newsletter"},
                {"code": "stats.view", "name_fr": "Voir les statistiques", "category": "stats"},
                {"code": "stats.export", "name_fr": "Exporter les statistiques", "category": "stats"},
                {"code": "settings.view", "name_fr": "Voir les paramètres", "category": "settings"},
                {"code": "settings.edit", "name_fr": "Modifier les paramètres", "category": "settings"},
            ]

            permissions_map = {}
            for perm_data in permissions_data:
                # Vérifier si la permission existe déjà
                existing_perm = (
                    await db.execute(
                        select(Permission).where(Permission.code == perm_data["code"])
                    )
                ).scalar_one_or_none()

                if existing_perm:
                    permissions_map[perm_data["code"]] = existing_perm
                else:
                    permission = Permission(
                        id=str(uuid4()),
                        code=perm_data["code"],
                        name_fr=perm_data["name_fr"],
                        category=perm_data.get("category"),
                    )
                    db.add(permission)
                    permissions_map[perm_data["code"]] = permission

            await db.flush()
            print(f"[OK] {len(permissions_map)} permissions configurées")

            # Créer le rôle super_admin
            super_admin_role = Role(
                id=str(uuid4()),
                code="super_admin",
                name_fr="Super Administrateur",
                description="Accès complet à toutes les fonctionnalités",
                hierarchy_level=100,
                active=True,
            )
            db.add(super_admin_role)
            await db.flush()

            # Attribuer toutes les permissions au super_admin
            for perm in permissions_map.values():
                role_perm = RolePermission(
                    role_id=super_admin_role.id,
                    permission_id=perm.id,
                )
                db.add(role_perm)

            await db.flush()
            print("[OK] Rôle super_admin créé avec toutes les permissions")

        # Créer l'utilisateur admin
        admin_user = User(
            id=str(uuid4()),
            email="admin@usenghor.org",
            password_hash=get_password_hash("Admin123!"),
            last_name="Admin",
            first_name="Administrateur",
            salutation="Mr",
            active=True,
            email_verified=True,
        )
        db.add(admin_user)
        await db.flush()

        # Attribuer le rôle super_admin
        user_role = UserRole(
            user_id=admin_user.id,
            role_id=super_admin_role.id,
        )
        db.add(user_role)

        await db.commit()

        print()
        print("=" * 60)
        print("[SUCCESS] Utilisateur admin créé avec succès !")
        print("=" * 60)
        print()
        print("  Identifiants :")
        print("    Email: admin@usenghor.org")
        print("    Mot de passe: Admin123!")
        print()
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(create_admin())
