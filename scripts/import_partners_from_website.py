#!/usr/bin/env python3
"""
Import des partenaires depuis le site usenghor-francophonie.org
===============================================================

Télécharge les logos et crée les enregistrements media + partners
dans la base de données locale.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/import_partners_from_website.py
"""

import asyncio
import mimetypes
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import httpx

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models.base import MediaType
from app.models.media import Media
from app.models.partner import Partner, PartnerType


# --- Configuration ---

STORAGE_PATH = Path(__file__).resolve().parent.parent / "uploads"
LOGOS_FOLDER = "partners/logos"
LOGOS_DIR = STORAGE_PATH / LOGOS_FOLDER

# Valeurs par défaut
DEFAULT_PARTNER_TYPE = PartnerType.CAMPUS_PARTNER
DEFAULT_ACTIVE = False  # Inactif par défaut


# --- Données scrapées depuis https://usenghor-francophonie.org/partenaires/ ---

PARTNERS_DATA = [
    {"name": "OIF", "website": "https://www.francophonie.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/01.jpg"},
    {"name": "APF", "website": "https://apf-francophonie.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/02.png"},
    {"name": "AUF", "website": "https://www.auf.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/03.png"},
    {"name": "AIMF", "website": "https://www.aimf.asso.fr/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/04.jpg"},
    {"name": "Enap Quebec", "website": "https://enap.ca/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/1.png"},
    {"name": "Université du Luxembourg", "website": "https://www.uni.lu/fr/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/2.png"},
    {"name": "Université de Porto", "website": "https://www.up.pt/portal/en/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/3.png"},
    {"name": "Institut français Égypte", "website": "https://www.ifegypte.com/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/5.png"},
    {"name": "IBDL", "website": "https://ibdl.net/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/6.png"},
    {"name": "Ina", "website": "https://www.ina.fr/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/7.png"},
    {"name": "ICHEC", "website": "https://www.ichec.be/fr", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/8.png"},
    {"name": "CEAlex", "website": "https://www.cealex.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/9.png"},
    {"name": "Ramsar", "website": "https://www.ramsar.org/fr", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/10.png"},
    {"name": "IUCN", "website": "https://www.iucn.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/11.png"},
    {"name": "Sciences Po", "website": "https://www.sciencespo.fr/fr/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/12.png"},
    {"name": "Rennes School Business", "website": "https://www.rennes-sb.fr/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/13.png"},
    {"name": "Em Lyon Business School", "website": "https://em-lyon.com/en", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/14.png"},
    {"name": "Enssib", "website": "https://www.enssib.fr/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/15.png"},
    {"name": "CEAlex (CNRS)", "website": "https://www.cealex.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/16.png"},
    {"name": "CMA", "website": "https://www.cmatlv.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/17.png"},
    {"name": "UCAC", "website": "https://ucac-icy.net/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/18.png"},
    {"name": "Université Catholique du Congo", "website": "https://ucc.ac.cd/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/19.jpg"},
    {"name": "Université Szeged", "website": "https://u-szeged.hu/english", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/20.png"},
    {"name": "Université Mohammed premier de Oujda", "website": "http://www.ump.ma/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/21.png"},
    {"name": "Institut Français d'Archéologie Orientale", "website": "https://www.ifao.egnet.net/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/22.gif"},
    {"name": "CAMES", "website": "https://www.lecames.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/24.jpg"},
    {"name": "Make Sense Africa", "website": "https://makesense.org/en/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/25.png"},
    {"name": "Université de Ouagadougou 2", "website": "https://www.univ-ouaga2.gov.bf/accueil", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/26.jpg"},
    {"name": "École Nationale d'Administration (RDC)", "website": "https://ena.cd/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/27.png"},
    {"name": "Institut Francophone International", "website": "https://ifi.vnu.edu.vn/fr/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/28-300x99.png"},
    {"name": "IDG Dakar", "website": "https://www.idgdakar.com/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/29.png"},
    {"name": "Trace", "website": "https://fr.trace.tv/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/31.jpg"},
    {"name": "EAMAU", "website": "https://www.eamau.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/32.png"},
    {"name": "CCI Côte d'Ivoire", "website": "https://www.cci.ci/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/33.jpg"},
    {"name": "Université Gamal Abdel Nasser de Conakry", "website": "https://uganc.edu.gn/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/34.jpg"},
    {"name": "Université de Parakou", "website": "http://www.univ-parakou.bj/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/35.png"},
    {"name": "CCCPA", "website": "https://www.cccpa-eg.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/36.jpg"},
    {"name": "Université de Pharos", "website": "https://www.pua.edu.eg/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/37.png"},
    {"name": "Ministère égyptien des affaires étrangères", "website": "https://www.mfa.gov.eg/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/38.png"},
    {"name": "IPMD", "website": "https://ipmd.pro/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/40.png"},
    {"name": "ISCAM", "website": "https://www.iscam.mg/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/41.png"},
    {"name": "Institut Supérieur Madiba", "website": "https://www.groupeism.sn/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/42.jpg"},
    {"name": "Bioforce", "website": "https://www.bioforce.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/43.png"},
    {"name": "Enaref", "website": "http://ena.enaref.gov.bf/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/44.jpg"},
    {"name": "UGLC-SC", "website": "https://uglcs.org/home/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/45.png"},
    {"name": "Institut National d'Assainissement et d'Urbanisme", "website": "https://inau.ac.ma/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/46.png"},
    {"name": "Université d'Abomey Calavi", "website": "https://uac.bj/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/47.jpg"},
    {"name": "Ista Cemac", "website": "https://www.ista-cemac.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/48.png"},
    {"name": "CNFTPA", "website": "https://cnftpa.sn/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/49.png"},
    {"name": "Imdr", "website": "https://www.imdr.eu/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/50.jpg"},
    {"name": "Codatu", "website": "https://www.codatu.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/51.jpg"},
    {"name": "Université Internationale de la Mer", "website": "https://www.univ-mer.org/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/52.png"},
    {"name": "EABA", "website": "", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/53.jpg"},
    {"name": "FAO", "website": "https://www.fao.org/home/fr", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/54.png"},
    {"name": "Unesco", "website": "https://www.unesco.org/fr", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/55.png"},
    {"name": "École nationale des chartes", "website": "https://www.chartes.psl.eu/", "logo_url": "https://usenghor-francophonie.org/wp-content/uploads/2023/09/4.png"},
]


def sanitize_filename(name: str) -> str:
    """Convertit un nom en nom de fichier sûr (ASCII, pas de caractères spéciaux)."""
    safe = re.sub(r"[^a-z0-9]", "_", name.lower().strip())
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe[:50]


def download_logo(client: httpx.Client, logo_url: str, partner_name: str) -> tuple[Path | None, str | None, int]:
    """Télécharge un logo et retourne (chemin_fichier, mime_type, taille_octets)."""
    try:
        response = client.get(logo_url, follow_redirects=True, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"    [ERREUR] Téléchargement échoué : {e}")
        return None, None, 0

    # Déterminer le type MIME et l'extension
    content_type = response.headers.get("content-type", "").split(";")[0].strip()
    ext = mimetypes.guess_extension(content_type)
    if not ext:
        ext = os.path.splitext(urlparse(logo_url).path)[1]
    if ext in (".jpe", ".jpeg"):
        ext = ".jpg"

    # Nommage : timestamp_nom_uuid.ext (convention du projet)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    uid = uuid4().hex[:8]
    safe_name = sanitize_filename(partner_name)
    filename = f"{timestamp}_{safe_name}_{uid}{ext}"

    filepath = LOGOS_DIR / filename
    filepath.write_bytes(response.content)

    return filepath, content_type, len(response.content)


async def seed():
    """Importe les partenaires avec leurs logos."""
    # Créer le dossier logos si nécessaire
    LOGOS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Import des partenaires depuis usenghor-francophonie.org")
    print("=" * 60)
    print(f"  Dossier logos : {LOGOS_DIR}")
    print(f"  Partenaires à importer : {len(PARTNERS_DATA)}")
    print()

    async with async_session_maker() as db:
        # Récupérer les noms existants pour éviter les doublons
        result = await db.execute(select(Partner.name))
        existing_names = {row[0] for row in result.all()}
        print(f"[INFO] {len(existing_names)} partenaires existants en base")
        print()

        created = 0
        skipped = 0

        with httpx.Client(
            headers={"User-Agent": "Mozilla/5.0 (Usenghor Seed Script)"},
        ) as client:
            for i, data in enumerate(PARTNERS_DATA, start=1):
                name = data["name"]

                # Vérifier doublon
                if name in existing_names:
                    print(f"  [{i:02d}/{len(PARTNERS_DATA)}] {name} — déjà en base, ignoré")
                    skipped += 1
                    continue

                print(f"  [{i:02d}/{len(PARTNERS_DATA)}] {name}...", end=" ", flush=True)

                # Télécharger le logo
                media_id = None
                if data["logo_url"]:
                    filepath, mime_type, size_bytes = download_logo(
                        client, data["logo_url"], name
                    )

                    if filepath:
                        # Créer l'enregistrement Media
                        media_id = str(uuid4())
                        relative_url = f"/uploads/{LOGOS_FOLDER}/{filepath.name}"

                        media = Media(
                            id=media_id,
                            name=f"Logo {name}",
                            type=MediaType.IMAGE,
                            url=relative_url,
                            is_external_url=False,
                            size_bytes=size_bytes,
                            mime_type=mime_type,
                            alt_text=f"Logo du partenaire {name}",
                        )
                        db.add(media)

                # Nettoyer le website
                website = data["website"].strip()
                if website and "usenghor-francophonie.org/partenaires" in website:
                    website = ""

                # Créer l'enregistrement Partner
                partner = Partner(
                    id=str(uuid4()),
                    name=name,
                    logo_external_id=media_id,
                    website=website or None,
                    type=DEFAULT_PARTNER_TYPE,
                    active=DEFAULT_ACTIVE,
                    display_order=i,
                )
                db.add(partner)

                logo_status = "avec logo" if media_id else "sans logo"
                print(f"OK ({logo_status})")
                created += 1

        await db.commit()

    print()
    print("=" * 60)
    print(f"  Créés   : {created}")
    print(f"  Ignorés : {skipped} (déjà en base)")
    print("=" * 60)
    print("[OK] Import terminé")


if __name__ == "__main__":
    asyncio.run(seed())
