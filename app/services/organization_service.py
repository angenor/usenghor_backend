"""
Service Organization
====================

Logique métier pour la gestion de la structure organisationnelle.
"""

from uuid import uuid4

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.organization import (
    Department,
    Service,
    ServiceAchievement,
    ServiceMediaLibrary,
    ServiceObjective,
    ServiceProject,
)


class OrganizationService:
    """Service pour la gestion de la structure organisationnelle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # DEPARTMENTS
    # =========================================================================

    async def get_departments(
        self,
        search: str | None = None,
        active: bool | None = None,
    ) -> select:
        """
        Construit une requête pour lister les départements.

        Args:
            search: Recherche sur code ou nom.
            active: Filtrer par statut actif.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(Department).options(selectinload(Department.services))

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Department.code.ilike(search_filter),
                    Department.name.ilike(search_filter),
                    Department.description.ilike(search_filter),
                )
            )

        if active is not None:
            query = query.where(Department.active == active)

        query = query.order_by(Department.display_order, Department.name)
        return query

    async def get_department_by_id(self, department_id: str) -> Department | None:
        """Récupère un département par son ID."""
        result = await self.db.execute(
            select(Department)
            .options(selectinload(Department.services))
            .where(Department.id == department_id)
        )
        return result.scalar_one_or_none()

    async def get_department_by_code(self, code: str) -> Department | None:
        """Récupère un département par son code."""
        result = await self.db.execute(
            select(Department).where(Department.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def create_department(
        self,
        code: str,
        name: str,
        **kwargs,
    ) -> Department:
        """
        Crée un nouveau département.

        Args:
            code: Code unique du département.
            name: Nom du département.
            **kwargs: Autres champs optionnels.

        Returns:
            Département créé.

        Raises:
            ConflictException: Si le code existe déjà.
        """
        code = code.upper()
        existing = await self.get_department_by_code(code)
        if existing:
            raise ConflictException(f"Un département avec le code '{code}' existe déjà")

        department = Department(
            id=str(uuid4()),
            code=code,
            name=name,
            **kwargs,
        )
        self.db.add(department)
        await self.db.flush()
        return department

    async def update_department(self, department_id: str, **kwargs) -> Department:
        """
        Met à jour un département.

        Args:
            department_id: ID du département.
            **kwargs: Champs à mettre à jour.

        Returns:
            Département mis à jour.

        Raises:
            NotFoundException: Si le département n'existe pas.
            ConflictException: Si le nouveau code existe déjà.
        """
        department = await self.get_department_by_id(department_id)
        if not department:
            raise NotFoundException("Département non trouvé")

        # Vérifier l'unicité du code si modifié
        if "code" in kwargs and kwargs["code"]:
            kwargs["code"] = kwargs["code"].upper()
            if kwargs["code"] != department.code:
                existing = await self.get_department_by_code(kwargs["code"])
                if existing:
                    raise ConflictException(
                        f"Un département avec le code '{kwargs['code']}' existe déjà"
                    )

        await self.db.execute(
            update(Department).where(Department.id == department_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_department_by_id(department_id)

    async def delete_department(self, department_id: str) -> None:
        """
        Supprime un département.

        Args:
            department_id: ID du département.

        Raises:
            NotFoundException: Si le département n'existe pas.
        """
        department = await self.get_department_by_id(department_id)
        if not department:
            raise NotFoundException("Département non trouvé")

        await self.db.execute(
            delete(Department).where(Department.id == department_id)
        )
        await self.db.flush()

    async def toggle_department_active(self, department_id: str) -> Department:
        """Bascule le statut actif d'un département."""
        department = await self.get_department_by_id(department_id)
        if not department:
            raise NotFoundException("Département non trouvé")

        await self.db.execute(
            update(Department)
            .where(Department.id == department_id)
            .values(active=not department.active)
        )
        await self.db.flush()
        return await self.get_department_by_id(department_id)

    async def reorder_departments(self, department_ids: list[str]) -> list[Department]:
        """
        Réordonne les départements.

        Args:
            department_ids: Liste ordonnée des IDs de départements.

        Returns:
            Liste des départements réordonnés.
        """
        for index, dept_id in enumerate(department_ids):
            await self.db.execute(
                update(Department)
                .where(Department.id == dept_id)
                .values(display_order=index)
            )
        await self.db.flush()

        result = await self.db.execute(
            select(Department)
            .where(Department.id.in_(department_ids))
            .order_by(Department.display_order)
        )
        return list(result.scalars().all())

    async def get_department_services(self, department_id: str) -> list[Service]:
        """Récupère les services d'un département."""
        department = await self.get_department_by_id(department_id)
        if not department:
            raise NotFoundException("Département non trouvé")

        result = await self.db.execute(
            select(Service)
            .where(Service.department_id == department_id)
            .order_by(Service.display_order, Service.name)
        )
        return list(result.scalars().all())

    # =========================================================================
    # SERVICES
    # =========================================================================

    async def get_services(
        self,
        search: str | None = None,
        department_id: str | None = None,
        active: bool | None = None,
    ) -> select:
        """
        Construit une requête pour lister les services.

        Args:
            search: Recherche sur nom ou description.
            department_id: Filtrer par département.
            active: Filtrer par statut actif.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(Service).options(
            selectinload(Service.objectives),
            selectinload(Service.achievements),
            selectinload(Service.projects),
        )

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Service.name.ilike(search_filter),
                    Service.description.ilike(search_filter),
                    Service.mission.ilike(search_filter),
                )
            )

        if department_id:
            query = query.where(Service.department_id == department_id)

        if active is not None:
            query = query.where(Service.active == active)

        query = query.order_by(Service.display_order, Service.name)
        return query

    async def get_service_by_id(self, service_id: str) -> Service | None:
        """Récupère un service par son ID."""
        result = await self.db.execute(
            select(Service)
            .options(
                selectinload(Service.objectives),
                selectinload(Service.achievements),
                selectinload(Service.projects),
            )
            .where(Service.id == service_id)
        )
        return result.scalar_one_or_none()

    async def create_service(
        self,
        name: str,
        department_id: str | None = None,
        **kwargs,
    ) -> Service:
        """
        Crée un nouveau service.

        Args:
            name: Nom du service.
            department_id: ID du département parent (optionnel).
            **kwargs: Autres champs optionnels.

        Returns:
            Service créé.

        Raises:
            NotFoundException: Si le département n'existe pas.
        """
        if department_id:
            department = await self.get_department_by_id(department_id)
            if not department:
                raise NotFoundException("Département non trouvé")

        service = Service(
            id=str(uuid4()),
            name=name,
            department_id=department_id,
            **kwargs,
        )
        self.db.add(service)
        await self.db.flush()
        return service

    async def update_service(self, service_id: str, **kwargs) -> Service:
        """
        Met à jour un service.

        Args:
            service_id: ID du service.
            **kwargs: Champs à mettre à jour.

        Returns:
            Service mis à jour.

        Raises:
            NotFoundException: Si le service n'existe pas.
        """
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        # Vérifier que le département existe si modifié
        if "department_id" in kwargs and kwargs["department_id"]:
            department = await self.get_department_by_id(kwargs["department_id"])
            if not department:
                raise NotFoundException("Département non trouvé")

        await self.db.execute(
            update(Service).where(Service.id == service_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_service_by_id(service_id)

    async def delete_service(self, service_id: str) -> None:
        """
        Supprime un service.

        Args:
            service_id: ID du service.

        Raises:
            NotFoundException: Si le service n'existe pas.
        """
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        await self.db.execute(delete(Service).where(Service.id == service_id))
        await self.db.flush()

    async def toggle_service_active(self, service_id: str) -> Service:
        """Bascule le statut actif d'un service."""
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        await self.db.execute(
            update(Service)
            .where(Service.id == service_id)
            .values(active=not service.active)
        )
        await self.db.flush()
        return await self.get_service_by_id(service_id)

    async def reorder_services(self, service_ids: list[str]) -> list[Service]:
        """
        Réordonne les services.

        Args:
            service_ids: Liste ordonnée des IDs de services.

        Returns:
            Liste des services réordonnés.
        """
        for index, svc_id in enumerate(service_ids):
            await self.db.execute(
                update(Service)
                .where(Service.id == svc_id)
                .values(display_order=index)
            )
        await self.db.flush()

        result = await self.db.execute(
            select(Service)
            .where(Service.id.in_(service_ids))
            .order_by(Service.display_order)
        )
        return list(result.scalars().all())

    # =========================================================================
    # SERVICE OBJECTIVES
    # =========================================================================

    async def get_service_objectives(self, service_id: str) -> list[ServiceObjective]:
        """Récupère les objectifs d'un service."""
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        result = await self.db.execute(
            select(ServiceObjective)
            .where(ServiceObjective.service_id == service_id)
            .order_by(ServiceObjective.display_order)
        )
        return list(result.scalars().all())

    async def create_service_objective(
        self,
        service_id: str,
        title: str,
        **kwargs,
    ) -> ServiceObjective:
        """Crée un objectif pour un service."""
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        objective = ServiceObjective(
            id=str(uuid4()),
            service_id=service_id,
            title=title,
            **kwargs,
        )
        self.db.add(objective)
        await self.db.flush()
        return objective

    async def update_service_objective(
        self, objective_id: str, **kwargs
    ) -> ServiceObjective:
        """Met à jour un objectif."""
        result = await self.db.execute(
            select(ServiceObjective).where(ServiceObjective.id == objective_id)
        )
        objective = result.scalar_one_or_none()
        if not objective:
            raise NotFoundException("Objectif non trouvé")

        await self.db.execute(
            update(ServiceObjective)
            .where(ServiceObjective.id == objective_id)
            .values(**kwargs)
        )
        await self.db.flush()

        result = await self.db.execute(
            select(ServiceObjective).where(ServiceObjective.id == objective_id)
        )
        return result.scalar_one()

    async def delete_service_objective(self, objective_id: str) -> None:
        """Supprime un objectif."""
        result = await self.db.execute(
            select(ServiceObjective).where(ServiceObjective.id == objective_id)
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Objectif non trouvé")

        await self.db.execute(
            delete(ServiceObjective).where(ServiceObjective.id == objective_id)
        )
        await self.db.flush()

    # =========================================================================
    # SERVICE ACHIEVEMENTS
    # =========================================================================

    async def get_service_achievements(
        self, service_id: str
    ) -> list[ServiceAchievement]:
        """Récupère les réalisations d'un service."""
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        result = await self.db.execute(
            select(ServiceAchievement)
            .where(ServiceAchievement.service_id == service_id)
            .order_by(ServiceAchievement.achievement_date.desc())
        )
        return list(result.scalars().all())

    async def create_service_achievement(
        self,
        service_id: str,
        title: str,
        **kwargs,
    ) -> ServiceAchievement:
        """Crée une réalisation pour un service."""
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        achievement = ServiceAchievement(
            id=str(uuid4()),
            service_id=service_id,
            title=title,
            **kwargs,
        )
        self.db.add(achievement)
        await self.db.flush()
        return achievement

    async def update_service_achievement(
        self, achievement_id: str, **kwargs
    ) -> ServiceAchievement:
        """Met à jour une réalisation."""
        result = await self.db.execute(
            select(ServiceAchievement).where(ServiceAchievement.id == achievement_id)
        )
        achievement = result.scalar_one_or_none()
        if not achievement:
            raise NotFoundException("Réalisation non trouvée")

        await self.db.execute(
            update(ServiceAchievement)
            .where(ServiceAchievement.id == achievement_id)
            .values(**kwargs)
        )
        await self.db.flush()

        result = await self.db.execute(
            select(ServiceAchievement).where(ServiceAchievement.id == achievement_id)
        )
        return result.scalar_one()

    async def delete_service_achievement(self, achievement_id: str) -> None:
        """Supprime une réalisation."""
        result = await self.db.execute(
            select(ServiceAchievement).where(ServiceAchievement.id == achievement_id)
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Réalisation non trouvée")

        await self.db.execute(
            delete(ServiceAchievement).where(ServiceAchievement.id == achievement_id)
        )
        await self.db.flush()

    # =========================================================================
    # SERVICE PROJECTS
    # =========================================================================

    async def get_service_projects(self, service_id: str) -> list[ServiceProject]:
        """Récupère les projets d'un service."""
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        result = await self.db.execute(
            select(ServiceProject)
            .where(ServiceProject.service_id == service_id)
            .order_by(ServiceProject.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_service_project(
        self,
        service_id: str,
        title: str,
        **kwargs,
    ) -> ServiceProject:
        """Crée un projet pour un service."""
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        project = ServiceProject(
            id=str(uuid4()),
            service_id=service_id,
            title=title,
            **kwargs,
        )
        self.db.add(project)
        await self.db.flush()
        return project

    async def update_service_project(
        self, project_id: str, **kwargs
    ) -> ServiceProject:
        """Met à jour un projet."""
        result = await self.db.execute(
            select(ServiceProject).where(ServiceProject.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundException("Projet non trouvé")

        await self.db.execute(
            update(ServiceProject)
            .where(ServiceProject.id == project_id)
            .values(**kwargs)
        )
        await self.db.flush()

        result = await self.db.execute(
            select(ServiceProject).where(ServiceProject.id == project_id)
        )
        return result.scalar_one()

    async def delete_service_project(self, project_id: str) -> None:
        """Supprime un projet."""
        result = await self.db.execute(
            select(ServiceProject).where(ServiceProject.id == project_id)
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Projet non trouvé")

        await self.db.execute(
            delete(ServiceProject).where(ServiceProject.id == project_id)
        )
        await self.db.flush()

    # =========================================================================
    # SERVICE MEDIA LIBRARY
    # =========================================================================

    async def add_album_to_service(
        self, service_id: str, album_external_id: str
    ) -> None:
        """Ajoute un album à la médiathèque d'un service."""
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        # Vérifier si la liaison existe déjà
        result = await self.db.execute(
            select(ServiceMediaLibrary).where(
                ServiceMediaLibrary.service_id == service_id,
                ServiceMediaLibrary.album_external_id == album_external_id,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException("Cet album est déjà associé au service")

        link = ServiceMediaLibrary(
            service_id=service_id,
            album_external_id=album_external_id,
        )
        self.db.add(link)
        await self.db.flush()

    async def remove_album_from_service(
        self, service_id: str, album_external_id: str
    ) -> None:
        """Retire un album de la médiathèque d'un service."""
        result = await self.db.execute(
            select(ServiceMediaLibrary).where(
                ServiceMediaLibrary.service_id == service_id,
                ServiceMediaLibrary.album_external_id == album_external_id,
            )
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Cette association n'existe pas")

        await self.db.execute(
            delete(ServiceMediaLibrary).where(
                ServiceMediaLibrary.service_id == service_id,
                ServiceMediaLibrary.album_external_id == album_external_id,
            )
        )
        await self.db.flush()

    async def get_service_albums(self, service_id: str) -> list[str]:
        """Récupère les IDs d'albums associés à un service."""
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        result = await self.db.execute(
            select(ServiceMediaLibrary.album_external_id).where(
                ServiceMediaLibrary.service_id == service_id
            )
        )
        return [row[0] for row in result.all()]
