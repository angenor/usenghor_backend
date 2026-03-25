"""
Service Short Links
====================

Logique métier pour le réducteur de liens.
"""

from urllib.parse import urlparse
from uuid import uuid4

from sqlalchemy import delete, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.short_links import AllowedDomain, ShortLink

BASE36_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
MAX_COUNTER = 1_679_615  # zzzz en base 36


def int_to_base36(n: int) -> str:
    """Convertit un entier en base 36 (alphabet 0-9a-z)."""
    if n < 0:
        raise ValueError("Le nombre doit être positif")
    if n == 0:
        return "0"
    result = []
    while n > 0:
        result.append(BASE36_ALPHABET[n % 36])
        n //= 36
    return "".join(reversed(result))


class ShortLinkService:
    """Service pour la gestion des liens courts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_target_url(self, target_url: str) -> None:
        """
        Valide l'URL de destination.

        Raises:
            ValidationException: Si l'URL est invalide.
        """
        if not target_url or not target_url.strip():
            raise ValidationException("L'URL de destination ne peut pas être vide")

        # Anti-boucle : rejeter les URLs /r/...
        if target_url.startswith("/r/") or target_url.startswith("/r"):
            raise ValidationException(
                "L'URL de destination ne doit pas pointer vers un lien réduit (/r/...)"
            )

        # URL interne (chemin relatif commençant par /)
        if target_url.startswith("/"):
            return

        # URL externe : parser et vérifier le domaine
        try:
            parsed = urlparse(target_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationException(
                    "L'URL externe doit être une URL complète (ex: https://exemple.com)"
                )
            domain = parsed.netloc.lower()
            # Retirer le port si présent
            if ":" in domain:
                domain = domain.split(":")[0]
        except Exception:
            raise ValidationException("Format d'URL invalide")

        # Domaines internes de la plateforme — toujours autorisés
        internal_domains = {
            "usenghor-francophonie.org",
            "www.usenghor-francophonie.org",
        }
        if domain in internal_domains:
            return

        # Vérifier que le domaine (ou son domaine parent) est dans la liste blanche
        # Ex: "www.google.com" matche "google.com", "docs.google.com" aussi
        result = await self.db.execute(select(AllowedDomain))
        allowed = [row.domain for row in result.scalars().all()]
        if not any(domain == d or domain.endswith(f".{d}") for d in allowed):
            raise ValidationException(
                f"Le domaine '{domain}' n'est pas dans la liste des domaines autorisés"
            )

    async def create_short_link(
        self, target_url: str, created_by: str | None = None
    ) -> ShortLink:
        """
        Crée un nouveau lien court.

        Args:
            target_url: URL de destination.
            created_by: ID de l'utilisateur créateur.

        Returns:
            Lien court créé.
        """
        # Valider l'URL
        await self.validate_target_url(target_url)

        # Obtenir le prochain compteur
        try:
            result = await self.db.execute(text("SELECT nextval('short_link_counter_seq')"))
            counter = result.scalar()
        except Exception:
            raise ValidationException(
                "Capacité maximale atteinte (1 679 616 liens). "
                "Impossible de créer de nouveaux liens courts."
            )

        if counter > MAX_COUNTER:
            raise ValidationException(
                "Capacité maximale atteinte (1 679 616 liens). "
                "Impossible de créer de nouveaux liens courts."
            )

        # Convertir en base 36
        code = int_to_base36(counter)

        # Créer le lien
        short_link = ShortLink(
            id=str(uuid4()),
            code=code,
            target_url=target_url.strip(),
            created_by=created_by,
        )
        self.db.add(short_link)
        await self.db.flush()
        return short_link

    async def get_by_code(self, code: str) -> ShortLink | None:
        """Récupère un lien court par son code."""
        result = await self.db.execute(
            select(ShortLink).where(ShortLink.code == code.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, link_id: str) -> ShortLink | None:
        """Récupère un lien court par son ID."""
        result = await self.db.execute(
            select(ShortLink).where(ShortLink.id == link_id)
        )
        return result.scalar_one_or_none()

    async def list_short_links(self, search: str | None = None) -> select:
        """
        Construit une requête pour lister les liens courts.

        Args:
            search: Recherche sur code ou target_url.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(ShortLink)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    ShortLink.code.ilike(search_filter),
                    ShortLink.target_url.ilike(search_filter),
                )
            )

        query = query.order_by(ShortLink.created_at.desc())
        return query

    async def delete_short_link(self, link_id: str) -> None:
        """
        Supprime un lien court par son ID.

        Raises:
            NotFoundException: Si le lien n'existe pas.
        """
        link = await self.get_by_id(link_id)
        if not link:
            raise NotFoundException("Lien court non trouvé")

        await self.db.execute(delete(ShortLink).where(ShortLink.id == link_id))
        await self.db.flush()

    # --- Gestion des domaines autorisés ---

    async def list_allowed_domains(self) -> list[AllowedDomain]:
        """Liste tous les domaines autorisés."""
        result = await self.db.execute(
            select(AllowedDomain).order_by(AllowedDomain.domain)
        )
        return list(result.scalars().all())

    async def add_allowed_domain(self, domain: str) -> AllowedDomain:
        """Ajoute un domaine à la liste blanche."""
        domain = domain.lower().strip()
        # Vérifier l'unicité
        result = await self.db.execute(
            select(AllowedDomain).where(AllowedDomain.domain == domain)
        )
        if result.scalar_one_or_none():
            raise ValidationException(f"Le domaine '{domain}' existe déjà")

        allowed = AllowedDomain(
            id=str(uuid4()),
            domain=domain,
        )
        self.db.add(allowed)
        await self.db.flush()
        return allowed

    async def remove_allowed_domain(self, domain_id: str) -> None:
        """Supprime un domaine de la liste blanche."""
        result = await self.db.execute(
            select(AllowedDomain).where(AllowedDomain.id == domain_id)
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Domaine non trouvé")

        await self.db.execute(
            delete(AllowedDomain).where(AllowedDomain.id == domain_id)
        )
        await self.db.flush()
