"""
Service Application
===================

Logique métier pour la gestion des appels à candidature et candidatures.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import case, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.application import (
    Application,
    ApplicationCall,
    ApplicationDegree,
    ApplicationDocument,
    CallCoverage,
    CallEligibilityCriteria,
    CallRequiredDocument,
    CallSchedule,
    CallStatus,
    SubmittedApplicationStatus,
)
from app.models.base import PublicationStatus


class ApplicationService:
    """Service pour la gestion des appels à candidature et candidatures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # APPLICATION CALLS
    # =========================================================================

    async def auto_close_expired_calls(self) -> int:
        """
        Ferme automatiquement les appels 'ongoing' dont la deadline est passée.

        Returns:
            Nombre d'appels mis à jour.
        """
        now = datetime.utcnow()
        stmt = (
            update(ApplicationCall)
            .where(
                ApplicationCall.status == CallStatus.ONGOING,
                ApplicationCall.deadline.isnot(None),
                ApplicationCall.deadline < now,
            )
            .values(status=CallStatus.CLOSED)
        )
        result = await self.db.execute(stmt)
        if result.rowcount > 0:
            await self.db.commit()
        return result.rowcount

    async def get_calls(
        self,
        search: str | None = None,
        call_type: str | None = None,
        call_status: CallStatus | None = None,
        publication_status: PublicationStatus | None = None,
        program_id: str | None = None,
        campus_id: str | None = None,
    ) -> select:
        """
        Construit une requête pour lister les appels à candidature.

        Args:
            search: Recherche sur titre ou description.
            call_type: Filtrer par type d'appel.
            call_status: Filtrer par statut de l'appel.
            publication_status: Filtrer par statut de publication.
            program_id: Filtrer par programme.
            campus_id: Filtrer par campus.

        Returns:
            Requête SQLAlchemy Select.
        """
        # Fermer automatiquement les appels expirés avant de lister
        await self.auto_close_expired_calls()

        query = select(ApplicationCall).options(
            selectinload(ApplicationCall.eligibility_criteria),
            selectinload(ApplicationCall.coverage),
            selectinload(ApplicationCall.required_documents),
            selectinload(ApplicationCall.schedule),
        )

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    ApplicationCall.title.ilike(search_filter),
                    ApplicationCall.description.ilike(search_filter),
                )
            )

        if call_type:
            query = query.where(ApplicationCall.type == call_type)

        if call_status:
            query = query.where(ApplicationCall.status == call_status)

        if publication_status:
            query = query.where(ApplicationCall.publication_status == publication_status)

        if program_id:
            query = query.where(ApplicationCall.program_external_id == program_id)

        if campus_id:
            query = query.where(ApplicationCall.campus_external_id == campus_id)

        query = query.order_by(ApplicationCall.created_at.desc(), ApplicationCall.deadline.desc())
        return query

    async def get_published_calls(
        self,
        search: str | None = None,
        call_type: str | None = None,
        call_status: CallStatus | None = None,
        program_id: str | None = None,
        campus_id: str | None = None,
    ) -> select:
        """
        Construit une requête pour lister les appels publiés (public).

        Args:
            search: Recherche sur titre ou description.
            call_type: Filtrer par type d'appel.
            call_status: Filtrer par statut de l'appel.
            program_id: Filtrer par programme.
            campus_id: Filtrer par campus.

        Returns:
            Requête SQLAlchemy Select.
        """
        return await self.get_calls(
            search=search,
            call_type=call_type,
            call_status=call_status,
            publication_status=PublicationStatus.PUBLISHED,
            program_id=program_id,
            campus_id=campus_id,
        )

    async def get_call_by_id(self, call_id: str) -> ApplicationCall | None:
        """Récupère un appel par son ID."""
        query = (
            select(ApplicationCall)
            .options(
                selectinload(ApplicationCall.eligibility_criteria),
                selectinload(ApplicationCall.coverage),
                selectinload(ApplicationCall.required_documents),
                selectinload(ApplicationCall.schedule),
            )
            .where(ApplicationCall.id == call_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_call_by_slug(self, slug: str) -> ApplicationCall | None:
        """Récupère un appel par son slug."""
        query = (
            select(ApplicationCall)
            .options(
                selectinload(ApplicationCall.eligibility_criteria),
                selectinload(ApplicationCall.coverage),
                selectinload(ApplicationCall.required_documents),
                selectinload(ApplicationCall.schedule),
            )
            .where(ApplicationCall.slug == slug)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_call(self, data: dict) -> ApplicationCall:
        """Crée un nouvel appel à candidature."""
        # Vérifier l'unicité du slug
        existing = await self.get_call_by_slug(data.get("slug", ""))
        if existing:
            raise ConflictException("Un appel avec ce slug existe déjà")

        call = ApplicationCall(id=str(uuid4()), **data)
        self.db.add(call)
        await self.db.commit()
        await self.db.refresh(call)
        return await self.get_call_by_id(call.id)

    async def update_call(self, call_id: str, data: dict) -> ApplicationCall:
        """Met à jour un appel à candidature."""
        call = await self.get_call_by_id(call_id)
        if not call:
            raise NotFoundException("Appel non trouvé")

        # Vérifier l'unicité du slug si modifié
        if "slug" in data and data["slug"] != call.slug:
            existing = await self.get_call_by_slug(data["slug"])
            if existing:
                raise ConflictException("Un appel avec ce slug existe déjà")

        for key, value in data.items():
            if hasattr(call, key):
                setattr(call, key, value)

        await self.db.commit()
        await self.db.refresh(call)
        return await self.get_call_by_id(call.id)

    async def delete_call(self, call_id: str) -> bool:
        """Supprime un appel à candidature."""
        call = await self.get_call_by_id(call_id)
        if not call:
            raise NotFoundException("Appel non trouvé")

        await self.db.delete(call)
        await self.db.commit()
        return True

    async def toggle_call_publication(self, call_id: str) -> ApplicationCall:
        """Bascule le statut de publication d'un appel."""
        call = await self.get_call_by_id(call_id)
        if not call:
            raise NotFoundException("Appel non trouvé")

        new_status = (
            PublicationStatus.DRAFT
            if call.publication_status == PublicationStatus.PUBLISHED
            else PublicationStatus.PUBLISHED
        )
        call.publication_status = new_status
        await self.db.commit()
        await self.db.refresh(call)
        return await self.get_call_by_id(call.id)

    async def update_call_status(self, call_id: str, status: CallStatus) -> ApplicationCall:
        """Met à jour le statut d'un appel (ongoing, closed, upcoming)."""
        call = await self.get_call_by_id(call_id)
        if not call:
            raise NotFoundException("Appel non trouvé")

        call.status = status
        await self.db.commit()
        await self.db.refresh(call)
        return await self.get_call_by_id(call.id)

    # =========================================================================
    # ELIGIBILITY CRITERIA
    # =========================================================================

    async def get_criteria_by_id(self, criterion_id: str) -> CallEligibilityCriteria | None:
        """Récupère un critère par son ID."""
        query = select(CallEligibilityCriteria).where(
            CallEligibilityCriteria.id == criterion_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_criterion(self, call_id: str, data: dict) -> CallEligibilityCriteria:
        """Ajoute un critère d'éligibilité à un appel."""
        call = await self.get_call_by_id(call_id)
        if not call:
            raise NotFoundException("Appel non trouvé")

        criterion = CallEligibilityCriteria(
            id=str(uuid4()),
            call_id=call_id,
            **data,
        )
        self.db.add(criterion)
        await self.db.commit()
        await self.db.refresh(criterion)
        return criterion

    async def update_criterion(self, criterion_id: str, data: dict) -> CallEligibilityCriteria:
        """Met à jour un critère d'éligibilité."""
        criterion = await self.get_criteria_by_id(criterion_id)
        if not criterion:
            raise NotFoundException("Critère non trouvé")

        for key, value in data.items():
            if hasattr(criterion, key):
                setattr(criterion, key, value)

        await self.db.commit()
        await self.db.refresh(criterion)
        return criterion

    async def delete_criterion(self, criterion_id: str) -> bool:
        """Supprime un critère d'éligibilité."""
        criterion = await self.get_criteria_by_id(criterion_id)
        if not criterion:
            raise NotFoundException("Critère non trouvé")

        await self.db.delete(criterion)
        await self.db.commit()
        return True

    # =========================================================================
    # COVERAGE
    # =========================================================================

    async def get_coverage_by_id(self, coverage_id: str) -> CallCoverage | None:
        """Récupère une prise en charge par son ID."""
        query = select(CallCoverage).where(CallCoverage.id == coverage_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_coverage(self, call_id: str, data: dict) -> CallCoverage:
        """Ajoute une prise en charge à un appel."""
        call = await self.get_call_by_id(call_id)
        if not call:
            raise NotFoundException("Appel non trouvé")

        coverage = CallCoverage(
            id=str(uuid4()),
            call_id=call_id,
            **data,
        )
        self.db.add(coverage)
        await self.db.commit()
        await self.db.refresh(coverage)
        return coverage

    async def update_coverage(self, coverage_id: str, data: dict) -> CallCoverage:
        """Met à jour une prise en charge."""
        coverage = await self.get_coverage_by_id(coverage_id)
        if not coverage:
            raise NotFoundException("Prise en charge non trouvée")

        for key, value in data.items():
            if hasattr(coverage, key):
                setattr(coverage, key, value)

        await self.db.commit()
        await self.db.refresh(coverage)
        return coverage

    async def delete_coverage(self, coverage_id: str) -> bool:
        """Supprime une prise en charge."""
        coverage = await self.get_coverage_by_id(coverage_id)
        if not coverage:
            raise NotFoundException("Prise en charge non trouvée")

        await self.db.delete(coverage)
        await self.db.commit()
        return True

    # =========================================================================
    # REQUIRED DOCUMENTS
    # =========================================================================

    async def get_required_document_by_id(self, document_id: str) -> CallRequiredDocument | None:
        """Récupère un document requis par son ID."""
        query = select(CallRequiredDocument).where(CallRequiredDocument.id == document_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_required_document(self, call_id: str, data: dict) -> CallRequiredDocument:
        """Ajoute un document requis à un appel."""
        call = await self.get_call_by_id(call_id)
        if not call:
            raise NotFoundException("Appel non trouvé")

        document = CallRequiredDocument(
            id=str(uuid4()),
            call_id=call_id,
            **data,
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def update_required_document(self, document_id: str, data: dict) -> CallRequiredDocument:
        """Met à jour un document requis."""
        document = await self.get_required_document_by_id(document_id)
        if not document:
            raise NotFoundException("Document requis non trouvé")

        for key, value in data.items():
            if hasattr(document, key):
                setattr(document, key, value)

        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def delete_required_document(self, document_id: str) -> bool:
        """Supprime un document requis."""
        document = await self.get_required_document_by_id(document_id)
        if not document:
            raise NotFoundException("Document requis non trouvé")

        await self.db.delete(document)
        await self.db.commit()
        return True

    # =========================================================================
    # SCHEDULE
    # =========================================================================

    async def get_schedule_by_id(self, schedule_id: str) -> CallSchedule | None:
        """Récupère une étape du calendrier par son ID."""
        query = select(CallSchedule).where(CallSchedule.id == schedule_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_schedule(self, call_id: str, data: dict) -> CallSchedule:
        """Ajoute une étape au calendrier d'un appel."""
        call = await self.get_call_by_id(call_id)
        if not call:
            raise NotFoundException("Appel non trouvé")

        schedule = CallSchedule(
            id=str(uuid4()),
            call_id=call_id,
            **data,
        )
        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    async def update_schedule(self, schedule_id: str, data: dict) -> CallSchedule:
        """Met à jour une étape du calendrier."""
        schedule = await self.get_schedule_by_id(schedule_id)
        if not schedule:
            raise NotFoundException("Étape non trouvée")

        for key, value in data.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)

        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    async def delete_schedule(self, schedule_id: str) -> bool:
        """Supprime une étape du calendrier."""
        schedule = await self.get_schedule_by_id(schedule_id)
        if not schedule:
            raise NotFoundException("Étape non trouvée")

        await self.db.delete(schedule)
        await self.db.commit()
        return True

    # =========================================================================
    # APPLICATIONS
    # =========================================================================

    def _generate_reference_number(self) -> str:
        """Génère un numéro de référence unique pour une candidature."""
        import random
        import string
        from datetime import datetime

        year = datetime.now().year
        random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"APP-{year}-{random_part}"

    async def get_applications(
        self,
        search: str | None = None,
        call_id: str | None = None,
        status: SubmittedApplicationStatus | None = None,
        program_id: str | None = None,
    ) -> select:
        """
        Construit une requête pour lister les candidatures.

        Args:
            search: Recherche sur nom, prénom, email ou référence.
            call_id: Filtrer par appel.
            status: Filtrer par statut.
            program_id: Filtrer par programme.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(Application).options(
            selectinload(Application.degrees),
            selectinload(Application.documents),
        )

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Application.reference_number.ilike(search_filter),
                    Application.last_name.ilike(search_filter),
                    Application.first_name.ilike(search_filter),
                    Application.email.ilike(search_filter),
                )
            )

        if call_id:
            query = query.where(Application.call_id == call_id)

        if status:
            query = query.where(Application.status == status)

        if program_id:
            query = query.where(Application.program_external_id == program_id)

        query = query.order_by(Application.submitted_at.desc())
        return query

    async def get_application_by_id(self, application_id: str) -> Application | None:
        """Récupère une candidature par son ID."""
        query = (
            select(Application)
            .options(
                selectinload(Application.degrees),
                selectinload(Application.documents),
            )
            .where(Application.id == application_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_application_by_reference(self, reference: str) -> Application | None:
        """Récupère une candidature par son numéro de référence."""
        query = (
            select(Application)
            .options(
                selectinload(Application.degrees),
                selectinload(Application.documents),
            )
            .where(Application.reference_number == reference)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_application(self, data: dict) -> Application:
        """Crée une nouvelle candidature."""
        # Extraire les données imbriquées
        degrees_data = data.pop("degrees", [])
        documents_data = data.pop("documents", [])

        # Générer un numéro de référence unique
        reference = self._generate_reference_number()
        while await self.get_application_by_reference(reference):
            reference = self._generate_reference_number()

        application = Application(
            id=str(uuid4()),
            reference_number=reference,
            **data,
        )
        self.db.add(application)
        await self.db.flush()

        # Ajouter les diplômes
        for degree_data in degrees_data:
            degree = ApplicationDegree(
                id=str(uuid4()),
                application_id=application.id,
                **degree_data,
            )
            self.db.add(degree)

        # Ajouter les documents
        for doc_data in documents_data:
            doc = ApplicationDocument(
                id=str(uuid4()),
                application_id=application.id,
                **doc_data,
            )
            self.db.add(doc)

        await self.db.commit()
        return await self.get_application_by_id(application.id)

    async def update_application(self, application_id: str, data: dict) -> Application:
        """Met à jour une candidature."""
        application = await self.get_application_by_id(application_id)
        if not application:
            raise NotFoundException("Candidature non trouvée")

        for key, value in data.items():
            if hasattr(application, key):
                setattr(application, key, value)

        await self.db.commit()
        await self.db.refresh(application)
        return await self.get_application_by_id(application.id)

    async def update_application_status(
        self,
        application_id: str,
        status: SubmittedApplicationStatus,
        review_notes: str | None = None,
        review_score: float | None = None,
        reviewer_id: str | None = None,
    ) -> Application:
        """Met à jour le statut d'une candidature."""
        application = await self.get_application_by_id(application_id)
        if not application:
            raise NotFoundException("Candidature non trouvée")

        application.status = status
        if review_notes is not None:
            application.review_notes = review_notes
        if review_score is not None:
            application.review_score = review_score
        if reviewer_id:
            application.reviewer_external_id = reviewer_id
            application.reviewed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(application)
        return await self.get_application_by_id(application.id)

    async def delete_application(self, application_id: str) -> bool:
        """Supprime une candidature."""
        application = await self.get_application_by_id(application_id)
        if not application:
            raise NotFoundException("Candidature non trouvée")

        await self.db.delete(application)
        await self.db.commit()
        return True

    # =========================================================================
    # APPLICATION DEGREES
    # =========================================================================

    async def get_degree_by_id(self, degree_id: str) -> ApplicationDegree | None:
        """Récupère un diplôme par son ID."""
        query = select(ApplicationDegree).where(ApplicationDegree.id == degree_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add_degree(self, application_id: str, data: dict) -> ApplicationDegree:
        """Ajoute un diplôme à une candidature."""
        application = await self.get_application_by_id(application_id)
        if not application:
            raise NotFoundException("Candidature non trouvée")

        degree = ApplicationDegree(
            id=str(uuid4()),
            application_id=application_id,
            **data,
        )
        self.db.add(degree)
        await self.db.commit()
        await self.db.refresh(degree)
        return degree

    async def update_degree(self, degree_id: str, data: dict) -> ApplicationDegree:
        """Met à jour un diplôme."""
        degree = await self.get_degree_by_id(degree_id)
        if not degree:
            raise NotFoundException("Diplôme non trouvé")

        for key, value in data.items():
            if hasattr(degree, key):
                setattr(degree, key, value)

        await self.db.commit()
        await self.db.refresh(degree)
        return degree

    async def delete_degree(self, degree_id: str) -> bool:
        """Supprime un diplôme."""
        degree = await self.get_degree_by_id(degree_id)
        if not degree:
            raise NotFoundException("Diplôme non trouvé")

        await self.db.delete(degree)
        await self.db.commit()
        return True

    # =========================================================================
    # APPLICATION DOCUMENTS
    # =========================================================================

    async def get_document_by_id(self, document_id: str) -> ApplicationDocument | None:
        """Récupère un document par son ID."""
        query = select(ApplicationDocument).where(ApplicationDocument.id == document_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add_document(self, application_id: str, data: dict) -> ApplicationDocument:
        """Ajoute un document à une candidature."""
        application = await self.get_application_by_id(application_id)
        if not application:
            raise NotFoundException("Candidature non trouvée")

        document = ApplicationDocument(
            id=str(uuid4()),
            application_id=application_id,
            **data,
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def update_document(self, document_id: str, data: dict) -> ApplicationDocument:
        """Met à jour un document."""
        document = await self.get_document_by_id(document_id)
        if not document:
            raise NotFoundException("Document non trouvé")

        for key, value in data.items():
            if hasattr(document, key):
                setattr(document, key, value)

        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def validate_document(
        self,
        document_id: str,
        is_valid: bool,
        comment: str | None = None,
    ) -> ApplicationDocument:
        """Valide ou invalide un document."""
        document = await self.get_document_by_id(document_id)
        if not document:
            raise NotFoundException("Document non trouvé")

        document.is_valid = is_valid
        document.validation_comment = comment
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def delete_document(self, document_id: str) -> bool:
        """Supprime un document."""
        document = await self.get_document_by_id(document_id)
        if not document:
            raise NotFoundException("Document non trouvé")

        await self.db.delete(document)
        await self.db.commit()
        return True

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_application_statistics(self, call_id: str | None = None) -> dict:
        """Récupère les statistiques des candidatures."""
        base_query = select(func.count(Application.id))

        if call_id:
            base_query = base_query.where(Application.call_id == call_id)

        # Total
        total_result = await self.db.execute(base_query)
        total = total_result.scalar() or 0

        # Par statut
        stats = {"total": total}
        for status in SubmittedApplicationStatus:
            query = base_query.where(Application.status == status)
            result = await self.db.execute(query)
            stats[status.value] = result.scalar() or 0

        return stats

    # =========================================================================
    # EXTENDED STATISTICS
    # =========================================================================

    async def get_extended_statistics(
        self,
        call_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        granularity: str = "month",
    ) -> dict:
        """Récupère les statistiques étendues des candidatures."""
        from datetime import date

        # 1. Stats de base par statut avec filtres de date
        base_stats = await self._get_status_counts(call_id, date_from, date_to)

        # 2. KPIs calculés
        total = base_stats["total"]
        pending = base_stats.get("submitted", 0) + base_stats.get("under_review", 0)
        decided = (
            base_stats.get("accepted", 0)
            + base_stats.get("rejected", 0)
            + base_stats.get("waitlisted", 0)
        )
        acceptance_rate = (
            round((base_stats.get("accepted", 0) / decided * 100), 1) if decided > 0 else 0
        )
        incomplete = base_stats.get("incomplete", 0)
        completion_rate = (
            round(((total - incomplete) / total * 100), 1) if total > 0 else 0
        )

        # 3. Timeline
        timeline = await self._get_timeline_stats(call_id, date_from, date_to, granularity)

        # 4. Par programme (via ApplicationCall.title comme proxy)
        by_program = await self._get_stats_by_program(call_id, date_from, date_to)

        # 5. Par appel
        by_call = await self._get_stats_by_call(date_from, date_to)

        return {
            "total": total,
            "pending": pending,
            "acceptance_rate": acceptance_rate,
            "completion_rate": completion_rate,
            "by_status": {
                "submitted": base_stats.get("submitted", 0),
                "under_review": base_stats.get("under_review", 0),
                "accepted": base_stats.get("accepted", 0),
                "rejected": base_stats.get("rejected", 0),
                "waitlisted": base_stats.get("waitlisted", 0),
                "incomplete": base_stats.get("incomplete", 0),
            },
            "timeline": timeline,
            "by_program": by_program,
            "by_call": by_call,
        }

    async def _get_status_counts(
        self,
        call_id: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> dict:
        """Comptages par statut avec filtres de date."""
        base_query = select(func.count(Application.id))

        if call_id:
            base_query = base_query.where(Application.call_id == call_id)
        if date_from:
            base_query = base_query.where(Application.submitted_at >= date_from)
        if date_to:
            base_query = base_query.where(Application.submitted_at <= date_to)

        # Total
        total_result = await self.db.execute(base_query)
        total = total_result.scalar() or 0

        # Par statut
        stats = {"total": total}
        for status in SubmittedApplicationStatus:
            query = base_query.where(Application.status == status)
            result = await self.db.execute(query)
            stats[status.value] = result.scalar() or 0

        return stats

    async def _get_timeline_stats(
        self,
        call_id: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        granularity: str,
    ) -> list[dict]:
        """Évolution temporelle des candidatures."""
        from sqlalchemy import text

        # Déterminer le format de troncature selon la granularité
        trunc_format = {
            "day": "day",
            "week": "week",
            "month": "month",
        }.get(granularity, "month")

        # Expression date_trunc réutilisable
        date_trunc_expr = func.date_trunc(trunc_format, Application.submitted_at)

        # Requête avec GROUP BY date_trunc
        query = select(
            func.to_char(
                date_trunc_expr,
                "YYYY-MM" if trunc_format == "month" else "YYYY-MM-DD",
            ).label("period"),
            func.count(Application.id).label("count"),
        )

        if call_id:
            query = query.where(Application.call_id == call_id)
        if date_from:
            query = query.where(Application.submitted_at >= date_from)
        if date_to:
            query = query.where(Application.submitted_at <= date_to)

        # GROUP BY et ORDER BY avec la même expression
        query = query.group_by(date_trunc_expr).order_by(date_trunc_expr)

        result = await self.db.execute(query)
        rows = result.all()

        return [{"period": row.period, "count": row.count} for row in rows if row.period]

    async def _get_stats_by_program(
        self,
        call_id: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list[dict]:
        """Statistiques groupées par programme (via ApplicationCall.title)."""
        # Requête avec JOIN sur ApplicationCall
        query = (
            select(
                ApplicationCall.id.label("program_id"),
                ApplicationCall.title.label("program_title"),
                func.count(Application.id).label("total"),
                func.sum(
                    case(
                        (Application.status == SubmittedApplicationStatus.ACCEPTED, 1),
                        else_=0,
                    )
                ).label("accepted"),
            )
            .select_from(Application)
            .join(ApplicationCall, Application.call_id == ApplicationCall.id)
        )

        if call_id:
            query = query.where(Application.call_id == call_id)
        if date_from:
            query = query.where(Application.submitted_at >= date_from)
        if date_to:
            query = query.where(Application.submitted_at <= date_to)

        query = query.group_by(ApplicationCall.id, ApplicationCall.title).order_by(
            func.count(Application.id).desc()
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "program_id": row.program_id,
                "program_title": row.program_title,
                "total": row.total,
                "accepted": row.accepted or 0,
                "acceptance_rate": (
                    round((row.accepted or 0) / row.total * 100, 1) if row.total > 0 else 0
                ),
            }
            for row in rows
        ]

    async def _get_stats_by_call(
        self,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list[dict]:
        """Statistiques détaillées par appel."""
        # Sous-requêtes pour compter chaque statut avec case()
        query = (
            select(
                ApplicationCall.id.label("call_id"),
                ApplicationCall.title.label("call_title"),
                func.count(Application.id).label("total"),
                func.sum(
                    case(
                        (Application.status == SubmittedApplicationStatus.SUBMITTED, 1),
                        else_=0,
                    )
                ).label("submitted"),
                func.sum(
                    case(
                        (Application.status == SubmittedApplicationStatus.UNDER_REVIEW, 1),
                        else_=0,
                    )
                ).label("under_review"),
                func.sum(
                    case(
                        (Application.status == SubmittedApplicationStatus.ACCEPTED, 1),
                        else_=0,
                    )
                ).label("accepted"),
                func.sum(
                    case(
                        (Application.status == SubmittedApplicationStatus.REJECTED, 1),
                        else_=0,
                    )
                ).label("rejected"),
                func.sum(
                    case(
                        (Application.status == SubmittedApplicationStatus.WAITLISTED, 1),
                        else_=0,
                    )
                ).label("waitlisted"),
                func.sum(
                    case(
                        (Application.status == SubmittedApplicationStatus.INCOMPLETE, 1),
                        else_=0,
                    )
                ).label("incomplete"),
            )
            .select_from(Application)
            .join(ApplicationCall, Application.call_id == ApplicationCall.id)
        )

        if date_from:
            query = query.where(Application.submitted_at >= date_from)
        if date_to:
            query = query.where(Application.submitted_at <= date_to)

        query = query.group_by(ApplicationCall.id, ApplicationCall.title).order_by(
            func.count(Application.id).desc()
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "call_id": row.call_id,
                "call_title": row.call_title,
                "total": row.total,
                "submitted": row.submitted or 0,
                "under_review": row.under_review or 0,
                "accepted": row.accepted or 0,
                "rejected": row.rejected or 0,
                "waitlisted": row.waitlisted or 0,
                "incomplete": row.incomplete or 0,
            }
            for row in rows
        ]
