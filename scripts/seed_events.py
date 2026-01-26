#!/usr/bin/env python3
"""
Seed script : Événements
========================
Crée des données de simulation pour les événements.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_events.py
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
from app.models.content import Event, EventType


async def seed():
    """Insère les données de seed pour les événements."""
    async with async_session_maker() as db:
        # ================================================================
        # 1. Vérifier si des événements existent déjà
        # ================================================================
        existing_events = (
            await db.execute(select(Event).limit(1))
        ).scalar_one_or_none()

        if existing_events:
            print("[SKIP] Des événements existent déjà. Seed ignoré.")
            return

        # ================================================================
        # 2. Créer les événements
        # ================================================================
        now = datetime.now(timezone.utc)

        events_data = [
            # --- 1. Conférence inaugurale (published, à venir) ---
            {
                "title": "Conférence inaugurale : L'avenir de la Francophonie en Afrique",
                "slug": "conference-inaugurale-francophonie-afrique-2026",
                "description": "Grande conférence réunissant des experts internationaux pour discuter des enjeux et perspectives de la Francophonie africaine dans un contexte de mondialisation.",
                "content": json.dumps({
                    "blocks": [
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "Cette conférence exceptionnelle réunira des experts internationaux, des décideurs politiques et des universitaires pour explorer l'avenir de la Francophonie en Afrique."
                            }
                        },
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "Au programme : tables rondes, interventions d'experts et networking avec les acteurs clés du développement francophone."
                            }
                        }
                    ]
                }),
                "type": EventType.CONFERENCE,
                "start_date": now + timedelta(days=60),
                "end_date": now + timedelta(days=60, hours=8),
                "is_online": False,
                "venue": "Amphithéâtre Léopold Sédar Senghor",
                "address": "1 Place Ahmed Orabi",
                "city": "Alexandrie",
                "registration_required": True,
                "max_attendees": 300,
                "status": PublicationStatus.PUBLISHED,
            },
            # --- 2. Atelier leadership (published, à venir) ---
            {
                "title": "Atelier de formation en leadership pour cadres africains",
                "slug": "atelier-formation-leadership-2026",
                "description": "Atelier intensif de trois jours sur le développement du leadership pour les futurs décideurs africains.",
                "content": json.dumps({
                    "blocks": [
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "Cet atelier pratique vous permettra de développer vos compétences en leadership, communication et gestion d'équipe."
                            }
                        }
                    ]
                }),
                "type": EventType.WORKSHOP,
                "start_date": now + timedelta(days=75),
                "end_date": now + timedelta(days=77),
                "is_online": False,
                "venue": "Salle de conférence A",
                "city": "Alexandrie",
                "registration_required": True,
                "max_attendees": 30,
                "status": PublicationStatus.PUBLISHED,
            },
            # --- 3. Cérémonie diplômes (published, hybrid) ---
            {
                "title": "Cérémonie de remise des diplômes - Promotion 2025",
                "slug": "ceremonie-remise-diplomes-2025",
                "description": "Cérémonie officielle de remise des diplômes pour la promotion 2025, retransmise en direct.",
                "content": json.dumps({
                    "blocks": [
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "Rejoignez-nous pour célébrer la réussite de nos diplômés lors de cette cérémonie solennelle."
                            }
                        }
                    ]
                }),
                "type": EventType.CEREMONY,
                "start_date": now + timedelta(days=35),
                "end_date": now + timedelta(days=35, hours=4),
                "is_online": True,
                "video_conference_link": "https://meet.usenghor.org/graduation-2025",
                "venue": "Bibliotheca Alexandrina",
                "city": "Alexandrie",
                "registration_required": True,
                "max_attendees": 500,
                "status": PublicationStatus.PUBLISHED,
            },
            # --- 4. Séminaire gouvernance (published, à venir) ---
            {
                "title": "Séminaire international sur la gouvernance en Afrique",
                "slug": "seminaire-international-gouvernance-2026",
                "description": "Séminaire réunissant chercheurs et praticiens autour des questions de gouvernance et d'administration publique.",
                "type": EventType.SEMINAR,
                "start_date": now + timedelta(days=120),
                "end_date": now + timedelta(days=121),
                "is_online": False,
                "venue": "Amphithéâtre Léopold Sédar Senghor",
                "city": "Alexandrie",
                "registration_required": True,
                "max_attendees": 150,
                "status": PublicationStatus.PUBLISHED,
            },
            # --- 5. Webinaire IA (published, en ligne) ---
            {
                "title": "Webinaire : Intelligence artificielle et éducation en Afrique",
                "slug": "webinaire-ia-education-afrique-2026",
                "description": "Webinaire sur les applications de l'IA dans l'enseignement supérieur africain.",
                "content": json.dumps({
                    "blocks": [
                        {
                            "type": "paragraph",
                            "data": {
                                "text": "Découvrez comment l'intelligence artificielle transforme l'éducation en Afrique et quelles opportunités elle offre pour l'enseignement supérieur."
                            }
                        }
                    ]
                }),
                "type": EventType.CONFERENCE,
                "start_date": now + timedelta(days=45),
                "end_date": now + timedelta(days=45, hours=2),
                "is_online": True,
                "video_conference_link": "https://zoom.us/j/123456789",
                "registration_required": True,
                "max_attendees": 500,
                "status": PublicationStatus.PUBLISHED,
            },
            # --- 6. Colloque culture (published, Abidjan) ---
            {
                "title": "Colloque : Politiques culturelles et développement durable",
                "slug": "colloque-politiques-culturelles-2026",
                "description": "Colloque interdisciplinaire explorant le rôle des politiques culturelles dans le développement durable africain.",
                "type": EventType.SYMPOSIUM,
                "start_date": now + timedelta(days=180),
                "end_date": now + timedelta(days=182),
                "is_online": False,
                "venue": "Centre de conférences",
                "city": "Abidjan",
                "registration_required": True,
                "max_attendees": 200,
                "status": PublicationStatus.PUBLISHED,
            },
            # --- 7. Journée portes ouvertes (draft) ---
            {
                "title": "Journée portes ouvertes - Avril 2026",
                "slug": "journee-portes-ouvertes-avril-2026",
                "description": "Découvrez nos formations et rencontrez nos équipes pédagogiques lors de cette journée d'accueil.",
                "type": EventType.OTHER,
                "type_other": "Portes ouvertes",
                "start_date": now + timedelta(days=90),
                "end_date": now + timedelta(days=90, hours=6),
                "is_online": True,
                "video_conference_link": "https://meet.usenghor.org/open-day",
                "venue": "Université Senghor",
                "city": "Alexandrie",
                "registration_required": False,
                "status": PublicationStatus.DRAFT,
            },
            # --- 8. Forum alumni (draft) ---
            {
                "title": "Forum des alumni 2026",
                "slug": "forum-alumni-2026",
                "description": "Rencontre annuelle des anciens étudiants de l'Université Senghor.",
                "type": EventType.OTHER,
                "type_other": "Forum",
                "start_date": now + timedelta(days=200),
                "end_date": now + timedelta(days=200, hours=9),
                "is_online": False,
                "venue": "Hôtel Sofitel",
                "city": "Alexandrie",
                "registration_required": True,
                "max_attendees": 250,
                "status": PublicationStatus.DRAFT,
            },
            # --- 9. Événement passé (archived) ---
            {
                "title": "Conférence sur l'innovation numérique",
                "slug": "conference-innovation-numerique-dec-2025",
                "description": "Conférence sur l'innovation numérique en Afrique (événement passé).",
                "type": EventType.CONFERENCE,
                "start_date": now - timedelta(days=30),
                "end_date": now - timedelta(days=30) + timedelta(hours=8),
                "is_online": False,
                "venue": "Amphithéâtre Léopold Sédar Senghor",
                "city": "Alexandrie",
                "registration_required": True,
                "max_attendees": 200,
                "status": PublicationStatus.ARCHIVED,
            },
            # --- 10. Atelier passé (archived) ---
            {
                "title": "Atelier entrepreneuriat africain",
                "slug": "atelier-entrepreneuriat-nov-2025",
                "description": "Atelier pratique sur l'entrepreneuriat (événement passé).",
                "type": EventType.WORKSHOP,
                "start_date": now - timedelta(days=60),
                "end_date": now - timedelta(days=59),
                "is_online": False,
                "venue": "Salle de conférence B",
                "city": "Alexandrie",
                "registration_required": True,
                "max_attendees": 40,
                "status": PublicationStatus.ARCHIVED,
            },
        ]

        created_events = []
        for data in events_data:
            event = Event(
                id=str(uuid4()),
                **data,
            )
            db.add(event)
            created_events.append(event)

        await db.commit()

        # ================================================================
        # Résumé
        # ================================================================
        published = sum(1 for e in created_events if e.status == PublicationStatus.PUBLISHED)
        draft = sum(1 for e in created_events if e.status == PublicationStatus.DRAFT)
        archived = sum(1 for e in created_events if e.status == PublicationStatus.ARCHIVED)

        print()
        print("=" * 50)
        print("Seed événements terminé avec succès !")
        print("=" * 50)
        print(f"  Total créés   : {len(created_events)}")
        print(f"  - Publiés     : {published}")
        print(f"  - Brouillons  : {draft}")
        print(f"  - Archivés    : {archived}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
