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
    Sector,
    Service,
    ServiceAchievement,
    ServiceMediaLibrary,
    ServiceObjective,
    ServiceProject,
    ServiceTeam,
)


class OrganizationService:
    """Service pour la gestion de la structure organisationnelle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # SECTORS
    # =========================================================================

    async def get_sectors(
        self,
        search: str | None = None,
        active: bool | None = None,
    ) -> select:
        """
        Construit une requête pour lister les secteurs.

        Args:
            search: Recherche sur code ou nom.
            active: Filtrer par statut actif.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(Sector).options(selectinload(Sector.services))

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Sector.code.ilike(search_filter),
                    Sector.name.ilike(search_filter),
                    Sector.description.ilike(search_filter),
                )
            )

        if active is not None:
            query = query.where(Sector.active == active)

        query = query.order_by(Sector.display_order, Sector.name)
        return query

    async def get_sector_by_id(self, sector_id: str) -> Sector | None:
        """Récupère un secteur par son ID."""
        result = await self.db.execute(
            select(Sector)
            .options(selectinload(Sector.services))
            .where(Sector.id == sector_id)
        )
        return result.scalar_one_or_none()

    async def get_sector_by_code(self, code: str) -> Sector | None:
        """Récupère un secteur par son code."""
        result = await self.db.execute(
            select(Sector)
            .options(selectinload(Sector.services))
            .where(Sector.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def create_sector(
        self,
        code: str,
        name: str,
        **kwargs,
    ) -> Sector:
        """
        Crée un nouveau secteur.

        Args:
            code: Code unique du secteur.
            name: Nom du secteur.
            **kwargs: Autres champs optionnels.

        Returns:
            Secteur créé.

        Raises:
            ConflictException: Si le code existe déjà.
        """
        code = code.upper()
        existing = await self.get_sector_by_code(code)
        if existing:
            raise ConflictException(f"Un secteur avec le code '{code}' existe déjà")

        sector = Sector(
            id=str(uuid4()),
            code=code,
            name=name,
            **kwargs,
        )
        self.db.add(sector)
        await self.db.flush()
        return sector

    async def update_sector(self, sector_id: str, **kwargs) -> Sector:
        """
        Met à jour un secteur.

        Args:
            sector_id: ID du secteur.
            **kwargs: Champs à mettre à jour.

        Returns:
            Secteur mis à jour.

        Raises:
            NotFoundException: Si le secteur n'existe pas.
            ConflictException: Si le nouveau code existe déjà.
        """
        sector = await self.get_sector_by_id(sector_id)
        if not sector:
            raise NotFoundException("Secteur non trouvé")

        # Vérifier l'unicité du code si modifié
        if "code" in kwargs and kwargs["code"]:
            kwargs["code"] = kwargs["code"].upper()
            if kwargs["code"] != sector.code:
                existing = await self.get_sector_by_code(kwargs["code"])
                if existing:
                    raise ConflictException(
                        f"Un secteur avec le code '{kwargs['code']}' existe déjà"
                    )

        await self.db.execute(
            update(Sector).where(Sector.id == sector_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_sector_by_id(sector_id)

    async def delete_sector(self, sector_id: str) -> None:
        """
        Supprime un secteur.

        Args:
            sector_id: ID du secteur.

        Raises:
            NotFoundException: Si le secteur n'existe pas.
        """
        sector = await self.get_sector_by_id(sector_id)
        if not sector:
            raise NotFoundException("Secteur non trouvé")

        await self.db.execute(
            delete(Sector).where(Sector.id == sector_id)
        )
        await self.db.flush()

    async def toggle_sector_active(self, sector_id: str) -> Sector:
        """Bascule le statut actif d'un secteur."""
        sector = await self.get_sector_by_id(sector_id)
        if not sector:
            raise NotFoundException("Secteur non trouvé")

        await self.db.execute(
            update(Sector)
            .where(Sector.id == sector_id)
            .values(active=not sector.active)
        )
        await self.db.flush()
        return await self.get_sector_by_id(sector_id)

    async def reorder_sectors(self, sector_ids: list[str]) -> list[Sector]:
        """
        Réordonne les secteurs.

        Args:
            sector_ids: Liste ordonnée des IDs de secteurs.

        Returns:
            Liste des secteurs réordonnés.
        """
        for index, sect_id in enumerate(sector_ids):
            await self.db.execute(
                update(Sector)
                .where(Sector.id == sect_id)
                .values(display_order=index)
            )
        await self.db.flush()

        result = await self.db.execute(
            select(Sector)
            .where(Sector.id.in_(sector_ids))
            .order_by(Sector.display_order)
        )
        return list(result.scalars().all())

    async def get_sector_services(self, sector_id: str) -> list[Service]:
        """Récupère les services d'un secteur."""
        sector = await self.get_sector_by_id(sector_id)
        if not sector:
            raise NotFoundException("Secteur non trouvé")

        result = await self.db.execute(
            select(Service)
            .where(Service.sector_id == sector_id)
            .order_by(Service.display_order, Service.name)
        )
        return list(result.scalars().all())

    async def duplicate_sector(self, sector_id: str, new_code: str) -> Sector:
        """
        Duplique un secteur avec un nouveau code.

        Args:
            sector_id: ID du secteur à dupliquer.
            new_code: Code unique pour le nouveau secteur.

        Returns:
            Nouveau secteur créé.

        Raises:
            NotFoundException: Si le secteur source n'existe pas.
            ConflictException: Si le nouveau code existe déjà.
        """
        sector = await self.get_sector_by_id(sector_id)
        if not sector:
            raise NotFoundException("Secteur non trouvé")

        new_code = new_code.upper()
        existing = await self.get_sector_by_code(new_code)
        if existing:
            raise ConflictException(f"Un secteur avec le code '{new_code}' existe déjà")

        new_sector = Sector(
            id=str(uuid4()),
            code=new_code,
            name=f"{sector.name} (copie)",
            description=sector.description,
            mission=sector.mission,
            icon_external_id=sector.icon_external_id,
            cover_image_external_id=sector.cover_image_external_id,
            head_external_id=sector.head_external_id,
            display_order=sector.display_order + 1,
            active=False,  # Désactivé par défaut
        )
        self.db.add(new_sector)
        await self.db.flush()
        return new_sector

    # =========================================================================
    # SECTORS - PUBLIC METHODS
    # =========================================================================

    async def get_active_sectors(self) -> list[Sector]:
        """Récupère les secteurs actifs triés par display_order."""
        result = await self.db.execute(
            select(Sector)
            .options(selectinload(Sector.services))
            .where(Sector.active == True)
            .order_by(Sector.display_order, Sector.name)
        )
        return list(result.scalars().all())

    async def get_active_sectors_with_active_services(self) -> list[Sector]:
        """Récupère les secteurs actifs avec uniquement leurs services actifs."""
        result = await self.db.execute(
            select(Sector)
            .options(selectinload(Sector.services))
            .where(Sector.active == True)
            .order_by(Sector.display_order, Sector.name)
        )
        sectors = list(result.scalars().all())
        # Filtrer pour ne garder que les services actifs
        for sector in sectors:
            sector.services = [s for s in sector.services if s.active]
            sector.services.sort(key=lambda s: (s.display_order, s.name))
        return sectors

    # =========================================================================
    # SERVICES
    # =========================================================================

    async def get_services(
        self,
        search: str | None = None,
        sector_id: str | None = None,
        active: bool | None = None,
    ) -> select:
        """
        Construit une requête pour lister les services.

        Args:
            search: Recherche sur nom ou description.
            sector_id: Filtrer par secteur.
            active: Filtrer par statut actif.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(Service).options(
            selectinload(Service.objectives),
            selectinload(Service.achievements),
            selectinload(Service.projects),
            selectinload(Service.team),
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

        if sector_id:
            query = query.where(Service.sector_id == sector_id)

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
                selectinload(Service.team),
            )
            .where(Service.id == service_id)
        )
        return result.scalar_one_or_none()

    async def create_service(
        self,
        name: str,
        sector_id: str | None = None,
        **kwargs,
    ) -> Service:
        """
        Crée un nouveau service.

        Args:
            name: Nom du service.
            sector_id: ID du secteur parent (optionnel).
            **kwargs: Autres champs optionnels.

        Returns:
            Service créé.

        Raises:
            NotFoundException: Si le secteur n'existe pas.
        """
        if sector_id:
            sector = await self.get_sector_by_id(sector_id)
            if not sector:
                raise NotFoundException("Secteur non trouvé")

        service = Service(
            id=str(uuid4()),
            name=name,
            sector_id=sector_id,
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

        # Vérifier que le secteur existe si modifié
        if "sector_id" in kwargs and kwargs["sector_id"]:
            sector = await self.get_sector_by_id(kwargs["sector_id"])
            if not sector:
                raise NotFoundException("Secteur non trouvé")

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

    async def duplicate_service(self, service_id: str, new_name: str) -> Service:
        """
        Duplique un service avec un nouveau nom.

        Args:
            service_id: ID du service à dupliquer.
            new_name: Nom pour le nouveau service.

        Returns:
            Nouveau service créé.

        Raises:
            NotFoundException: Si le service source n'existe pas.
        """
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        new_service = Service(
            id=str(uuid4()),
            sector_id=service.sector_id,
            name=new_name,
            description=service.description,
            mission=service.mission,
            head_external_id=service.head_external_id,
            album_external_id=service.album_external_id,
            email=service.email,
            phone=service.phone,
            display_order=service.display_order + 1,
            active=False,  # Désactivé par défaut
        )
        self.db.add(new_service)
        await self.db.flush()

        # Dupliquer les objectifs
        for obj in service.objectives:
            new_obj = ServiceObjective(
                id=str(uuid4()),
                service_id=new_service.id,
                title=obj.title,
                description=obj.description,
                display_order=obj.display_order,
            )
            self.db.add(new_obj)

        await self.db.flush()
        return await self.get_service_by_id(new_service.id)

    # =========================================================================
    # SERVICES - PUBLIC METHODS
    # =========================================================================

    async def get_active_services(
        self, sector_id: str | None = None
    ) -> list[Service]:
        """
        Récupère les services actifs.

        Args:
            sector_id: Filtrer par secteur (optionnel).

        Returns:
            Liste des services actifs triés.
        """
        query = select(Service).where(Service.active == True)

        if sector_id:
            query = query.where(Service.sector_id == sector_id)

        query = query.order_by(Service.display_order, Service.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_service_with_details(self, service_id: str) -> Service | None:
        """
        Récupère un service avec ses objectifs, réalisations, projets et équipe.

        Args:
            service_id: ID du service.

        Returns:
            Service avec ses détails ou None si non trouvé.
        """
        result = await self.db.execute(
            select(Service)
            .options(
                selectinload(Service.objectives),
                selectinload(Service.achievements),
                selectinload(Service.projects),
                selectinload(Service.team),
            )
            .where(Service.id == service_id, Service.active == True)
        )
        return result.scalar_one_or_none()

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

    # =========================================================================
    # SERVICE TEAM
    # =========================================================================

    async def get_service_team(self, service_id: str) -> list[ServiceTeam]:
        """Récupère les membres de l'équipe d'un service."""
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        result = await self.db.execute(
            select(ServiceTeam)
            .where(ServiceTeam.service_id == service_id)
            .order_by(ServiceTeam.display_order, ServiceTeam.created_at)
        )
        return list(result.scalars().all())

    async def get_service_team_member(self, member_id: str) -> ServiceTeam | None:
        """Récupère un membre de l'équipe par son ID."""
        result = await self.db.execute(
            select(ServiceTeam).where(ServiceTeam.id == member_id)
        )
        return result.scalar_one_or_none()

    async def create_service_team_member(
        self,
        service_id: str,
        user_external_id: str,
        position: str,
        **kwargs,
    ) -> ServiceTeam:
        """Ajoute un membre à l'équipe d'un service."""
        service = await self.get_service_by_id(service_id)
        if not service:
            raise NotFoundException("Service non trouvé")

        member = ServiceTeam(
            id=str(uuid4()),
            service_id=service_id,
            user_external_id=user_external_id,
            position=position,
            **kwargs,
        )
        self.db.add(member)
        await self.db.flush()
        return member

    async def update_service_team_member(
        self, member_id: str, **kwargs
    ) -> ServiceTeam:
        """Met à jour un membre de l'équipe."""
        result = await self.db.execute(
            select(ServiceTeam).where(ServiceTeam.id == member_id)
        )
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundException("Membre non trouvé")

        await self.db.execute(
            update(ServiceTeam)
            .where(ServiceTeam.id == member_id)
            .values(**kwargs)
        )
        await self.db.flush()

        result = await self.db.execute(
            select(ServiceTeam).where(ServiceTeam.id == member_id)
        )
        return result.scalar_one()

    async def delete_service_team_member(self, member_id: str) -> None:
        """Supprime un membre de l'équipe."""
        result = await self.db.execute(
            select(ServiceTeam).where(ServiceTeam.id == member_id)
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Membre non trouvé")

        await self.db.execute(
            delete(ServiceTeam).where(ServiceTeam.id == member_id)
        )
        await self.db.flush()

    async def get_user_service_affectations(self, user_id: str) -> list[ServiceTeam]:
        """Récupère les affectations service d'un utilisateur."""
        result = await self.db.execute(
            select(ServiceTeam)
            .where(ServiceTeam.user_external_id == user_id)
            .order_by(ServiceTeam.created_at.desc())
        )
        return list(result.scalars().all())
