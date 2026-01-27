#!/usr/bin/env python3
"""
Seed script : Social Media (Réseaux sociaux)
=============================================
Crée les données de référence pour les réseaux sociaux de l'Université Senghor.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_social_media.py
"""

import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.editorial import (
    EditorialCategory,
    EditorialContent,
    EditorialValueType,
)


# ============================================================================
# CATÉGORIE
# ============================================================================

SOCIAL_MEDIA_CATEGORY = {
    "code": "social_media",
    "name": "Réseaux sociaux",
    "description": "Liens vers les réseaux sociaux de l'université",
}


# ============================================================================
# RÉSEAUX SOCIAUX
# ============================================================================

SOCIAL_MEDIA_DATA = [
    {
        "platform": "facebook",
        "url": "https://www.facebook.com/UniversiteSenghor",
        "active": True,
        "display_order": 1,
    },
    {
        "platform": "linkedin",
        "url": "https://www.linkedin.com/school/universite-senghor/",
        "active": True,
        "display_order": 2,
    },
    {
        "platform": "youtube",
        "url": "https://www.youtube.com/@UniversiteSenghor",
        "active": True,
        "display_order": 3,
    },
    {
        "platform": "twitter",
        "url": "https://x.com/USenghor",
        "active": True,
        "display_order": 4,
    },
    {
        "platform": "instagram",
        "url": "https://www.instagram.com/universenghor",
        "active": False,
        "display_order": 5,
    },
    {
        "platform": "whatsapp",
        "url": "https://wa.me/20348435625",
        "active": True,
        "display_order": 6,
    },
]

# Labels des plateformes
PLATFORM_LABELS = {
    "facebook": "Facebook",
    "twitter": "Twitter / X",
    "linkedin": "LinkedIn",
    "instagram": "Instagram",
    "youtube": "YouTube",
    "tiktok": "TikTok",
    "whatsapp": "WhatsApp",
    "telegram": "Telegram",
    "other": "Autre",
}


async def seed():
    """Insère les données de seed pour les réseaux sociaux."""
    async with async_session_maker() as db:
        # Vérifier/créer la catégorie "social_media"
        existing_cat = (
            await db.execute(
                select(EditorialCategory).where(
                    EditorialCategory.code == SOCIAL_MEDIA_CATEGORY["code"]
                )
            )
        ).scalar_one_or_none()

        if existing_cat:
            category_id = existing_cat.id
            print(f"[INFO] Catégorie '{SOCIAL_MEDIA_CATEGORY['code']}' existe déjà (ID: {category_id})")
        else:
            category_id = str(uuid4())
            category = EditorialCategory(
                id=category_id,
                code=SOCIAL_MEDIA_CATEGORY["code"],
                name=SOCIAL_MEDIA_CATEGORY["name"],
                description=SOCIAL_MEDIA_CATEGORY["description"],
            )
            db.add(category)
            await db.flush()
            print(f"[OK] Catégorie '{SOCIAL_MEDIA_CATEGORY['code']}' créée (ID: {category_id})")

        # Vérifier si des contenus existent déjà pour cette catégorie
        existing_contents = (
            await db.execute(
                select(EditorialContent).where(
                    EditorialContent.category_id == category_id
                )
            )
        ).scalars().all()

        if existing_contents:
            print(f"[SKIP] {len(existing_contents)} réseaux sociaux existent déjà. Seed ignoré.")
            print("       Utilisez 'python scripts/seed_social_media.py --force' pour recréer.")
            return

        social_media_created = []

        # Créer les réseaux sociaux
        for data in SOCIAL_MEDIA_DATA:
            key = f"social_media_{str(uuid4())[:8]}"
            content = EditorialContent(
                id=str(uuid4()),
                key=key,
                value=json.dumps(data, ensure_ascii=False),
                value_type=EditorialValueType.JSON,
                category_id=category_id,
                description=PLATFORM_LABELS.get(data["platform"], data["platform"]),
                admin_editable=True,
            )
            db.add(content)
            social_media_created.append((data["platform"], data["url"], data["active"]))

        await db.commit()

        print()
        print("=" * 60)
        print("Seed des réseaux sociaux terminé avec succès !")
        print("=" * 60)
        print(f"  Catégorie : {SOCIAL_MEDIA_CATEGORY['name']}")
        print(f"  Réseaux sociaux créés : {len(social_media_created)}")
        for platform, url, active in social_media_created:
            status = "✓" if active else "○"
            print(f"    {status} {PLATFORM_LABELS.get(platform, platform)}: {url}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
