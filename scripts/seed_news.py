#!/usr/bin/env python3
"""
Seed script : Actualités et Tags
================================
Crée des données de simulation pour les actualités et les tags.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_news.py
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.base import PublicationStatus
from app.models.content import News, NewsHighlightStatus, Tag, NewsTag


async def seed():
    """Insère les données de seed pour les actualités et tags."""
    async with async_session_maker() as db:
        # ================================================================
        # 1. Vérifier si des actualités existent déjà
        # ================================================================
        existing_news = (
            await db.execute(select(News).limit(1))
        ).scalar_one_or_none()

        if existing_news:
            print("[SKIP] Des actualités existent déjà. Seed ignoré.")
            return

        # ================================================================
        # 2. Créer les tags
        # ================================================================
        print("[INFO] Création des tags...")

        tags_data = [
            {"name": "Académique", "slug": "academique", "icon": "fa-graduation-cap", "description": "Actualités liées aux programmes académiques"},
            {"name": "Partenariat", "slug": "partenariat", "icon": "fa-handshake", "description": "Partenariats institutionnels et collaborations"},
            {"name": "Événement", "slug": "evenement", "icon": "fa-calendar", "description": "Événements et manifestations"},
            {"name": "Recherche", "slug": "recherche", "icon": "fa-flask", "description": "Recherche et innovation"},
            {"name": "International", "slug": "international", "icon": "fa-globe", "description": "Relations internationales"},
            {"name": "Alumni", "slug": "alumni", "icon": "fa-users", "description": "Actualités des anciens"},
            {"name": "Formation", "slug": "formation", "icon": "fa-book", "description": "Formations continues et certifications"},
            {"name": "Innovation", "slug": "innovation", "icon": "fa-lightbulb", "description": "Innovation et développement"},
            {"name": "Culture", "slug": "culture", "icon": "fa-palette", "description": "Vie culturelle et artistique"},
            {"name": "Gouvernance", "slug": "gouvernance", "icon": "fa-landmark", "description": "Gouvernance et administration"},
        ]

        tags = {}
        for tag_data in tags_data:
            tag = Tag(
                id=str(uuid4()),
                **tag_data
            )
            db.add(tag)
            tags[tag_data["slug"]] = tag

        await db.flush()
        print(f"[OK] {len(tags)} tags créés")

        # ================================================================
        # 3. Créer les actualités
        # ================================================================
        print("[INFO] Création des actualités...")

        now = datetime.now(timezone.utc)

        def make_content(fr_text: str, en_text: str = None, ar_text: str = None):
            """Crée un contenu multilingue JSON."""
            content = {
                "fr": {
                    "time": int(now.timestamp() * 1000),
                    "version": "2.28.2",
                    "blocks": [
                        {"id": str(uuid4())[:8], "type": "paragraph", "data": {"text": fr_text}}
                    ]
                }
            }
            if en_text:
                content["en"] = {
                    "time": int(now.timestamp() * 1000),
                    "version": "2.28.2",
                    "blocks": [
                        {"id": str(uuid4())[:8], "type": "paragraph", "data": {"text": en_text}}
                    ]
                }
            if ar_text:
                content["ar"] = {
                    "time": int(now.timestamp() * 1000),
                    "version": "2.28.2",
                    "blocks": [
                        {"id": str(uuid4())[:8], "type": "paragraph", "data": {"text": ar_text}}
                    ]
                }
            return json.dumps(content)

        news_data = [
            # === 1. À la une (headline) ===
            {
                "title": "L'Université Senghor célèbre ses 35 ans d'excellence au service de l'Afrique",
                "slug": "35-ans-universite-senghor",
                "summary": "L'Université Senghor fête 35 années d'engagement pour la formation des cadres africains et le développement durable du continent.",
                "content": make_content(
                    "Depuis sa création en 1990, l'Université Senghor s'est imposée comme un acteur incontournable de la formation des cadres africains. Avec plus de 3000 diplômés issus de 54 pays africains, notre institution continue de porter les valeurs de la Francophonie et du développement durable.",
                    "Since its creation in 1990, Senghor University has established itself as a key player in training African executives. With over 3000 graduates from 54 African countries, our institution continues to uphold the values of Francophonie and sustainable development."
                ),
                "highlight_status": NewsHighlightStatus.HEADLINE,
                "status": PublicationStatus.PUBLISHED,
                "published_at": now - timedelta(days=5),
                "tag_slugs": ["academique", "international"],
            },
            # === 2-4. Mises en avant (featured) ===
            {
                "title": "Nouveau partenariat stratégique avec l'Organisation Internationale de la Francophonie",
                "slug": "partenariat-oif-2026",
                "summary": "Signature d'un accord-cadre renforçant la coopération avec l'OIF pour les cinq prochaines années.",
                "content": make_content(
                    "L'Université Senghor et l'OIF renforcent leur collaboration historique avec la signature d'un nouvel accord-cadre ambitieux. Ce partenariat permettra de développer des programmes innovants en matière de développement durable et de gouvernance."
                ),
                "highlight_status": NewsHighlightStatus.FEATURED,
                "status": PublicationStatus.PUBLISHED,
                "published_at": now - timedelta(days=10),
                "tag_slugs": ["partenariat", "international"],
            },
            {
                "title": "Rentrée académique 2025-2026 : plus de 200 nouveaux étudiants accueillis",
                "slug": "rentree-academique-2025-2026",
                "summary": "L'Université accueille sa nouvelle promotion avec des étudiants venus de 35 pays africains.",
                "content": make_content(
                    "La cérémonie de rentrée a rassemblé plus de 200 nouveaux étudiants représentant 35 pays africains. Cette diversité illustre le rayonnement continental de notre université et son rôle dans la formation des leaders de demain."
                ),
                "highlight_status": NewsHighlightStatus.FEATURED,
                "status": PublicationStatus.PUBLISHED,
                "published_at": now - timedelta(days=15),
                "tag_slugs": ["academique", "evenement"],
            },
            {
                "title": "Lancement du programme KreAfrika pour l'entrepreneuriat culturel",
                "slug": "programme-kreafrika-entrepreneuriat",
                "summary": "Un nouveau programme pour former les entrepreneurs culturels africains de demain.",
                "content": make_content(
                    "Le programme KreAfrika vise à former la prochaine génération d'entrepreneurs culturels africains. En partenariat avec des institutions culturelles majeures, ce programme offre une formation unique alliant créativité et business."
                ),
                "highlight_status": NewsHighlightStatus.FEATURED,
                "status": PublicationStatus.PUBLISHED,
                "published_at": now - timedelta(days=20),
                "tag_slugs": ["formation", "innovation", "culture"],
            },
            # === 5-8. Standard publiées ===
            {
                "title": "Conférence internationale sur le développement durable en Afrique",
                "slug": "conference-developpement-durable-afrique",
                "summary": "Retour sur les échanges de la conférence qui a réuni 150 experts internationaux.",
                "content": make_content(
                    "La conférence sur le développement durable a permis de dresser un bilan des avancées et des défis du continent. Les participants ont adopté une déclaration commune pour renforcer les actions en faveur de l'environnement."
                ),
                "highlight_status": NewsHighlightStatus.STANDARD,
                "status": PublicationStatus.PUBLISHED,
                "published_at": now - timedelta(days=25),
                "tag_slugs": ["evenement", "recherche"],
            },
            {
                "title": "Les Alumni de l'Université Senghor se retrouvent à Dakar",
                "slug": "alumni-retrouvailles-dakar-2025",
                "summary": "Plus de 80 anciens étudiants ont participé à la rencontre annuelle du réseau Alumni.",
                "content": make_content(
                    "La rencontre annuelle des Alumni à Dakar a été l'occasion de renforcer les liens entre anciens et de développer des projets de collaboration. Des tables rondes ont permis d'échanger sur les défis de développement du continent."
                ),
                "highlight_status": NewsHighlightStatus.STANDARD,
                "status": PublicationStatus.PUBLISHED,
                "published_at": now - timedelta(days=30),
                "tag_slugs": ["alumni", "evenement"],
            },
            {
                "title": "Publication du rapport annuel de recherche 2025",
                "slug": "rapport-recherche-2025",
                "summary": "Le rapport met en lumière les 45 projets de recherche menés par nos équipes.",
                "content": make_content(
                    "Le rapport annuel de recherche 2025 présente les avancées majeures de nos équipes dans les domaines du patrimoine, de l'environnement et de la gouvernance. 45 projets ont été menés à bien cette année."
                ),
                "highlight_status": NewsHighlightStatus.STANDARD,
                "status": PublicationStatus.PUBLISHED,
                "published_at": now - timedelta(days=35),
                "tag_slugs": ["recherche", "academique"],
            },
            {
                "title": "Formation continue : nouvelles certifications en management public",
                "slug": "certifications-management-public-2025",
                "summary": "Trois nouvelles certifications professionnelles sont désormais disponibles.",
                "content": make_content(
                    "L'Université Senghor enrichit son offre de formation continue avec trois nouvelles certifications en management public. Ces programmes courts s'adressent aux cadres en activité souhaitant développer leurs compétences."
                ),
                "highlight_status": NewsHighlightStatus.STANDARD,
                "status": PublicationStatus.PUBLISHED,
                "published_at": now - timedelta(days=40),
                "tag_slugs": ["formation", "gouvernance"],
            },
            # === 9. Brouillon ===
            {
                "title": "Projet de rénovation du campus - Consultation publique",
                "slug": "projet-renovation-campus-2026",
                "summary": "Présentation du projet de modernisation des infrastructures du campus principal.",
                "content": make_content(
                    "Le projet de rénovation vise à moderniser les infrastructures du campus tout en préservant le patrimoine architectural. Une consultation publique sera organisée prochainement."
                ),
                "highlight_status": NewsHighlightStatus.STANDARD,
                "status": PublicationStatus.DRAFT,
                "published_at": None,
                "tag_slugs": ["gouvernance"],
            },
            # === 10. Archivée ===
            {
                "title": "Bilan de la semaine de l'innovation 2024",
                "slug": "bilan-semaine-innovation-2024",
                "summary": "Retour sur les temps forts de la semaine dédiée à l'innovation.",
                "content": make_content(
                    "La semaine de l'innovation 2024 a été un succès avec plus de 500 participants. Les projets présentés par nos étudiants ont démontré leur créativité et leur engagement."
                ),
                "highlight_status": NewsHighlightStatus.STANDARD,
                "status": PublicationStatus.ARCHIVED,
                "published_at": now - timedelta(days=180),
                "tag_slugs": ["innovation", "evenement"],
            },
        ]

        news_items = []
        for news in news_data:
            tag_slugs = news.pop("tag_slugs", [])
            news_item = News(
                id=str(uuid4()),
                **news,
                created_at=now,
                updated_at=now,
            )
            db.add(news_item)
            news_items.append((news_item, tag_slugs))

        await db.flush()

        # ================================================================
        # 4. Créer les relations news_tags
        # ================================================================
        print("[INFO] Création des relations news-tags...")

        for news_item, tag_slugs in news_items:
            for slug in tag_slugs:
                if slug in tags:
                    news_tag = NewsTag(
                        news_id=news_item.id,
                        tag_id=tags[slug].id
                    )
                    db.add(news_tag)

        await db.commit()
        print(f"[OK] {len(news_items)} actualités créées avec leurs tags")

        print("\n[SUCCESS] Seed des actualités terminé !")
        print(f"  - {len(tags)} tags")
        print(f"  - {len(news_items)} actualités")
        print("    - 1 à la une (headline)")
        print("    - 3 mises en avant (featured)")
        print("    - 4 publiées (standard)")
        print("    - 1 brouillon (draft)")
        print("    - 1 archivée (archived)")


if __name__ == "__main__":
    asyncio.run(seed())
