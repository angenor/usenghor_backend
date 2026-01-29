"""
Service Partner
================

Logique métier pour la gestion des partenaires.
"""

from uuid import uuid4

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.campus import Campus, CampusPartner
from app.models.partner import Partner, PartnerType
from app.models.project import Project, ProjectPartner


class PartnerService:
    """Service pour la gestion des partenaires."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_partners(
        self,
        search: str | None = None,
        partner_type: PartnerType | None = None,
        country_id: str | None = None,
        active: bool | None = None,
    ) -> select:
        """
        Construit une requête pour lister les partenaires.

        Args:
            search: Recherche sur nom ou description.
            partner_type: Filtrer par type de partenaire.
            country_id: Filtrer par pays.
            active: Filtrer par statut actif.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(Partner)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Partner.name.ilike(search_filter),
                    Partner.description.ilike(search_filter),
                )
            )

        if partner_type:
            query = query.where(Partner.type == partner_type)

        if country_id:
            query = query.where(Partner.country_external_id == country_id)

        if active is not None:
            query = query.where(Partner.active == active)

        query = query.order_by(Partner.display_order, Partner.name)
        return query

    async def get_partner_by_id(self, partner_id: str) -> Partner | None:
        """Récupère un partenaire par son ID."""
        result = await self.db.execute(
            select(Partner).where(Partner.id == partner_id)
        )
        return result.scalar_one_or_none()

    async def create_partner(
        self,
        name: str,
        partner_type: PartnerType,
        **kwargs,
    ) -> Partner:
        """
        Crée un nouveau partenaire.

        Args:
            name: Nom du partenaire.
            partner_type: Type de partenaire.
            **kwargs: Autres champs optionnels.

        Returns:
            Partenaire créé.
        """
        partner = Partner(
            id=str(uuid4()),
            name=name,
            type=partner_type,
            **kwargs,
        )
        self.db.add(partner)
        await self.db.flush()
        return partner

    async def update_partner(self, partner_id: str, **kwargs) -> Partner:
        """
        Met à jour un partenaire.

        Args:
            partner_id: ID du partenaire.
            **kwargs: Champs à mettre à jour.

        Returns:
            Partenaire mis à jour.

        Raises:
            NotFoundException: Si le partenaire n'existe pas.
        """
        partner = await self.get_partner_by_id(partner_id)
        if not partner:
            raise NotFoundException("Partenaire non trouvé")

        await self.db.execute(
            update(Partner).where(Partner.id == partner_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_partner_by_id(partner_id)

    async def delete_partner(self, partner_id: str) -> None:
        """
        Supprime un partenaire.

        Args:
            partner_id: ID du partenaire.

        Raises:
            NotFoundException: Si le partenaire n'existe pas.
        """
        partner = await self.get_partner_by_id(partner_id)
        if not partner:
            raise NotFoundException("Partenaire non trouvé")

        await self.db.execute(delete(Partner).where(Partner.id == partner_id))
        await self.db.flush()

    async def toggle_partner_active(self, partner_id: str) -> Partner:
        """Bascule le statut actif d'un partenaire."""
        partner = await self.get_partner_by_id(partner_id)
        if not partner:
            raise NotFoundException("Partenaire non trouvé")

        await self.db.execute(
            update(Partner)
            .where(Partner.id == partner_id)
            .values(active=not partner.active)
        )
        await self.db.flush()
        return await self.get_partner_by_id(partner_id)

    async def reorder_partners(self, partner_ids: list[str]) -> list[Partner]:
        """
        Réordonne les partenaires.

        Args:
            partner_ids: Liste ordonnée des IDs de partenaires.

        Returns:
            Liste des partenaires réordonnés.
        """
        for index, partner_id in enumerate(partner_ids):
            await self.db.execute(
                update(Partner)
                .where(Partner.id == partner_id)
                .values(display_order=index)
            )
        await self.db.flush()

        result = await self.db.execute(
            select(Partner)
            .where(Partner.id.in_(partner_ids))
            .order_by(Partner.display_order)
        )
        return list(result.scalars().all())

    async def get_partners_by_type(self, partner_type: PartnerType) -> list[Partner]:
        """Récupère les partenaires actifs d'un type donné."""
        result = await self.db.execute(
            select(Partner)
            .where(Partner.type == partner_type, Partner.active == True)
            .order_by(Partner.display_order, Partner.name)
        )
        return list(result.scalars().all())

    async def get_partner_associations(self, partner_id: str) -> dict:
        """
        Récupère les associations d'un partenaire (campus et projets).

        Args:
            partner_id: ID du partenaire.

        Returns:
            Dict avec les listes de campus et projets associés.
        """
        # Récupérer les campus associés
        campus_result = await self.db.execute(
            select(Campus.id, Campus.name, Campus.code)
            .join(CampusPartner, Campus.id == CampusPartner.campus_id)
            .where(CampusPartner.partner_external_id == partner_id)
            .order_by(Campus.name)
        )
        campuses = [
            {"id": row.id, "name": row.name, "code": row.code}
            for row in campus_result.all()
        ]

        # Récupérer les projets associés
        project_result = await self.db.execute(
            select(Project.id, Project.title, ProjectPartner.partner_role)
            .join(ProjectPartner, Project.id == ProjectPartner.project_id)
            .where(ProjectPartner.partner_external_id == partner_id)
            .order_by(Project.title)
        )
        projects = [
            {"id": row.id, "title": row.title, "role": row.partner_role}
            for row in project_result.all()
        ]

        return {
            "campuses": campuses,
            "projects": projects,
            "campuses_count": len(campuses),
            "projects_count": len(projects),
        }
