#!/usr/bin/env python3
"""
Seed script : Candidatures (Applications)
=========================================
Crée des données de simulation pour les candidatures,
liées aux appels à candidatures existants.

Prérequis:
  - Exécuter d'abord :
    1. python scripts/seed_countries.py
    2. python scripts/seed_programs.py
    3. python scripts/seed_application_calls.py

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_applications.py
"""

import asyncio
import random
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select

from app.database import async_session_maker
from app.models.academic import Program
from app.models.application import (
    Application,
    ApplicationCall,
    ApplicationDegree,
    ApplicationDocument,
    CallRequiredDocument,
    EmploymentStatus,
    ExperienceDuration,
    MaritalStatus,
    SubmittedApplicationStatus,
)
from app.models.base import Salutation
from app.models.core import Country


# =============================================================================
# DONNÉES RÉALISTES
# =============================================================================

FIRST_NAMES_MALE = [
    "Amadou", "Mamadou", "Moussa", "Ibrahima", "Abdoulaye", "Ousmane", "Cheikh",
    "Samba", "Modou", "Aliou", "Boubacar", "Souleymane", "Ismaïla", "Pape",
    "Jean-Pierre", "François", "Patrick", "Christian", "Emmanuel", "Joseph",
    "Kofi", "Kwame", "Yao", "Koffi", "Kodjo", "Kouassi", "Issa", "Dramane",
]

FIRST_NAMES_FEMALE = [
    "Fatou", "Aminata", "Mariama", "Aïssatou", "Ndeye", "Khady", "Awa",
    "Coumba", "Dieynaba", "Bineta", "Adama", "Rama", "Sokhna", "Mame",
    "Marie", "Jeanne", "Cécile", "Thérèse", "Béatrice", "Claire",
    "Adjoa", "Akosua", "Ama", "Abena", "Akua", "Adjoua", "Fanta", "Kadiatou",
]

LAST_NAMES = [
    "Diallo", "Ba", "Diop", "Ndiaye", "Sow", "Fall", "Mbaye", "Gueye",
    "Sarr", "Sy", "Diouf", "Kane", "Faye", "Thiam", "Cissé", "Traoré",
    "Coulibaly", "Konaté", "Keita", "Touré", "Camara", "Koné", "Diabaté",
    "Ouattara", "Sanogo", "Bamba", "Doumbia", "Sidibé", "Sanou", "Zongo",
    "Nguema", "Obiang", "Mba", "Ndong", "Nze", "Essono", "Ondo",
    "Kouamé", "Koffi", "Yao", "Kouakou", "Konan", "N'Guessan", "Aka",
    "Ouédraogo", "Sawadogo", "Compaoré", "Ilboudo", "Kaboré", "Tapsoba",
]

# Villes par code ISO pays (utilisé pour générer des données cohérentes)
CITIES_BY_ISO = {
    "SN": ["Dakar", "Saint-Louis", "Thiès", "Ziguinchor", "Kaolack"],
    "ML": ["Bamako", "Sikasso", "Ségou", "Mopti", "Kayes"],
    "CI": ["Abidjan", "Bouaké", "Yamoussoukro", "Daloa", "San-Pédro"],
    "BF": ["Ouagadougou", "Bobo-Dioulasso", "Koudougou", "Banfora"],
    "GN": ["Conakry", "Kankan", "Kindia", "Nzérékoré"],
    "TG": ["Lomé", "Sokodé", "Kara", "Kpalimé"],
    "BJ": ["Cotonou", "Porto-Novo", "Parakou", "Abomey"],
    "NE": ["Niamey", "Zinder", "Maradi", "Tahoua"],
    "GA": ["Libreville", "Port-Gentil", "Franceville"],
    "CM": ["Douala", "Yaoundé", "Garoua", "Bamenda", "Maroua"],
    "CD": ["Kinshasa", "Lubumbashi", "Goma", "Kisangani"],
    "MG": ["Antananarivo", "Toamasina", "Fianarantsoa", "Mahajanga"],
    "MA": ["Casablanca", "Rabat", "Marrakech", "Fès"],
    "DZ": ["Alger", "Oran", "Constantine", "Annaba"],
    "TN": ["Tunis", "Sfax", "Sousse", "Kairouan"],
}

UNIVERSITIES = [
    "Université Cheikh Anta Diop de Dakar",
    "Université Gaston Berger de Saint-Louis",
    "Université Félix Houphouët-Boigny d'Abidjan",
    "Université de Ouagadougou",
    "Université de Bamako",
    "Université Omar Bongo de Libreville",
    "Université de Yaoundé I",
    "Université de Kinshasa",
    "Université Marien Ngouabi de Brazzaville",
    "Université d'Antananarivo",
    "École Nationale d'Administration",
    "Institut Polytechnique",
    "École Supérieure de Commerce",
]

DEGREE_TITLES = [
    ("Licence en Économie", "Économie"),
    ("Licence en Droit", "Droit"),
    ("Licence en Administration Publique", "Administration"),
    ("Licence en Sciences Politiques", "Sciences Politiques"),
    ("Maîtrise en Gestion", "Gestion"),
    ("Maîtrise en Finance", "Finance"),
    ("Master 1 en Développement Durable", "Développement Durable"),
    ("Master 1 en Gouvernance", "Gouvernance"),
    ("Master en Management de Projet", "Management"),
    ("Diplôme d'Ingénieur", "Ingénierie"),
]

EMPLOYERS = [
    ("Ministère de l'Économie et des Finances", "Analyste financier"),
    ("Ministère de l'Environnement", "Chargé de programme"),
    ("Banque Centrale", "Économiste"),
    ("Agence de Développement", "Chef de projet"),
    ("Programme des Nations Unies pour le Développement", "Consultant"),
    ("Banque Mondiale - Bureau Pays", "Spécialiste"),
    ("Organisation Internationale de la Francophonie", "Coordinateur"),
    ("ONG Internationale", "Responsable de programme"),
    ("Cabinet de Conseil", "Consultant senior"),
    ("Université", "Assistant de recherche"),
    ("Collectivité locale", "Directeur de service"),
    ("Entreprise privée", "Responsable administratif"),
]


def generate_reference_number(index: int) -> str:
    """Génère un numéro de référence unique."""
    year = datetime.now().year
    return f"USENGHOR-{year}-{index:05d}"


def generate_email(first_name: str, last_name: str) -> str:
    """Génère une adresse email."""
    domains = ["gmail.com", "yahoo.fr", "outlook.com", "hotmail.com"]
    first = first_name.lower().replace("é", "e").replace("è", "e").replace("ï", "i").replace("ô", "o")
    last = last_name.lower().replace("é", "e").replace("è", "e")
    return f"{first}.{last}@{random.choice(domains)}"


def generate_phone(phone_code: str) -> str:
    """Génère un numéro de téléphone."""
    return f"{phone_code} {random.randint(60, 79)} {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}"


async def seed():
    """Insère les données de seed pour les candidatures."""
    async with async_session_maker() as db:
        # ================================================================
        # 1. Vérifier les prérequis
        # ================================================================

        # Récupérer les pays
        countries_result = await db.execute(select(Country).where(Country.active == True))
        countries = countries_result.scalars().all()

        if not countries:
            print("[ERREUR] Aucun pays trouvé.")
            print("         Exécutez d'abord : python scripts/seed_countries.py")
            return

        # Créer un mapping ISO -> Country pour faciliter l'accès
        countries_by_iso = {c.iso_code: c for c in countries}
        # Liste des pays africains francophones (principaux)
        african_iso_codes = ["SN", "ML", "CI", "BF", "GN", "TG", "BJ", "NE", "GA", "CM", "CD", "MG", "MA", "DZ", "TN"]
        african_countries = [countries_by_iso[iso] for iso in african_iso_codes if iso in countries_by_iso]

        if not african_countries:
            print("[ERREUR] Pays africains non trouvés.")
            return

        print(f"[OK] {len(countries)} pays trouvés ({len(african_countries)} pays africains)")

        # Récupérer les programmes
        programs_result = await db.execute(select(Program))
        programs = programs_result.scalars().all()

        if not programs:
            print("[ERREUR] Aucun programme trouvé.")
            print("         Exécutez d'abord : python scripts/seed_programs.py")
            return

        print(f"[OK] {len(programs)} programmes trouvés")

        # Vérifier que des appels existent
        calls_result = await db.execute(select(ApplicationCall))
        calls = calls_result.scalars().all()

        if not calls:
            print("[ERREUR] Aucun appel à candidature trouvé.")
            print("         Exécutez d'abord : python scripts/seed_application_calls.py")
            return

        print(f"[OK] {len(calls)} appels à candidatures trouvés")

        # Vérifier si des candidatures existent déjà
        existing_count = (
            await db.execute(select(func.count(Application.id)))
        ).scalar_one()

        if existing_count > 0:
            print(f"[SKIP] {existing_count} candidatures existent déjà. Seed ignoré.")
            return

        # Récupérer les documents requis par appel
        docs_by_call = {}
        for call in calls:
            docs_result = await db.execute(
                select(CallRequiredDocument).where(CallRequiredDocument.call_id == call.id)
            )
            docs_by_call[call.id] = docs_result.scalars().all()

        # ================================================================
        # 2. Créer les candidatures
        # ================================================================
        now = datetime.now(timezone.utc)
        created_applications = []
        ref_index = 1

        # Distribution des statuts
        statuses_distribution = [
            (SubmittedApplicationStatus.SUBMITTED, 8),
            (SubmittedApplicationStatus.UNDER_REVIEW, 6),
            (SubmittedApplicationStatus.ACCEPTED, 4),
            (SubmittedApplicationStatus.REJECTED, 3),
            (SubmittedApplicationStatus.WAITLISTED, 2),
            (SubmittedApplicationStatus.INCOMPLETE, 2),
        ]

        # Appels publiés uniquement
        usable_calls = [c for c in calls if c.publication_status.value == "published"]
        if not usable_calls:
            usable_calls = calls[:3]

        for status, count in statuses_distribution:
            for i in range(count):
                # Sélectionner un appel et un programme aléatoires
                call = random.choice(usable_calls)
                program = random.choice(programs)

                # Sélectionner un pays aléatoire
                country = random.choice(african_countries)
                cities = CITIES_BY_ISO.get(country.iso_code, ["Capitale"])
                city = random.choice(cities)
                birth_city = random.choice(cities)

                # Déterminer le genre et les informations personnelles
                is_male = random.choice([True, False])
                first_name = random.choice(FIRST_NAMES_MALE if is_male else FIRST_NAMES_FEMALE)
                last_name = random.choice(LAST_NAMES)
                salutation = random.choice([Salutation.MR, Salutation.DR, Salutation.PR]) if is_male else random.choice([Salutation.MRS, Salutation.DR, Salutation.PR])

                # Dates
                age = random.randint(25, 40)
                birth_year = datetime.now().year - age
                birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28))

                # Calculer submitted_at en fonction du status
                if status == SubmittedApplicationStatus.SUBMITTED:
                    submitted_at = now - timedelta(days=random.randint(1, 10))
                elif status in [SubmittedApplicationStatus.UNDER_REVIEW, SubmittedApplicationStatus.INCOMPLETE]:
                    submitted_at = now - timedelta(days=random.randint(10, 30))
                else:
                    submitted_at = now - timedelta(days=random.randint(30, 90))

                reviewed_at = None
                review_notes = None
                review_score = None

                if status not in [SubmittedApplicationStatus.SUBMITTED, SubmittedApplicationStatus.INCOMPLETE]:
                    reviewed_at = submitted_at + timedelta(days=random.randint(5, 20))

                    if status == SubmittedApplicationStatus.ACCEPTED:
                        review_score = Decimal(str(round(random.uniform(75, 95), 2)))
                        review_notes = "Excellent profil. Candidature retenue."
                    elif status == SubmittedApplicationStatus.REJECTED:
                        review_score = Decimal(str(round(random.uniform(30, 55), 2)))
                        review_notes = "Profil ne correspondant pas aux critères d'éligibilité."
                    elif status == SubmittedApplicationStatus.WAITLISTED:
                        review_score = Decimal(str(round(random.uniform(60, 74), 2)))
                        review_notes = "Bon profil. Placé sur liste d'attente."
                    elif status == SubmittedApplicationStatus.UNDER_REVIEW:
                        review_notes = "Dossier en cours d'examen par le comité."

                if status == SubmittedApplicationStatus.INCOMPLETE:
                    review_notes = "Documents manquants : CV et lettre de motivation."

                # Informations professionnelles
                has_work_exp = random.choice([True, True, True, False])
                employer_data = random.choice(EMPLOYERS) if has_work_exp else (None, None)
                experience_dur = random.choice(list(ExperienceDuration)) if has_work_exp else None

                # Créer la candidature
                application = Application(
                    id=str(uuid4()),
                    reference_number=generate_reference_number(ref_index),
                    call_id=call.id,
                    program_external_id=program.id,

                    # Informations personnelles
                    salutation=salutation,
                    last_name=last_name,
                    first_name=first_name,
                    birth_date=birth_date,
                    birth_city=birth_city,
                    birth_country_external_id=country.id,
                    nationality_external_id=country.id,
                    country_external_id=country.id,
                    marital_status=random.choice(list(MaritalStatus)),
                    employment_status=random.choice([
                        EmploymentStatus.CIVIL_SERVANT,
                        EmploymentStatus.PRIVATE_EMPLOYEE,
                        EmploymentStatus.TEACHER,
                        EmploymentStatus.NGO_EMPLOYEE,
                        EmploymentStatus.STUDENT,
                    ]) if not has_work_exp else random.choice([
                        EmploymentStatus.CIVIL_SERVANT,
                        EmploymentStatus.PRIVATE_EMPLOYEE,
                        EmploymentStatus.TEACHER,
                        EmploymentStatus.NGO_EMPLOYEE,
                    ]),

                    # Coordonnées
                    address=f"{random.randint(1, 500)} Rue {random.choice(['de la Paix', 'Principale', 'du Commerce', 'de la Liberté'])}",
                    city=city,
                    postal_code=str(random.randint(10000, 99999)),
                    phone=generate_phone(country.phone_code or "+221"),
                    phone_whatsapp=generate_phone(country.phone_code or "+221"),
                    email=generate_email(first_name, last_name),

                    # Informations professionnelles
                    has_work_experience=has_work_exp,
                    current_job=employer_data[1] if has_work_exp else None,
                    job_title=employer_data[1] if has_work_exp else None,
                    employer_name=employer_data[0] if has_work_exp else None,
                    employer_address=f"BP {random.randint(100, 9999)}, {city}" if has_work_exp else None,
                    employer_city=city if has_work_exp else None,
                    employer_country_external_id=country.id if has_work_exp else None,
                    employer_phone=generate_phone(country.phone_code or "+221") if has_work_exp else None,
                    employer_email=f"contact@{employer_data[0].lower().replace(' ', '').replace('-', '')[:10]}.org" if has_work_exp and employer_data[0] else None,
                    experience_duration=experience_dur,

                    # Formation académique
                    highest_degree_level="Bac+4" if random.random() > 0.3 else "Bac+5",
                    highest_degree_title=random.choice(DEGREE_TITLES)[0],
                    degree_date=date(datetime.now().year - random.randint(2, 8), 6, 30),
                    degree_location=random.choice(UNIVERSITIES),

                    # Statut
                    status=status,
                    submitted_at=submitted_at,
                    reviewed_at=reviewed_at,
                    review_notes=review_notes,
                    review_score=review_score,
                )

                db.add(application)
                await db.flush()
                created_applications.append((application, call.id, country))
                ref_index += 1

        print(f"[OK] {len(created_applications)} candidatures créées")

        # ================================================================
        # 3. Ajouter des diplômes à chaque candidature
        # ================================================================
        degrees_count = 0
        for app, call_id, country in created_applications:
            num_degrees = random.randint(1, 3)

            for order in range(1, num_degrees + 1):
                degree_info = random.choice(DEGREE_TITLES)
                year = datetime.now().year - random.randint(2, 10) - (order * 2)

                # Choisir un pays pour le diplôme (même pays ou autre)
                degree_country = country if random.random() > 0.3 else random.choice(african_countries)
                degree_cities = CITIES_BY_ISO.get(degree_country.iso_code, ["Capitale"])

                degree = ApplicationDegree(
                    id=str(uuid4()),
                    application_id=app.id,
                    title=degree_info[0],
                    year=year,
                    institution=random.choice(UNIVERSITIES),
                    city=random.choice(degree_cities),
                    country_external_id=degree_country.id,
                    specialization=degree_info[1],
                    honors=random.choice(["Passable", "Assez Bien", "Bien", "Très Bien", None]),
                    display_order=order,
                )
                db.add(degree)
                degrees_count += 1

        print(f"[OK] {degrees_count} diplômes ajoutés")

        # ================================================================
        # 4. Ajouter des documents à certaines candidatures
        # ================================================================
        documents_count = 0
        for app, call_id, country in created_applications:
            required_docs = docs_by_call.get(call_id, [])

            if not required_docs:
                generic_docs = [
                    ("CV", True),
                    ("Lettre de motivation", True),
                    ("Copie des diplômes", True),
                    ("Photo d'identité", False),
                ]

                if app.status == SubmittedApplicationStatus.INCOMPLETE:
                    docs_to_add = generic_docs[:1]
                else:
                    docs_to_add = generic_docs[:random.randint(2, 4)]

                for doc_name, _ in docs_to_add:
                    if app.status == SubmittedApplicationStatus.ACCEPTED:
                        is_valid = True
                        comment = "Document conforme"
                    elif app.status == SubmittedApplicationStatus.REJECTED:
                        is_valid = random.choice([True, False])
                        comment = "Document non conforme" if not is_valid else None
                    elif app.status == SubmittedApplicationStatus.INCOMPLETE:
                        is_valid = None
                        comment = None
                    else:
                        is_valid = None
                        comment = None

                    doc = ApplicationDocument(
                        id=str(uuid4()),
                        application_id=app.id,
                        document_name=doc_name,
                        required_document_id=None,
                        media_external_id=str(uuid4()),
                        is_valid=is_valid,
                        validation_comment=comment,
                    )
                    db.add(doc)
                    documents_count += 1
            else:
                if app.status == SubmittedApplicationStatus.INCOMPLETE:
                    docs_to_use = required_docs[:1]
                else:
                    docs_to_use = required_docs[:random.randint(len(required_docs) // 2, len(required_docs))]

                for req_doc in docs_to_use:
                    if app.status == SubmittedApplicationStatus.ACCEPTED:
                        is_valid = True
                        comment = "Document conforme"
                    elif app.status == SubmittedApplicationStatus.REJECTED:
                        is_valid = random.choice([True, False])
                        comment = "Document non conforme" if not is_valid else None
                    else:
                        is_valid = None
                        comment = None

                    doc = ApplicationDocument(
                        id=str(uuid4()),
                        application_id=app.id,
                        document_name=req_doc.document_name,
                        required_document_id=req_doc.id,
                        media_external_id=str(uuid4()),
                        is_valid=is_valid,
                        validation_comment=comment,
                    )
                    db.add(doc)
                    documents_count += 1

        print(f"[OK] {documents_count} documents ajoutés")

        # ================================================================
        # Commit final
        # ================================================================
        await db.commit()

        # Statistiques par statut
        stats = {}
        for app, _, _ in created_applications:
            status_name = app.status.value
            stats[status_name] = stats.get(status_name, 0) + 1

        print()
        print("=" * 50)
        print("Seed des candidatures terminé avec succès !")
        print("=" * 50)
        print(f"  Candidatures créées : {len(created_applications)}")
        print(f"  Diplômes ajoutés    : {degrees_count}")
        print(f"  Documents ajoutés   : {documents_count}")
        print()
        print("  Répartition par statut :")
        for status_name, count in sorted(stats.items()):
            print(f"    - {status_name}: {count}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
