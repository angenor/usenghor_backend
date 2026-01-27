#!/usr/bin/env python3
"""
Seed script : Médias et Albums
==============================
Crée des données de simulation pour la médiathèque (médias et albums).

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_media.py
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.base import MediaType, PublicationStatus
from app.models.media import Album, AlbumMedia, Media


# Données des médias - Images avec picsum.photos pour avoir de vraies images
MEDIA_DATA = [
    # === IMAGES (15) ===
    {
        "name": "Vue aérienne campus Alexandrie",
        "description": "Photo drone du campus principal de l'Université Senghor",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/campus-alx-001/1200/800",
        "is_external_url": True,
        "size_bytes": 245000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Vue aérienne du campus d'Alexandrie",
        "credits": "Service Communication USenghor",
    },
    {
        "name": "Bibliothèque universitaire",
        "description": "Intérieur de la bibliothèque centrale avec espaces de lecture",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/biblio-usenghor-002/1200/800",
        "is_external_url": True,
        "size_bytes": 185000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Bibliothèque universitaire",
        "credits": "USenghor",
    },
    {
        "name": "Amphithéâtre principal",
        "description": "Grand amphithéâtre lors d'une conférence internationale",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/amphi-usenghor-003/1200/800",
        "is_external_url": True,
        "size_bytes": 210000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Amphithéâtre principal",
        "credits": "USenghor",
    },
    {
        "name": "Cérémonie de remise des diplômes",
        "description": "Remise des diplômes de la promotion 2024",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/diplome-usenghor-004/1200/800",
        "is_external_url": True,
        "size_bytes": 195000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Cérémonie de remise des diplômes",
        "credits": "Service Communication USenghor",
    },
    {
        "name": "Étudiants en atelier",
        "description": "Session de design thinking avec les étudiants du master",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/atelier-usenghor-005/1200/800",
        "is_external_url": True,
        "size_bytes": 175000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Étudiants en atelier de design thinking",
        "credits": "USenghor",
    },
    {
        "name": "Façade du bâtiment principal",
        "description": "Vue de face du bâtiment administratif principal",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/facade-usenghor-006/1200/800",
        "is_external_url": True,
        "size_bytes": 230000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Façade du bâtiment principal",
        "credits": "USenghor",
    },
    {
        "name": "Jardin méditerranéen",
        "description": "Les jardins du campus avec végétation méditerranéenne",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/jardin-usenghor-007/1200/800",
        "is_external_url": True,
        "size_bytes": 205000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Jardin méditerranéen du campus",
        "credits": "USenghor",
    },
    {
        "name": "Salle informatique",
        "description": "Centre de ressources informatiques équipé",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/info-usenghor-008/1200/800",
        "is_external_url": True,
        "size_bytes": 180000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Salle informatique moderne",
        "credits": "USenghor",
    },
    {
        "name": "Signature de partenariat",
        "description": "Signature d'un accord de partenariat institutionnel",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/partenariat-usenghor-009/1200/800",
        "is_external_url": True,
        "size_bytes": 165000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Signature de partenariat",
        "credits": "Service Communication USenghor",
    },
    {
        "name": "Conférence internationale",
        "description": "Panel de discussion lors d'une conférence internationale",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/conference-usenghor-010/1200/800",
        "is_external_url": True,
        "size_bytes": 190000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Conférence internationale",
        "credits": "USenghor",
    },
    {
        "name": "Résidence étudiante",
        "description": "Vue extérieure de la résidence universitaire",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/residence-usenghor-011/1200/800",
        "is_external_url": True,
        "size_bytes": 215000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Résidence étudiante",
        "credits": "USenghor",
    },
    {
        "name": "Cafétéria universitaire",
        "description": "Espace de restauration et de convivialité",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/cafeteria-usenghor-012/1200/800",
        "is_external_url": True,
        "size_bytes": 170000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Cafétéria universitaire",
        "credits": "USenghor",
    },
    {
        "name": "Équipe administrative",
        "description": "Photo de groupe de l'équipe administrative",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/equipe-usenghor-013/1200/800",
        "is_external_url": True,
        "size_bytes": 185000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Équipe administrative USenghor",
        "credits": "Service Communication USenghor",
    },
    {
        "name": "Salle de cours",
        "description": "Salle de cours équipée pour l'enseignement hybride",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/salle-usenghor-014/1200/800",
        "is_external_url": True,
        "size_bytes": 175000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Salle de cours moderne",
        "credits": "USenghor",
    },
    {
        "name": "Cour intérieure",
        "description": "Cour intérieure du bâtiment principal avec fontaine",
        "type": MediaType.IMAGE,
        "url": "https://picsum.photos/seed/cour-usenghor-015/1200/800",
        "is_external_url": True,
        "size_bytes": 220000,
        "mime_type": "image/jpeg",
        "width": 1200,
        "height": 800,
        "alt_text": "Cour intérieure",
        "credits": "USenghor",
    },
    # === VIDÉOS (4) ===
    {
        "name": "Présentation de l'Université Senghor",
        "description": "Vidéo institutionnelle présentant l'université, sa mission et ses formations",
        "type": MediaType.VIDEO,
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "is_external_url": True,
        "duration_seconds": 245,
        "alt_text": "Vidéo de présentation USenghor",
        "credits": "Service Communication USenghor",
    },
    {
        "name": "Témoignages d'anciens étudiants",
        "description": "Témoignages vidéo d'alumni sur leur parcours professionnel",
        "type": MediaType.VIDEO,
        "url": "https://www.youtube.com/watch?v=example123",
        "is_external_url": True,
        "duration_seconds": 480,
        "alt_text": "Témoignages d'anciens étudiants",
        "credits": "USenghor",
    },
    {
        "name": "Visite virtuelle du campus",
        "description": "Visite guidée du campus en vidéo 360°",
        "type": MediaType.VIDEO,
        "url": "https://www.youtube.com/watch?v=example456",
        "is_external_url": True,
        "duration_seconds": 600,
        "alt_text": "Visite virtuelle du campus",
        "credits": "Service Communication USenghor",
    },
    {
        "name": "Conférence du Recteur",
        "description": "Discours du Recteur lors de la rentrée académique 2024",
        "type": MediaType.VIDEO,
        "url": "https://www.youtube.com/watch?v=example789",
        "is_external_url": True,
        "duration_seconds": 1800,
        "alt_text": "Conférence du Recteur",
        "credits": "USenghor",
    },
    # === DOCUMENTS (2) ===
    {
        "name": "Brochure institutionnelle 2024-2025",
        "description": "Brochure de présentation de l'université et de ses formations",
        "type": MediaType.DOCUMENT,
        "url": "https://example.com/brochure-usenghor-2024-2025.pdf",
        "is_external_url": True,
        "size_bytes": 5200000,
        "mime_type": "application/pdf",
        "alt_text": "Brochure institutionnelle USenghor",
    },
    {
        "name": "Guide de l'étudiant 2024-2025",
        "description": "Guide complet pour les étudiants : vie sur le campus, services, règlement",
        "type": MediaType.DOCUMENT,
        "url": "https://example.com/guide-etudiant-usenghor-2024-2025.pdf",
        "is_external_url": True,
        "size_bytes": 3800000,
        "mime_type": "application/pdf",
        "alt_text": "Guide de l'étudiant USenghor",
    },
]

# Données des albums avec indices des médias à associer
ALBUMS_DATA = [
    {
        "title": "Cérémonie de remise des diplômes 2024",
        "description": "Photos officielles de la cérémonie de remise des diplômes de la promotion 2024",
        "status": PublicationStatus.PUBLISHED,
        "media_indices": [3, 2, 4, 12],  # Cérémonie, Amphi, Atelier, Équipe
    },
    {
        "title": "Campus d'Alexandrie - Visite guidée",
        "description": "Découverte des installations et espaces du campus principal",
        "status": PublicationStatus.PUBLISHED,
        "media_indices": [0, 5, 6, 1, 14, 10, 11],  # Vue aérienne, Façade, Jardin, Biblio, Cour, Résidence, Cafétéria
    },
    {
        "title": "Ateliers pédagogiques Novembre 2024",
        "description": "Sessions de design thinking et travaux collaboratifs avec les étudiants",
        "status": PublicationStatus.PUBLISHED,
        "media_indices": [4, 7, 13],  # Atelier, Salle info, Salle cours
    },
    {
        "title": "Conférence internationale 2024",
        "description": "Moments forts de la conférence internationale sur le développement durable",
        "status": PublicationStatus.PUBLISHED,
        "media_indices": [9, 2, 8],  # Conférence, Amphi, Signature
    },
    {
        "title": "Partenariats et conventions 2024",
        "description": "Signatures de partenariats institutionnels et conventions académiques",
        "status": PublicationStatus.DRAFT,
        "media_indices": [8, 9],  # Signature, Conférence
    },
    {
        "title": "Vidéos institutionnelles",
        "description": "Collection de vidéos de présentation de l'université",
        "status": PublicationStatus.PUBLISHED,
        "media_indices": [15, 16, 17, 18],  # Les 4 vidéos
    },
    {
        "title": "Vie étudiante 2024",
        "description": "Moments de vie quotidienne sur le campus d'Alexandrie",
        "status": PublicationStatus.DRAFT,
        "media_indices": [10, 11, 4, 6],  # Résidence, Cafétéria, Atelier, Jardin
    },
]


async def seed():
    """Insère les données de seed pour les médias et albums."""
    async with async_session_maker() as db:
        # Vérifier si des médias existent déjà
        existing_media = (await db.execute(select(Media).limit(1))).scalar_one_or_none()

        if existing_media:
            print("[SKIP] Des médias existent déjà. Seed ignoré.")
            print("       Pour réinitialiser, supprimez les données existantes.")
            return

        now = datetime.now(timezone.utc)
        print()
        print("[INFO] Création des médias...")

        # Créer les médias
        media_objects = []
        for i, data in enumerate(MEDIA_DATA):
            # Créer le média avec une date de création échelonnée
            created_at = now - timedelta(days=365 - i * 15)  # Échelonner sur l'année
            media = Media(
                id=str(uuid4()),
                name=data["name"],
                description=data.get("description"),
                type=data["type"],
                url=data["url"],
                is_external_url=data.get("is_external_url", False),
                size_bytes=data.get("size_bytes"),
                mime_type=data.get("mime_type"),
                width=data.get("width"),
                height=data.get("height"),
                duration_seconds=data.get("duration_seconds"),
                alt_text=data.get("alt_text"),
                credits=data.get("credits"),
                created_at=created_at,
                updated_at=created_at,
            )
            db.add(media)
            media_objects.append(media)

        await db.flush()

        images_count = len([m for m in media_objects if m.type == MediaType.IMAGE])
        videos_count = len([m for m in media_objects if m.type == MediaType.VIDEO])
        docs_count = len([m for m in media_objects if m.type == MediaType.DOCUMENT])
        print(f"[OK] {len(media_objects)} médias créés ({images_count} images, {videos_count} vidéos, {docs_count} documents)")

        # Créer les albums
        print("[INFO] Création des albums...")
        album_objects = []
        for data in ALBUMS_DATA:
            album = Album(
                id=str(uuid4()),
                title=data["title"],
                description=data.get("description"),
                status=data.get("status", PublicationStatus.DRAFT),
                created_at=now,
                updated_at=now,
            )
            db.add(album)
            album_objects.append((album, data.get("media_indices", [])))

        await db.flush()
        print(f"[OK] {len(album_objects)} albums créés")

        # Créer les relations album-média
        print("[INFO] Création des relations album-média...")
        relations_count = 0
        for album, media_indices in album_objects:
            for order, media_idx in enumerate(media_indices):
                if media_idx < len(media_objects):
                    album_media = AlbumMedia(
                        album_id=album.id,
                        media_id=media_objects[media_idx].id,
                        display_order=order,
                    )
                    db.add(album_media)
                    relations_count += 1

        await db.commit()
        print(f"[OK] {relations_count} relations album-média créées")

        # Résumé final
        print()
        print("=" * 60)
        print("Seed des médias et albums terminé avec succès !")
        print("=" * 60)
        print(f"  Médias créés     : {len(media_objects)}")
        print(f"    - Images       : {images_count}")
        print(f"    - Vidéos       : {videos_count}")
        print(f"    - Documents    : {docs_count}")
        print(f"  Albums créés     : {len(album_objects)}")
        print(f"  Relations créées : {relations_count}")
        print()
        print("  Albums :")
        for album, media_indices in album_objects:
            status = "📢" if album.status == PublicationStatus.PUBLISHED else "📝"
            print(f"    {status} {album.title} ({len(media_indices)} médias)")
        print()
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
