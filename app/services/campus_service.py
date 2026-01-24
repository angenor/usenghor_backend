"""
Service Campus
===============

Logique métier pour la gestion des campus.
"""

from datetime import date
from uuid import uuid4

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.campus import (
    Campus,
    CampusMediaLibrary,
    CampusPartner,
    CampusTeam,
)


class CampusService:
    """Service pour la gestion des campus."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # CAMPUSES
    # =========================================================================

    async def get_campuses(
        self,
        search: str | None = None,
        country_id: str | None = None,
        active: bool | None = None,
        is_headquarters: bool | None = None,
    ) -> select:
        """
        Construit une requête pour lister les campus.

        Args:
            search: Recherche sur code, nom, ville ou description.
            country_id: Filtrer par pays.
            active: Filtrer par statut actif.
            is_headquarters: Filtrer par siège principal.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(Campus).options(selectinload(Campus.team_members))

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Campus.code.ilike(search_filter),
                    Campus.name.ilike(search_filter),
                    Campus.city.ilike(search_filter),
                    Campus.description.ilike(search_filter),
                )
            )

        if country_id:
            query = query.where(Campus.country_external_id == country_id)

        if active is not None:
            query = query.where(Campus.active == active)

        if is_headquarters is not None:
            query = query.where(Campus.is_headquarters == is_headquarters)

        query = query.order_by(Campus.is_headquarters.desc(), Campus.name)
        return query

    async def get_campus_by_id(self, campus_id: str) -> Campus | None:
        """Récupère un campus par son ID."""
        result = await self.db.execute(
            select(Campus)
            .options(selectinload(Campus.team_members))
            .where(Campus.id == campus_id)
        )
        return result.scalar_one_or_none()

    async def get_campus_by_code(self, code: str) -> Campus | None:
        """Récupère un campus par son code."""
        result = await self.db.execute(
            select(Campus).where(Campus.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def create_campus(
        self,
        code: str,
        name: str,
        **kwargs,
    ) -> Campus:
        """
        Crée un nouveau campus.

        Args:
            code: Code unique du campus.
            name: Nom du campus.
            **kwargs: Autres champs optionnels.

        Returns:
            Campus créé.

        Raises:
            ConflictException: Si le code existe déjà.
        """
        code = code.upper()
        existing = await self.get_campus_by_code(code)
        if existing:
            raise ConflictException(f"Un campus avec le code '{code}' existe déjà")

        # Si c'est le siège, s'assurer qu'il n'y en a pas déjà un
        if kwargs.get("is_headquarters"):
            result = await self.db.execute(
                select(Campus).where(Campus.is_headquarters == True)
            )
            if result.scalar_one_or_none():
                raise ConflictException("Un siège principal existe déjà")

        campus = Campus(
            id=str(uuid4()),
            code=code,
            name=name,
            **kwargs,
        )
        self.db.add(campus)
        await self.db.flush()
        return campus

    async def update_campus(self, campus_id: str, **kwargs) -> Campus:
        """
        Met à jour un campus.

        Args:
            campus_id: ID du campus.
            **kwargs: Champs à mettre à jour.

        Returns:
            Campus mis à jour.

        Raises:
            NotFoundException: Si le campus n'existe pas.
            ConflictException: Si le nouveau code existe déjà ou si on tente d'ajouter un second siège.
        """
        campus = await self.get_campus_by_id(campus_id)
        if not campus:
            raise NotFoundException("Campus non trouvé")

        # Vérifier l'unicité du code si modifié
        if "code" in kwargs and kwargs["code"]:
            kwargs["code"] = kwargs["code"].upper()
            if kwargs["code"] != campus.code:
                existing = await self.get_campus_by_code(kwargs["code"])
                if existing:
                    raise ConflictException(
                        f"Un campus avec le code '{kwargs['code']}' existe déjà"
                    )

        # Vérifier la contrainte du siège unique si modifié
        if kwargs.get("is_headquarters") and not campus.is_headquarters:
            result = await self.db.execute(
                select(Campus).where(
                    Campus.is_headquarters == True,
                    Campus.id != campus_id,
                )
            )
            if result.scalar_one_or_none():
                raise ConflictException("Un siège principal existe déjà")

        await self.db.execute(
            update(Campus).where(Campus.id == campus_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_campus_by_id(campus_id)

    async def delete_campus(self, campus_id: str) -> None:
        """
        Supprime un campus.

        Args:
            campus_id: ID du campus.

        Raises:
            NotFoundException: Si le campus n'existe pas.
        """
        campus = await self.get_campus_by_id(campus_id)
        if not campus:
            raise NotFoundException("Campus non trouvé")

        await self.db.execute(delete(Campus).where(Campus.id == campus_id))
        await self.db.flush()

    async def toggle_campus_active(self, campus_id: str) -> Campus:
        """Bascule le statut actif d'un campus."""
        campus = await self.get_campus_by_id(campus_id)
        if not campus:
            raise NotFoundException("Campus non trouvé")

        await self.db.execute(
            update(Campus)
            .where(Campus.id == campus_id)
            .values(active=not campus.active)
        )
        await self.db.flush()
        return await self.get_campus_by_id(campus_id)

    # =========================================================================
    # CAMPUS TEAM
    # =========================================================================

    async def get_campus_team(
        self,
        campus_id: str | None = None,
        active: bool | None = None,
    ) -> select:
        """
        Construit une requête pour lister les membres d'équipe.

        Args:
            campus_id: Filtrer par campus.
            active: Filtrer par statut actif.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(CampusTeam)

        if campus_id:
            query = query.where(CampusTeam.campus_id == campus_id)

        if active is not None:
            query = query.where(CampusTeam.active == active)

        query = query.order_by(CampusTeam.display_order, CampusTeam.position)
        return query

    async def get_team_member_by_id(self, team_member_id: str) -> CampusTeam | None:
        """Récupère un membre d'équipe par son ID."""
        result = await self.db.execute(
            select(CampusTeam).where(CampusTeam.id == team_member_id)
        )
        return result.scalar_one_or_none()

    async def create_team_member(
        self,
        campus_id: str,
        user_external_id: str,
        position: str,
        **kwargs,
    ) -> CampusTeam:
        """
        Ajoute un membre à l'équipe d'un campus.

        Args:
            campus_id: ID du campus.
            user_external_id: ID de l'utilisateur.
            position: Poste occupé.
            **kwargs: Autres champs optionnels.

        Returns:
            Membre d'équipe créé.

        Raises:
            NotFoundException: Si le campus n'existe pas.
            ConflictException: Si l'utilisateur est déjà dans l'équipe.
        """
        campus = await self.get_campus_by_id(campus_id)
        if not campus:
            raise NotFoundException("Campus non trouvé")

        # Vérifier que l'utilisateur n'est pas déjà dans l'équipe
        result = await self.db.execute(
            select(CampusTeam).where(
                CampusTeam.campus_id == campus_id,
                CampusTeam.user_external_id == user_external_id,
                CampusTeam.active == True,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException("Cet utilisateur est déjà dans l'équipe du campus")

        team_member = CampusTeam(
            id=str(uuid4()),
            campus_id=campus_id,
            user_external_id=user_external_id,
            position=position,
            **kwargs,
        )
        self.db.add(team_member)
        await self.db.flush()
        return team_member

    async def update_team_member(self, team_member_id: str, **kwargs) -> CampusTeam:
        """
        Met à jour un membre d'équipe.

        Args:
            team_member_id: ID du membre.
            **kwargs: Champs à mettre à jour.

        Returns:
            Membre mis à jour.

        Raises:
            NotFoundException: Si le membre n'existe pas.
        """
        team_member = await self.get_team_member_by_id(team_member_id)
        if not team_member:
            raise NotFoundException("Membre d'équipe non trouvé")

        await self.db.execute(
            update(CampusTeam).where(CampusTeam.id == team_member_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_team_member_by_id(team_member_id)

    async def delete_team_member(self, team_member_id: str) -> None:
        """
        Supprime un membre d'équipe.

        Args:
            team_member_id: ID du membre.

        Raises:
            NotFoundException: Si le membre n'existe pas.
        """
        team_member = await self.get_team_member_by_id(team_member_id)
        if not team_member:
            raise NotFoundException("Membre d'équipe non trouvé")

        await self.db.execute(
            delete(CampusTeam).where(CampusTeam.id == team_member_id)
        )
        await self.db.flush()

    async def toggle_team_member_active(self, team_member_id: str) -> CampusTeam:
        """Bascule le statut actif d'un membre d'équipe."""
        team_member = await self.get_team_member_by_id(team_member_id)
        if not team_member:
            raise NotFoundException("Membre d'équipe non trouvé")

        await self.db.execute(
            update(CampusTeam)
            .where(CampusTeam.id == team_member_id)
            .values(active=not team_member.active)
        )
        await self.db.flush()
        return await self.get_team_member_by_id(team_member_id)

    async def reorder_team_members(self, team_member_ids: list[str]) -> list[CampusTeam]:
        """
        Réordonne les membres d'équipe.

        Args:
            team_member_ids: Liste ordonnée des IDs de membres.

        Returns:
            Liste des membres réordonnés.
        """
        for index, member_id in enumerate(team_member_ids):
            await self.db.execute(
                update(CampusTeam)
                .where(CampusTeam.id == member_id)
                .values(display_order=index)
            )
        await self.db.flush()

        result = await self.db.execute(
            select(CampusTeam)
            .where(CampusTeam.id.in_(team_member_ids))
            .order_by(CampusTeam.display_order)
        )
        return list(result.scalars().all())

    # =========================================================================
    # CAMPUS PARTNERS
    # =========================================================================

    async def get_campus_partners(self, campus_id: str) -> list[CampusPartner]:
        """Récupère les partenaires d'un campus."""
        campus = await self.get_campus_by_id(campus_id)
        if not campus:
            raise NotFoundException("Campus non trouvé")

        result = await self.db.execute(
            select(CampusPartner).where(CampusPartner.campus_id == campus_id)
        )
        return list(result.scalars().all())

    async def add_partner_to_campus(
        self,
        campus_id: str,
        partner_external_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> CampusPartner:
        """
        Ajoute un partenaire à un campus.

        Args:
            campus_id: ID du campus.
            partner_external_id: ID du partenaire.
            start_date: Date de début du partenariat.
            end_date: Date de fin du partenariat.

        Returns:
            Partenariat créé.

        Raises:
            NotFoundException: Si le campus n'existe pas.
            ConflictException: Si le partenariat existe déjà.
        """
        campus = await self.get_campus_by_id(campus_id)
        if not campus:
            raise NotFoundException("Campus non trouvé")

        # Vérifier si le partenariat existe déjà
        result = await self.db.execute(
            select(CampusPartner).where(
                CampusPartner.campus_id == campus_id,
                CampusPartner.partner_external_id == partner_external_id,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException("Ce partenaire est déjà associé au campus")

        partner = CampusPartner(
            campus_id=campus_id,
            partner_external_id=partner_external_id,
            start_date=start_date,
            end_date=end_date,
        )
        self.db.add(partner)
        await self.db.flush()
        return partner

    async def update_campus_partner(
        self,
        campus_id: str,
        partner_external_id: str,
        **kwargs,
    ) -> CampusPartner:
        """Met à jour les dates d'un partenariat."""
        result = await self.db.execute(
            select(CampusPartner).where(
                CampusPartner.campus_id == campus_id,
                CampusPartner.partner_external_id == partner_external_id,
            )
        )
        partner = result.scalar_one_or_none()
        if not partner:
            raise NotFoundException("Partenariat non trouvé")

        await self.db.execute(
            update(CampusPartner)
            .where(
                CampusPartner.campus_id == campus_id,
                CampusPartner.partner_external_id == partner_external_id,
            )
            .values(**kwargs)
        )
        await self.db.flush()

        result = await self.db.execute(
            select(CampusPartner).where(
                CampusPartner.campus_id == campus_id,
                CampusPartner.partner_external_id == partner_external_id,
            )
        )
        return result.scalar_one()

    async def remove_partner_from_campus(
        self, campus_id: str, partner_external_id: str
    ) -> None:
        """
        Retire un partenaire d'un campus.

        Args:
            campus_id: ID du campus.
            partner_external_id: ID du partenaire.

        Raises:
            NotFoundException: Si le partenariat n'existe pas.
        """
        result = await self.db.execute(
            select(CampusPartner).where(
                CampusPartner.campus_id == campus_id,
                CampusPartner.partner_external_id == partner_external_id,
            )
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Partenariat non trouvé")

        await self.db.execute(
            delete(CampusPartner).where(
                CampusPartner.campus_id == campus_id,
                CampusPartner.partner_external_id == partner_external_id,
            )
        )
        await self.db.flush()

    # =========================================================================
    # CAMPUS MEDIA LIBRARY
    # =========================================================================

    async def get_campus_albums(self, campus_id: str) -> list[str]:
        """Récupère les IDs d'albums associés à un campus."""
        campus = await self.get_campus_by_id(campus_id)
        if not campus:
            raise NotFoundException("Campus non trouvé")

        result = await self.db.execute(
            select(CampusMediaLibrary.album_external_id).where(
                CampusMediaLibrary.campus_id == campus_id
            )
        )
        return [row[0] for row in result.all()]

    async def add_album_to_campus(
        self, campus_id: str, album_external_id: str
    ) -> None:
        """
        Ajoute un album à la médiathèque d'un campus.

        Args:
            campus_id: ID du campus.
            album_external_id: ID de l'album.

        Raises:
            NotFoundException: Si le campus n'existe pas.
            ConflictException: Si l'album est déjà associé.
        """
        campus = await self.get_campus_by_id(campus_id)
        if not campus:
            raise NotFoundException("Campus non trouvé")

        # Vérifier si la liaison existe déjà
        result = await self.db.execute(
            select(CampusMediaLibrary).where(
                CampusMediaLibrary.campus_id == campus_id,
                CampusMediaLibrary.album_external_id == album_external_id,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException("Cet album est déjà associé au campus")

        link = CampusMediaLibrary(
            campus_id=campus_id,
            album_external_id=album_external_id,
        )
        self.db.add(link)
        await self.db.flush()

    async def remove_album_from_campus(
        self, campus_id: str, album_external_id: str
    ) -> None:
        """
        Retire un album de la médiathèque d'un campus.

        Args:
            campus_id: ID du campus.
            album_external_id: ID de l'album.

        Raises:
            NotFoundException: Si l'association n'existe pas.
        """
        result = await self.db.execute(
            select(CampusMediaLibrary).where(
                CampusMediaLibrary.campus_id == campus_id,
                CampusMediaLibrary.album_external_id == album_external_id,
            )
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Cette association n'existe pas")

        await self.db.execute(
            delete(CampusMediaLibrary).where(
                CampusMediaLibrary.campus_id == campus_id,
                CampusMediaLibrary.album_external_id == album_external_id,
            )
        )
        await self.db.flush()
