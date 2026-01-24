"""
Service Project
===============

Logique métier pour la gestion des projets institutionnels.
"""

from decimal import Decimal
from uuid import uuid4

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.base import PublicationStatus
from app.models.organization import ProjectStatus
from app.models.project import (
    Project,
    ProjectCall,
    ProjectCallStatus,
    ProjectCategory,
    ProjectCategoryLink,
    ProjectCountry,
    ProjectMediaLibrary,
    ProjectPartner,
)


class ProjectService:
    """Service pour la gestion des projets institutionnels."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # CATEGORIES
    # =========================================================================

    async def get_categories(
        self,
        search: str | None = None,
    ) -> select:
        """Construit une requête pour lister les catégories."""
        query = select(ProjectCategory)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    ProjectCategory.name.ilike(search_filter),
                    ProjectCategory.slug.ilike(search_filter),
                )
            )

        query = query.order_by(ProjectCategory.name)
        return query

    async def get_category_by_id(self, category_id: str) -> ProjectCategory | None:
        """Récupère une catégorie par son ID."""
        result = await self.db.execute(
            select(ProjectCategory).where(ProjectCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_category_by_slug(self, slug: str) -> ProjectCategory | None:
        """Récupère une catégorie par son slug."""
        result = await self.db.execute(
            select(ProjectCategory).where(ProjectCategory.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_category(
        self, name: str, slug: str, **kwargs
    ) -> ProjectCategory:
        """Crée une nouvelle catégorie."""
        existing = await self.get_category_by_slug(slug)
        if existing:
            raise ConflictException(f"Une catégorie avec le slug '{slug}' existe déjà")

        category = ProjectCategory(
            id=str(uuid4()),
            name=name,
            slug=slug,
            **kwargs,
        )
        self.db.add(category)
        await self.db.flush()
        return category

    async def update_category(
        self, category_id: str, **kwargs
    ) -> ProjectCategory:
        """Met à jour une catégorie."""
        category = await self.get_category_by_id(category_id)
        if not category:
            raise NotFoundException("Catégorie non trouvée")

        if "slug" in kwargs and kwargs["slug"] != category.slug:
            existing = await self.get_category_by_slug(kwargs["slug"])
            if existing:
                raise ConflictException(
                    f"Une catégorie avec le slug '{kwargs['slug']}' existe déjà"
                )

        await self.db.execute(
            update(ProjectCategory)
            .where(ProjectCategory.id == category_id)
            .values(**kwargs)
        )
        await self.db.flush()
        return await self.get_category_by_id(category_id)

    async def delete_category(self, category_id: str) -> None:
        """Supprime une catégorie."""
        category = await self.get_category_by_id(category_id)
        if not category:
            raise NotFoundException("Catégorie non trouvée")

        await self.db.execute(
            delete(ProjectCategory).where(ProjectCategory.id == category_id)
        )
        await self.db.flush()

    # =========================================================================
    # PROJECTS
    # =========================================================================

    async def get_projects(
        self,
        search: str | None = None,
        status: ProjectStatus | None = None,
        publication_status: PublicationStatus | None = None,
        category_id: str | None = None,
        department_external_id: str | None = None,
    ) -> select:
        """Construit une requête pour lister les projets."""
        query = select(Project).options(selectinload(Project.categories))

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Project.title.ilike(search_filter),
                    Project.summary.ilike(search_filter),
                )
            )

        if status:
            query = query.where(Project.status == status)

        if publication_status:
            query = query.where(Project.publication_status == publication_status)

        if category_id:
            query = query.join(ProjectCategoryLink).where(
                ProjectCategoryLink.category_id == category_id
            )

        if department_external_id:
            query = query.where(
                Project.department_external_id == department_external_id
            )

        query = query.order_by(Project.created_at.desc())
        return query

    async def get_project_by_id(self, project_id: str) -> Project | None:
        """Récupère un projet par son ID."""
        result = await self.db.execute(
            select(Project)
            .options(
                selectinload(Project.categories),
                selectinload(Project.countries),
                selectinload(Project.partners),
                selectinload(Project.calls),
                selectinload(Project.media_library),
            )
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_project_by_slug(self, slug: str) -> Project | None:
        """Récupère un projet par son slug."""
        result = await self.db.execute(
            select(Project)
            .options(
                selectinload(Project.categories),
                selectinload(Project.countries),
                selectinload(Project.partners),
                selectinload(Project.calls),
            )
            .where(Project.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_project(
        self,
        title: str,
        slug: str,
        category_ids: list[str] | None = None,
        country_ids: list[str] | None = None,
        **kwargs,
    ) -> Project:
        """Crée un nouveau projet."""
        existing = await self.get_project_by_slug(slug)
        if existing:
            raise ConflictException(f"Un projet avec le slug '{slug}' existe déjà")

        project = Project(
            id=str(uuid4()),
            title=title,
            slug=slug,
            **kwargs,
        )
        self.db.add(project)
        await self.db.flush()

        # Ajouter les catégories
        if category_ids:
            for cat_id in category_ids:
                link = ProjectCategoryLink(project_id=project.id, category_id=cat_id)
                self.db.add(link)

        # Ajouter les pays
        if country_ids:
            for country_id in country_ids:
                country = ProjectCountry(
                    project_id=project.id, country_external_id=country_id
                )
                self.db.add(country)

        await self.db.flush()
        return await self.get_project_by_id(project.id)

    async def update_project(
        self,
        project_id: str,
        category_ids: list[str] | None = None,
        country_ids: list[str] | None = None,
        **kwargs,
    ) -> Project:
        """Met à jour un projet."""
        project = await self.get_project_by_id(project_id)
        if not project:
            raise NotFoundException("Projet non trouvé")

        if "slug" in kwargs and kwargs["slug"] != project.slug:
            existing = await self.get_project_by_slug(kwargs["slug"])
            if existing:
                raise ConflictException(
                    f"Un projet avec le slug '{kwargs['slug']}' existe déjà"
                )

        await self.db.execute(
            update(Project).where(Project.id == project_id).values(**kwargs)
        )

        # Mettre à jour les catégories si spécifiées
        if category_ids is not None:
            await self.db.execute(
                delete(ProjectCategoryLink).where(
                    ProjectCategoryLink.project_id == project_id
                )
            )
            for cat_id in category_ids:
                link = ProjectCategoryLink(project_id=project_id, category_id=cat_id)
                self.db.add(link)

        # Mettre à jour les pays si spécifiés
        if country_ids is not None:
            await self.db.execute(
                delete(ProjectCountry).where(ProjectCountry.project_id == project_id)
            )
            for country_id in country_ids:
                country = ProjectCountry(
                    project_id=project_id, country_external_id=country_id
                )
                self.db.add(country)

        await self.db.flush()
        return await self.get_project_by_id(project_id)

    async def delete_project(self, project_id: str) -> None:
        """Supprime un projet."""
        project = await self.get_project_by_id(project_id)
        if not project:
            raise NotFoundException("Projet non trouvé")

        await self.db.execute(delete(Project).where(Project.id == project_id))
        await self.db.flush()

    async def publish_project(self, project_id: str) -> Project:
        """Publie un projet."""
        project = await self.get_project_by_id(project_id)
        if not project:
            raise NotFoundException("Projet non trouvé")

        await self.db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(publication_status=PublicationStatus.PUBLISHED)
        )
        await self.db.flush()
        return await self.get_project_by_id(project_id)

    async def unpublish_project(self, project_id: str) -> Project:
        """Dépublie un projet."""
        project = await self.get_project_by_id(project_id)
        if not project:
            raise NotFoundException("Projet non trouvé")

        await self.db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(publication_status=PublicationStatus.DRAFT)
        )
        await self.db.flush()
        return await self.get_project_by_id(project_id)

    # =========================================================================
    # PROJECT PARTNERS
    # =========================================================================

    async def add_partner(
        self,
        project_id: str,
        partner_external_id: str,
        partner_role: str | None = None,
    ) -> ProjectPartner:
        """Ajoute un partenaire à un projet."""
        project = await self.get_project_by_id(project_id)
        if not project:
            raise NotFoundException("Projet non trouvé")

        # Vérifier si le partenaire existe déjà
        result = await self.db.execute(
            select(ProjectPartner).where(
                ProjectPartner.project_id == project_id,
                ProjectPartner.partner_external_id == partner_external_id,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException("Ce partenaire est déjà associé au projet")

        partner = ProjectPartner(
            project_id=project_id,
            partner_external_id=partner_external_id,
            partner_role=partner_role,
        )
        self.db.add(partner)
        await self.db.flush()
        return partner

    async def update_partner(
        self,
        project_id: str,
        partner_external_id: str,
        partner_role: str | None = None,
    ) -> ProjectPartner:
        """Met à jour un partenaire de projet."""
        result = await self.db.execute(
            select(ProjectPartner).where(
                ProjectPartner.project_id == project_id,
                ProjectPartner.partner_external_id == partner_external_id,
            )
        )
        partner = result.scalar_one_or_none()
        if not partner:
            raise NotFoundException("Partenaire non trouvé pour ce projet")

        await self.db.execute(
            update(ProjectPartner)
            .where(
                ProjectPartner.project_id == project_id,
                ProjectPartner.partner_external_id == partner_external_id,
            )
            .values(partner_role=partner_role)
        )
        await self.db.flush()

        result = await self.db.execute(
            select(ProjectPartner).where(
                ProjectPartner.project_id == project_id,
                ProjectPartner.partner_external_id == partner_external_id,
            )
        )
        return result.scalar_one()

    async def remove_partner(
        self, project_id: str, partner_external_id: str
    ) -> None:
        """Retire un partenaire d'un projet."""
        result = await self.db.execute(
            select(ProjectPartner).where(
                ProjectPartner.project_id == project_id,
                ProjectPartner.partner_external_id == partner_external_id,
            )
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Partenaire non trouvé pour ce projet")

        await self.db.execute(
            delete(ProjectPartner).where(
                ProjectPartner.project_id == project_id,
                ProjectPartner.partner_external_id == partner_external_id,
            )
        )
        await self.db.flush()

    async def get_project_partners(self, project_id: str) -> list[ProjectPartner]:
        """Récupère les partenaires d'un projet."""
        result = await self.db.execute(
            select(ProjectPartner).where(ProjectPartner.project_id == project_id)
        )
        return list(result.scalars().all())

    # =========================================================================
    # PROJECT CALLS
    # =========================================================================

    async def get_calls(
        self,
        project_id: str | None = None,
        status: ProjectCallStatus | None = None,
    ) -> select:
        """Construit une requête pour lister les appels."""
        query = select(ProjectCall)

        if project_id:
            query = query.where(ProjectCall.project_id == project_id)

        if status:
            query = query.where(ProjectCall.status == status)

        query = query.order_by(ProjectCall.deadline.asc().nullslast())
        return query

    async def get_call_by_id(self, call_id: str) -> ProjectCall | None:
        """Récupère un appel par son ID."""
        result = await self.db.execute(
            select(ProjectCall)
            .options(selectinload(ProjectCall.project))
            .where(ProjectCall.id == call_id)
        )
        return result.scalar_one_or_none()

    async def create_call(
        self, project_id: str, title: str, **kwargs
    ) -> ProjectCall:
        """Crée un nouvel appel pour un projet."""
        project = await self.get_project_by_id(project_id)
        if not project:
            raise NotFoundException("Projet non trouvé")

        call = ProjectCall(
            id=str(uuid4()),
            project_id=project_id,
            title=title,
            **kwargs,
        )
        self.db.add(call)
        await self.db.flush()
        return call

    async def update_call(self, call_id: str, **kwargs) -> ProjectCall:
        """Met à jour un appel."""
        call = await self.get_call_by_id(call_id)
        if not call:
            raise NotFoundException("Appel non trouvé")

        await self.db.execute(
            update(ProjectCall).where(ProjectCall.id == call_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_call_by_id(call_id)

    async def delete_call(self, call_id: str) -> None:
        """Supprime un appel."""
        call = await self.get_call_by_id(call_id)
        if not call:
            raise NotFoundException("Appel non trouvé")

        await self.db.execute(delete(ProjectCall).where(ProjectCall.id == call_id))
        await self.db.flush()

    # =========================================================================
    # PROJECT MEDIA LIBRARY
    # =========================================================================

    async def add_album(
        self, project_id: str, album_external_id: str
    ) -> ProjectMediaLibrary:
        """Ajoute un album à la médiathèque d'un projet."""
        project = await self.get_project_by_id(project_id)
        if not project:
            raise NotFoundException("Projet non trouvé")

        # Vérifier si l'album existe déjà
        result = await self.db.execute(
            select(ProjectMediaLibrary).where(
                ProjectMediaLibrary.project_id == project_id,
                ProjectMediaLibrary.album_external_id == album_external_id,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException("Cet album est déjà dans la médiathèque")

        media = ProjectMediaLibrary(
            project_id=project_id,
            album_external_id=album_external_id,
        )
        self.db.add(media)
        await self.db.flush()
        return media

    async def remove_album(
        self, project_id: str, album_external_id: str
    ) -> None:
        """Retire un album de la médiathèque d'un projet."""
        result = await self.db.execute(
            select(ProjectMediaLibrary).where(
                ProjectMediaLibrary.project_id == project_id,
                ProjectMediaLibrary.album_external_id == album_external_id,
            )
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Album non trouvé dans la médiathèque")

        await self.db.execute(
            delete(ProjectMediaLibrary).where(
                ProjectMediaLibrary.project_id == project_id,
                ProjectMediaLibrary.album_external_id == album_external_id,
            )
        )
        await self.db.flush()

    async def get_project_albums(
        self, project_id: str
    ) -> list[ProjectMediaLibrary]:
        """Récupère les albums d'un projet."""
        result = await self.db.execute(
            select(ProjectMediaLibrary).where(
                ProjectMediaLibrary.project_id == project_id
            )
        )
        return list(result.scalars().all())

    # =========================================================================
    # PUBLIC ACCESS
    # =========================================================================

    async def get_public_projects(
        self,
        search: str | None = None,
        status: ProjectStatus | None = None,
        category_slug: str | None = None,
    ) -> select:
        """Récupère les projets publiés."""
        query = (
            select(Project)
            .options(selectinload(Project.categories))
            .where(Project.publication_status == PublicationStatus.PUBLISHED)
        )

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Project.title.ilike(search_filter),
                    Project.summary.ilike(search_filter),
                )
            )

        if status:
            query = query.where(Project.status == status)

        if category_slug:
            query = query.join(ProjectCategoryLink).join(ProjectCategory).where(
                ProjectCategory.slug == category_slug
            )

        query = query.order_by(Project.created_at.desc())
        return query

    async def get_public_project_by_slug(self, slug: str) -> Project | None:
        """Récupère un projet publié par son slug."""
        result = await self.db.execute(
            select(Project)
            .options(
                selectinload(Project.categories),
                selectinload(Project.partners),
                selectinload(Project.calls),
            )
            .where(
                Project.slug == slug,
                Project.publication_status == PublicationStatus.PUBLISHED,
            )
        )
        return result.scalar_one_or_none()

    async def get_public_calls(
        self, status: ProjectCallStatus | None = None
    ) -> list[ProjectCall]:
        """Récupère les appels publics (projets publiés uniquement)."""
        query = (
            select(ProjectCall)
            .join(Project)
            .where(Project.publication_status == PublicationStatus.PUBLISHED)
        )

        if status:
            query = query.where(ProjectCall.status == status)

        query = query.order_by(ProjectCall.deadline.asc().nullslast())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_statistics(self) -> dict:
        """Calcule les statistiques globales des projets."""
        # Total projets
        total_result = await self.db.execute(select(func.count(Project.id)))
        total_projects = total_result.scalar() or 0

        # Par statut
        ongoing_result = await self.db.execute(
            select(func.count(Project.id)).where(
                Project.status == ProjectStatus.ONGOING
            )
        )
        ongoing_projects = ongoing_result.scalar() or 0

        completed_result = await self.db.execute(
            select(func.count(Project.id)).where(
                Project.status == ProjectStatus.COMPLETED
            )
        )
        completed_projects = completed_result.scalar() or 0

        planned_result = await self.db.execute(
            select(func.count(Project.id)).where(
                Project.status == ProjectStatus.PLANNED
            )
        )
        planned_projects = planned_result.scalar() or 0

        suspended_result = await self.db.execute(
            select(func.count(Project.id)).where(
                Project.status == ProjectStatus.SUSPENDED
            )
        )
        suspended_projects = suspended_result.scalar() or 0

        # Budget total
        budget_result = await self.db.execute(
            select(func.sum(Project.budget)).where(Project.budget.isnot(None))
        )
        total_budget = budget_result.scalar() or Decimal("0")

        # Total catégories
        categories_result = await self.db.execute(
            select(func.count(ProjectCategory.id))
        )
        total_categories = categories_result.scalar() or 0

        return {
            "total_projects": total_projects,
            "ongoing_projects": ongoing_projects,
            "completed_projects": completed_projects,
            "planned_projects": planned_projects,
            "suspended_projects": suspended_projects,
            "total_budget": total_budget,
            "total_categories": total_categories,
        }
