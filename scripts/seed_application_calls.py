#!/usr/bin/env python3
"""
Seed script : Appels à candidatures
====================================
Crée des données de simulation pour les appels à candidatures,
ainsi qu'un utilisateur admin avec les permissions nécessaires.

Usage:
  cd usenghor_backend
  source .venv/bin/activate
  python scripts/seed_application_calls.py
"""

import asyncio
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.security import get_password_hash
from app.database import async_session_maker, engine
from app.models.application import (
    ApplicationCall,
    CallCoverage,
    CallEligibilityCriteria,
    CallRequiredDocument,
    CallSchedule,
    CallStatus,
    CallType,
)
from app.models.base import PublicationStatus
from app.models.identity import Permission, Role, RolePermission, User, UserRole


async def seed():
    """Insère les données de seed."""
    async with async_session_maker() as db:
        # ================================================================
        # 1. Utilisateur admin + rôle + permissions
        # ================================================================
        existing_user = (
            await db.execute(select(User).where(User.email == "admin@usenghor.org"))
        ).scalar_one_or_none()

        if existing_user:
            admin_user = existing_user
            print("[OK] Utilisateur admin existant trouvé")
        else:
            # Permissions applications
            perm_codes = ["applications.view", "applications.create", "applications.edit", "applications.delete"]
            app_perms = []
            for code in perm_codes:
                existing_perm = (
                    await db.execute(select(Permission).where(Permission.code == code))
                ).scalar_one_or_none()
                if existing_perm:
                    app_perms.append(existing_perm)
                else:
                    perm = Permission(
                        id=str(uuid4()),
                        code=code,
                        name_fr=f"Candidatures - {code.split('.')[-1]}",
                        category="applications",
                    )
                    db.add(perm)
                    app_perms.append(perm)

            await db.flush()

            # Rôle super_admin
            existing_role = (
                await db.execute(select(Role).where(Role.code == "super_admin"))
            ).scalar_one_or_none()

            if existing_role:
                role = existing_role
            else:
                role = Role(
                    id=str(uuid4()),
                    code="super_admin",
                    name_fr="Super Administrateur",
                    hierarchy_level=100,
                    active=True,
                )
                db.add(role)
                await db.flush()

                for perm in app_perms:
                    db.add(RolePermission(role_id=role.id, permission_id=perm.id))

            # Utilisateur admin
            admin_user = User(
                id=str(uuid4()),
                email="admin@usenghor.org",
                password_hash=get_password_hash("Admin123!"),
                last_name="Admin",
                first_name="Super",
                active=True,
                email_verified=True,
            )
            db.add(admin_user)
            await db.flush()

            db.add(UserRole(user_id=admin_user.id, role_id=role.id))
            await db.flush()
            print("[OK] Utilisateur admin créé : admin@usenghor.org / Admin123!")

        # ================================================================
        # 2. Vérifier si des appels existent déjà
        # ================================================================
        existing_calls = (
            await db.execute(select(ApplicationCall).limit(1))
        ).scalar_one_or_none()

        if existing_calls:
            print("[SKIP] Des appels à candidatures existent déjà. Seed ignoré.")
            await db.commit()
            return

        # ================================================================
        # 3. Créer les appels à candidatures
        # ================================================================
        now = datetime.now(timezone.utc)

        calls_data = [
            # --- 1. Application ongoing published (avec tous les sous-entités) ---
            {
                "title": "Appel à candidatures Master Développement 2025-2026",
                "slug": "master-developpement-2025-2026",
                "description": "L'Université Senghor lance un appel à candidatures pour le programme de Master en Développement pour l'année académique 2025-2026. Ce programme est destiné aux cadres africains souhaitant approfondir leurs compétences en gestion du développement durable, gouvernance et administration publique.",
                "type": CallType.APPLICATION,
                "status": CallStatus.ONGOING,
                "opening_date": date(2025, 1, 15),
                "deadline": now + timedelta(days=45),
                "program_start_date": date(2025, 9, 15),
                "program_end_date": date(2027, 6, 30),
                "target_audience": "Cadres africains titulaires d'un Bac+4 minimum avec 2 ans d'expérience professionnelle",
                "registration_fee": Decimal("50.00"),
                "currency": "EUR",
                "use_internal_form": True,
                "publication_status": PublicationStatus.PUBLISHED,
            },
            # --- 2. Scholarship ongoing published ---
            {
                "title": "Bourse d'excellence Senghor 2025",
                "slug": "bourse-excellence-senghor-2025",
                "description": "Programme de bourses d'excellence pour les étudiants méritants d'Afrique francophone. La bourse couvre les frais de scolarité, l'hébergement et une allocation mensuelle.",
                "type": CallType.SCHOLARSHIP,
                "status": CallStatus.ONGOING,
                "opening_date": date(2025, 2, 1),
                "deadline": now + timedelta(days=30),
                "program_start_date": date(2025, 9, 1),
                "program_end_date": date(2026, 6, 30),
                "target_audience": "Étudiants africains francophones avec mention Bien ou Très Bien au dernier diplôme",
                "registration_fee": Decimal("0"),
                "currency": "EUR",
                "use_internal_form": True,
                "publication_status": PublicationStatus.PUBLISHED,
            },
            # --- 3. Recruitment upcoming published ---
            {
                "title": "Recrutement Enseignants-Chercheurs 2025",
                "slug": "recrutement-enseignants-chercheurs-2025",
                "description": "L'Université Senghor recrute des enseignants-chercheurs dans les domaines du développement durable, de la gouvernance et de la gestion du patrimoine culturel.",
                "type": CallType.RECRUITMENT,
                "status": CallStatus.UPCOMING,
                "opening_date": date(2025, 3, 1),
                "deadline": now + timedelta(days=90),
                "target_audience": "Docteurs en sciences du développement, gouvernance ou disciplines connexes avec publications",
                "registration_fee": Decimal("0"),
                "currency": "EUR",
                "use_internal_form": False,
                "external_form_url": "https://forms.usenghor.org/recrutement-2025",
                "publication_status": PublicationStatus.PUBLISHED,
            },
            # --- 4. Project ongoing published ---
            {
                "title": "Appel à projets Innovation Africaine 2025",
                "slug": "appel-projets-innovation-africaine-2025",
                "description": "Appel à projets pour soutenir les initiatives innovantes en faveur du développement durable en Afrique. Financement de 5 000 à 20 000 EUR par projet.",
                "type": CallType.PROJECT,
                "status": CallStatus.ONGOING,
                "opening_date": date(2025, 1, 1),
                "deadline": now + timedelta(days=15),
                "target_audience": "Entrepreneurs, chercheurs et organisations africaines porteurs de projets innovants",
                "registration_fee": Decimal("25.00"),
                "currency": "USD",
                "use_internal_form": True,
                "publication_status": PublicationStatus.PUBLISHED,
            },
            # --- 5. Training upcoming published ---
            {
                "title": "Formation continue en Gestion de Projets",
                "slug": "formation-continue-gestion-projets-2025",
                "description": "Programme de formation continue de 3 mois en gestion de projets de développement. Formation en présentiel à Alexandrie avec modules pratiques.",
                "type": CallType.TRAINING,
                "status": CallStatus.UPCOMING,
                "opening_date": date(2025, 4, 1),
                "deadline": now + timedelta(days=60),
                "program_start_date": date(2025, 6, 1),
                "program_end_date": date(2025, 8, 31),
                "target_audience": "Professionnels du développement souhaitant renforcer leurs compétences en gestion de projets",
                "registration_fee": Decimal("500.00"),
                "currency": "EUR",
                "use_internal_form": True,
                "publication_status": PublicationStatus.PUBLISHED,
            },
            # --- 6. Application closed published ---
            {
                "title": "Master Patrimoine Culturel 2024-2025",
                "slug": "master-patrimoine-culturel-2024-2025",
                "description": "Programme de Master en Gestion du Patrimoine Culturel pour l'année académique 2024-2025. Cet appel est désormais clôturé.",
                "type": CallType.APPLICATION,
                "status": CallStatus.CLOSED,
                "opening_date": date(2024, 1, 15),
                "deadline": now - timedelta(days=60),
                "program_start_date": date(2024, 9, 15),
                "program_end_date": date(2026, 6, 30),
                "target_audience": "Cadres africains spécialisés en patrimoine culturel et industries créatives",
                "registration_fee": Decimal("50.00"),
                "currency": "EUR",
                "use_internal_form": True,
                "publication_status": PublicationStatus.PUBLISHED,
            },
            # --- 7. Scholarship upcoming draft ---
            {
                "title": "Bourse de recherche doctorale 2025",
                "slug": "bourse-recherche-doctorale-2025",
                "description": "Bourses de recherche pour les doctorants africains dans les domaines prioritaires de l'université. En cours de rédaction.",
                "type": CallType.SCHOLARSHIP,
                "status": CallStatus.UPCOMING,
                "opening_date": date(2025, 5, 1),
                "deadline": now + timedelta(days=120),
                "target_audience": "Doctorants africains inscrits dans une université partenaire",
                "registration_fee": Decimal("0"),
                "currency": "EUR",
                "use_internal_form": True,
                "publication_status": PublicationStatus.DRAFT,
            },
            # --- 8. Application closed archived ---
            {
                "title": "Master Administration Publique 2023-2024",
                "slug": "master-admin-publique-2023-2024-archive",
                "description": "Programme archivé - Master en Administration Publique pour l'année 2023-2024.",
                "type": CallType.APPLICATION,
                "status": CallStatus.CLOSED,
                "opening_date": date(2023, 6, 1),
                "deadline": now - timedelta(days=365),
                "program_start_date": date(2023, 9, 15),
                "program_end_date": date(2025, 6, 30),
                "target_audience": "Fonctionnaires et cadres du secteur public africain",
                "registration_fee": Decimal("75.00"),
                "currency": "EUR",
                "use_internal_form": True,
                "publication_status": PublicationStatus.ARCHIVED,
            },
        ]

        created_calls = []
        for data in calls_data:
            # Ne PAS passer les colonnes UUID nullables (cover_image_external_id,
            # program_external_id, campus_external_id) - elles seront NULL par défaut.
            # Passer None explicitement cause une erreur asyncpg de type inference
            # (asyncpg infère VARCHAR au lieu de UUID pour les valeurs None).
            call = ApplicationCall(
                id=str(uuid4()),
                created_by_external_id=str(admin_user.id),  # Convertir en string pour éviter type inference
                **data,
            )
            db.add(call)
            await db.flush()
            created_calls.append(call)

        print(f"[OK] {len(created_calls)} appels à candidatures créés")

        # ================================================================
        # 4. Sous-entités pour l'appel 1 (Master Développement) - COMPLET
        # ================================================================
        call_0 = created_calls[0]

        # Critères d'éligibilité
        criteria_0 = [
            ("Être ressortissant d'un pays africain", True, 1),
            ("Être titulaire d'un diplôme Bac+4 minimum (Maîtrise, Master 1 ou équivalent)", True, 2),
            ("Avoir au moins 2 ans d'expérience professionnelle après l'obtention du diplôme", True, 3),
            ("Maîtrise du français (niveau B2 minimum, certificat requis pour les non-francophones)", True, 4),
            ("Avoir moins de 40 ans à la date de clôture de l'appel", True, 5),
            ("Lettre de recommandation de l'employeur actuel ou d'un ancien employeur", False, 6),
        ]
        for criterion, mandatory, order in criteria_0:
            db.add(CallEligibilityCriteria(
                id=str(uuid4()), call_id=call_0.id,
                criterion=criterion, is_mandatory=mandatory, display_order=order,
            ))

        # Prises en charge
        coverage_0 = [
            ("Frais de scolarité", "Prise en charge complète des frais de formation pour les 2 années", 1),
            ("Hébergement", "Logement en chambre individuelle sur le campus universitaire d'Alexandrie", 2),
            ("Allocation mensuelle", "Allocation de 300 EUR/mois pour les frais de vie courante", 3),
            ("Billet d'avion", "Aller-retour en classe économique pays d'origine - Alexandrie", 4),
            ("Assurance maladie", "Couverture santé complète pendant toute la durée du programme", 5),
        ]
        for item, desc, order in coverage_0:
            db.add(CallCoverage(
                id=str(uuid4()), call_id=call_0.id,
                item=item, description=desc, display_order=order,
            ))

        # Documents requis
        documents_0 = [
            ("CV détaillé", "Curriculum vitae actualisé en français", True, "pdf", 5, 1),
            ("Lettre de motivation", "Maximum 2 pages, expliquant le projet professionnel", True, "pdf", 2, 2),
            ("Copie des diplômes", "Copies certifiées conformes de tous les diplômes universitaires", True, "pdf,jpg", 10, 3),
            ("Relevés de notes", "Tous les relevés de notes depuis le Baccalauréat", True, "pdf", 15, 4),
            ("Lettre de recommandation", "De l'employeur actuel ou d'un professeur universitaire", False, "pdf", 5, 5),
            ("Photo d'identité", "Format passeport, fond blanc, récente (moins de 6 mois)", True, "jpg,png", 2, 6),
            ("Copie du passeport", "Pages d'identité en cours de validité", True, "pdf,jpg", 5, 7),
            ("Certificat de langue", "DELF B2 ou équivalent pour les non-francophones", False, "pdf", 5, 8),
        ]
        for name, desc, mandatory, formats, max_size, order in documents_0:
            db.add(CallRequiredDocument(
                id=str(uuid4()), call_id=call_0.id,
                document_name=name, description=desc, is_mandatory=mandatory,
                accepted_formats=formats, max_size_mb=max_size, display_order=order,
            ))

        # Calendrier
        schedule_0 = [
            ("Ouverture des candidatures", date(2025, 1, 15), date(2025, 1, 15), "Début de la réception des dossiers en ligne", 1),
            ("Date limite de dépôt", date(2025, 3, 15), date(2025, 3, 15), "Dernier jour pour soumettre un dossier complet", 2),
            ("Présélection sur dossier", date(2025, 4, 1), date(2025, 4, 30), "Examen des dossiers par le comité de sélection", 3),
            ("Entretiens de sélection", date(2025, 5, 15), date(2025, 5, 30), "Entretiens en visioconférence avec les candidats présélectionnés", 4),
            ("Publication des résultats", date(2025, 6, 15), date(2025, 6, 15), "Annonce officielle des candidats retenus", 5),
            ("Rentrée académique", date(2025, 9, 15), date(2025, 9, 15), "Début des cours sur le campus d'Alexandrie", 6),
        ]
        for step, start, end, desc, order in schedule_0:
            db.add(CallSchedule(
                id=str(uuid4()), call_id=call_0.id,
                step=step, start_date=start, end_date=end,
                description=desc, display_order=order,
            ))

        print(f"  -> Appel 1 : 6 critères, 5 couvertures, 8 documents, 6 étapes")

        # ================================================================
        # 5. Sous-entités pour l'appel 2 (Bourse d'excellence)
        # ================================================================
        call_1 = created_calls[1]

        criteria_1 = [
            ("Être ressortissant d'un pays africain francophone", True, 1),
            ("Être titulaire d'un Bac+3 minimum avec mention Bien ou Très Bien", True, 2),
            ("Avoir moins de 35 ans à la date de clôture", True, 3),
            ("Ne pas bénéficier d'une autre bourse pour la même période", True, 4),
        ]
        for criterion, mandatory, order in criteria_1:
            db.add(CallEligibilityCriteria(
                id=str(uuid4()), call_id=call_1.id,
                criterion=criterion, is_mandatory=mandatory, display_order=order,
            ))

        coverage_1 = [
            ("Frais de scolarité", "Exonération totale des frais de formation", 1),
            ("Allocation mensuelle", "500 EUR/mois pendant la durée de la formation", 2),
            ("Billet d'avion", "Aller-retour en classe économique", 3),
            ("Assurance maladie", "Couverture santé complète", 4),
        ]
        for item, desc, order in coverage_1:
            db.add(CallCoverage(
                id=str(uuid4()), call_id=call_1.id,
                item=item, description=desc, display_order=order,
            ))

        documents_1 = [
            ("CV", "Curriculum vitae actualisé", True, "pdf", 5, 1),
            ("Lettre de motivation", "Détailler le projet d'études et professionnel", True, "pdf", 3, 2),
            ("Relevés de notes", "Tous les relevés universitaires", True, "pdf", 15, 3),
            ("Copie des diplômes", "Copies certifiées", True, "pdf,jpg", 10, 4),
        ]
        for name, desc, mandatory, formats, max_size, order in documents_1:
            db.add(CallRequiredDocument(
                id=str(uuid4()), call_id=call_1.id,
                document_name=name, description=desc, is_mandatory=mandatory,
                accepted_formats=formats, max_size_mb=max_size, display_order=order,
            ))

        print(f"  -> Appel 2 : 4 critères, 4 couvertures, 4 documents")

        # ================================================================
        # 6. Sous-entités pour l'appel 4 (Innovation Africaine)
        # ================================================================
        call_3 = created_calls[3]

        criteria_3 = [
            ("Le porteur du projet doit être un ressortissant africain", True, 1),
            ("Le projet doit contribuer au développement durable en Afrique", True, 2),
            ("Le projet doit être à un stade de prototype ou de phase pilote", True, 3),
            ("Budget prévisionnel détaillé requis", True, 4),
            ("Partenariat avec une institution locale est un plus", False, 5),
        ]
        for criterion, mandatory, order in criteria_3:
            db.add(CallEligibilityCriteria(
                id=str(uuid4()), call_id=call_3.id,
                criterion=criterion, is_mandatory=mandatory, display_order=order,
            ))

        documents_3 = [
            ("Fiche projet", "Description complète du projet (max 10 pages)", True, "pdf", 10, 1),
            ("Budget prévisionnel", "Détail des postes de dépenses", True, "pdf,xlsx", 5, 2),
            ("CV du porteur", "CV du responsable principal du projet", True, "pdf", 5, 3),
            ("Lettres de soutien", "Lettres d'institutions partenaires", False, "pdf", 10, 4),
        ]
        for name, desc, mandatory, formats, max_size, order in documents_3:
            db.add(CallRequiredDocument(
                id=str(uuid4()), call_id=call_3.id,
                document_name=name, description=desc, is_mandatory=mandatory,
                accepted_formats=formats, max_size_mb=max_size, display_order=order,
            ))

        schedule_3 = [
            ("Dépôt des projets", date(2025, 1, 1), date(2025, 2, 28), "Soumission des dossiers en ligne", 1),
            ("Évaluation par les pairs", date(2025, 3, 1), date(2025, 3, 31), "Évaluation par un comité d'experts", 2),
            ("Annonce des lauréats", date(2025, 4, 15), date(2025, 4, 15), "Publication des projets retenus", 3),
            ("Démarrage des projets", date(2025, 5, 1), date(2025, 5, 1), "Versement de la première tranche de financement", 4),
        ]
        for step, start, end, desc, order in schedule_3:
            db.add(CallSchedule(
                id=str(uuid4()), call_id=call_3.id,
                step=step, start_date=start, end_date=end,
                description=desc, display_order=order,
            ))

        print(f"  -> Appel 4 : 5 critères, 4 documents, 4 étapes")

        # ================================================================
        # 7. Sous-entités pour l'appel 5 (Formation continue)
        # ================================================================
        call_4 = created_calls[4]

        criteria_4 = [
            ("Être titulaire d'un Bac+3 minimum", True, 1),
            ("Avoir au moins 1 an d'expérience en gestion de projets", True, 2),
            ("Maîtrise du français oral et écrit", True, 3),
        ]
        for criterion, mandatory, order in criteria_4:
            db.add(CallEligibilityCriteria(
                id=str(uuid4()), call_id=call_4.id,
                criterion=criterion, is_mandatory=mandatory, display_order=order,
            ))

        documents_4 = [
            ("CV", "Curriculum vitae à jour", True, "pdf", 5, 1),
            ("Lettre de motivation", "Préciser les attentes de la formation", True, "pdf", 3, 2),
            ("Attestation employeur", "Autorisation de l'employeur pour suivre la formation", False, "pdf", 5, 3),
        ]
        for name, desc, mandatory, formats, max_size, order in documents_4:
            db.add(CallRequiredDocument(
                id=str(uuid4()), call_id=call_4.id,
                document_name=name, description=desc, is_mandatory=mandatory,
                accepted_formats=formats, max_size_mb=max_size, display_order=order,
            ))

        schedule_4 = [
            ("Inscription", date(2025, 4, 1), date(2025, 5, 15), "Période d'inscription en ligne", 1),
            ("Confirmation des places", date(2025, 5, 20), date(2025, 5, 20), "Notification d'admission", 2),
            ("Début de la formation", date(2025, 6, 1), date(2025, 6, 1), "Rentrée sur le campus d'Alexandrie", 3),
            ("Fin de la formation", date(2025, 8, 31), date(2025, 8, 31), "Remise des certificats", 4),
        ]
        for step, start, end, desc, order in schedule_4:
            db.add(CallSchedule(
                id=str(uuid4()), call_id=call_4.id,
                step=step, start_date=start, end_date=end,
                description=desc, display_order=order,
            ))

        print(f"  -> Appel 5 : 3 critères, 3 documents, 4 étapes")

        # ================================================================
        # Commit final
        # ================================================================
        await db.commit()

        print()
        print("=" * 50)
        print("Seed terminé avec succès !")
        print("=" * 50)
        print(f"  Appels créés       : {len(created_calls)}")
        print(f"  Utilisateur admin  : admin@usenghor.org")
        print(f"  Mot de passe       : Admin123!")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
