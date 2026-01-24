"""
Service Core
=============

Logique métier pour la gestion des données de référence (pays).
"""

from uuid import uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.core import Country


# Données ISO 3166-1 pour les pays africains et francophones (sous-ensemble)
ISO_COUNTRIES_DATA = [
    # Afrique
    {"iso_code": "DZ", "iso_code3": "DZA", "name_fr": "Algérie", "name_en": "Algeria", "name_ar": "الجزائر", "phone_code": "+213"},
    {"iso_code": "AO", "iso_code3": "AGO", "name_fr": "Angola", "name_en": "Angola", "name_ar": "أنغولا", "phone_code": "+244"},
    {"iso_code": "BJ", "iso_code3": "BEN", "name_fr": "Bénin", "name_en": "Benin", "name_ar": "بنين", "phone_code": "+229"},
    {"iso_code": "BW", "iso_code3": "BWA", "name_fr": "Botswana", "name_en": "Botswana", "name_ar": "بوتسوانا", "phone_code": "+267"},
    {"iso_code": "BF", "iso_code3": "BFA", "name_fr": "Burkina Faso", "name_en": "Burkina Faso", "name_ar": "بوركينا فاسو", "phone_code": "+226"},
    {"iso_code": "BI", "iso_code3": "BDI", "name_fr": "Burundi", "name_en": "Burundi", "name_ar": "بوروندي", "phone_code": "+257"},
    {"iso_code": "CV", "iso_code3": "CPV", "name_fr": "Cap-Vert", "name_en": "Cape Verde", "name_ar": "الرأس الأخضر", "phone_code": "+238"},
    {"iso_code": "CM", "iso_code3": "CMR", "name_fr": "Cameroun", "name_en": "Cameroon", "name_ar": "الكاميرون", "phone_code": "+237"},
    {"iso_code": "CF", "iso_code3": "CAF", "name_fr": "République centrafricaine", "name_en": "Central African Republic", "name_ar": "جمهورية أفريقيا الوسطى", "phone_code": "+236"},
    {"iso_code": "TD", "iso_code3": "TCD", "name_fr": "Tchad", "name_en": "Chad", "name_ar": "تشاد", "phone_code": "+235"},
    {"iso_code": "KM", "iso_code3": "COM", "name_fr": "Comores", "name_en": "Comoros", "name_ar": "جزر القمر", "phone_code": "+269"},
    {"iso_code": "CG", "iso_code3": "COG", "name_fr": "Congo", "name_en": "Congo", "name_ar": "الكونغو", "phone_code": "+242"},
    {"iso_code": "CD", "iso_code3": "COD", "name_fr": "République démocratique du Congo", "name_en": "Democratic Republic of the Congo", "name_ar": "جمهورية الكونغو الديمقراطية", "phone_code": "+243"},
    {"iso_code": "DJ", "iso_code3": "DJI", "name_fr": "Djibouti", "name_en": "Djibouti", "name_ar": "جيبوتي", "phone_code": "+253"},
    {"iso_code": "EG", "iso_code3": "EGY", "name_fr": "Égypte", "name_en": "Egypt", "name_ar": "مصر", "phone_code": "+20"},
    {"iso_code": "GQ", "iso_code3": "GNQ", "name_fr": "Guinée équatoriale", "name_en": "Equatorial Guinea", "name_ar": "غينيا الاستوائية", "phone_code": "+240"},
    {"iso_code": "ER", "iso_code3": "ERI", "name_fr": "Érythrée", "name_en": "Eritrea", "name_ar": "إريتريا", "phone_code": "+291"},
    {"iso_code": "SZ", "iso_code3": "SWZ", "name_fr": "Eswatini", "name_en": "Eswatini", "name_ar": "إسواتيني", "phone_code": "+268"},
    {"iso_code": "ET", "iso_code3": "ETH", "name_fr": "Éthiopie", "name_en": "Ethiopia", "name_ar": "إثيوبيا", "phone_code": "+251"},
    {"iso_code": "GA", "iso_code3": "GAB", "name_fr": "Gabon", "name_en": "Gabon", "name_ar": "الغابون", "phone_code": "+241"},
    {"iso_code": "GM", "iso_code3": "GMB", "name_fr": "Gambie", "name_en": "Gambia", "name_ar": "غامبيا", "phone_code": "+220"},
    {"iso_code": "GH", "iso_code3": "GHA", "name_fr": "Ghana", "name_en": "Ghana", "name_ar": "غانا", "phone_code": "+233"},
    {"iso_code": "GN", "iso_code3": "GIN", "name_fr": "Guinée", "name_en": "Guinea", "name_ar": "غينيا", "phone_code": "+224"},
    {"iso_code": "GW", "iso_code3": "GNB", "name_fr": "Guinée-Bissau", "name_en": "Guinea-Bissau", "name_ar": "غينيا بيساو", "phone_code": "+245"},
    {"iso_code": "CI", "iso_code3": "CIV", "name_fr": "Côte d'Ivoire", "name_en": "Ivory Coast", "name_ar": "ساحل العاج", "phone_code": "+225"},
    {"iso_code": "KE", "iso_code3": "KEN", "name_fr": "Kenya", "name_en": "Kenya", "name_ar": "كينيا", "phone_code": "+254"},
    {"iso_code": "LS", "iso_code3": "LSO", "name_fr": "Lesotho", "name_en": "Lesotho", "name_ar": "ليسوتو", "phone_code": "+266"},
    {"iso_code": "LR", "iso_code3": "LBR", "name_fr": "Libéria", "name_en": "Liberia", "name_ar": "ليبيريا", "phone_code": "+231"},
    {"iso_code": "LY", "iso_code3": "LBY", "name_fr": "Libye", "name_en": "Libya", "name_ar": "ليبيا", "phone_code": "+218"},
    {"iso_code": "MG", "iso_code3": "MDG", "name_fr": "Madagascar", "name_en": "Madagascar", "name_ar": "مدغشقر", "phone_code": "+261"},
    {"iso_code": "MW", "iso_code3": "MWI", "name_fr": "Malawi", "name_en": "Malawi", "name_ar": "مالاوي", "phone_code": "+265"},
    {"iso_code": "ML", "iso_code3": "MLI", "name_fr": "Mali", "name_en": "Mali", "name_ar": "مالي", "phone_code": "+223"},
    {"iso_code": "MR", "iso_code3": "MRT", "name_fr": "Mauritanie", "name_en": "Mauritania", "name_ar": "موريتانيا", "phone_code": "+222"},
    {"iso_code": "MU", "iso_code3": "MUS", "name_fr": "Maurice", "name_en": "Mauritius", "name_ar": "موريشيوس", "phone_code": "+230"},
    {"iso_code": "MA", "iso_code3": "MAR", "name_fr": "Maroc", "name_en": "Morocco", "name_ar": "المغرب", "phone_code": "+212"},
    {"iso_code": "MZ", "iso_code3": "MOZ", "name_fr": "Mozambique", "name_en": "Mozambique", "name_ar": "موزمبيق", "phone_code": "+258"},
    {"iso_code": "NA", "iso_code3": "NAM", "name_fr": "Namibie", "name_en": "Namibia", "name_ar": "ناميبيا", "phone_code": "+264"},
    {"iso_code": "NE", "iso_code3": "NER", "name_fr": "Niger", "name_en": "Niger", "name_ar": "النيجر", "phone_code": "+227"},
    {"iso_code": "NG", "iso_code3": "NGA", "name_fr": "Nigéria", "name_en": "Nigeria", "name_ar": "نيجيريا", "phone_code": "+234"},
    {"iso_code": "RW", "iso_code3": "RWA", "name_fr": "Rwanda", "name_en": "Rwanda", "name_ar": "رواندا", "phone_code": "+250"},
    {"iso_code": "ST", "iso_code3": "STP", "name_fr": "Sao Tomé-et-Principe", "name_en": "São Tomé and Príncipe", "name_ar": "ساو تومي وبرينسيبي", "phone_code": "+239"},
    {"iso_code": "SN", "iso_code3": "SEN", "name_fr": "Sénégal", "name_en": "Senegal", "name_ar": "السنغال", "phone_code": "+221"},
    {"iso_code": "SC", "iso_code3": "SYC", "name_fr": "Seychelles", "name_en": "Seychelles", "name_ar": "سيشيل", "phone_code": "+248"},
    {"iso_code": "SL", "iso_code3": "SLE", "name_fr": "Sierra Leone", "name_en": "Sierra Leone", "name_ar": "سيراليون", "phone_code": "+232"},
    {"iso_code": "SO", "iso_code3": "SOM", "name_fr": "Somalie", "name_en": "Somalia", "name_ar": "الصومال", "phone_code": "+252"},
    {"iso_code": "ZA", "iso_code3": "ZAF", "name_fr": "Afrique du Sud", "name_en": "South Africa", "name_ar": "جنوب أفريقيا", "phone_code": "+27"},
    {"iso_code": "SS", "iso_code3": "SSD", "name_fr": "Soudan du Sud", "name_en": "South Sudan", "name_ar": "جنوب السودان", "phone_code": "+211"},
    {"iso_code": "SD", "iso_code3": "SDN", "name_fr": "Soudan", "name_en": "Sudan", "name_ar": "السودان", "phone_code": "+249"},
    {"iso_code": "TZ", "iso_code3": "TZA", "name_fr": "Tanzanie", "name_en": "Tanzania", "name_ar": "تنزانيا", "phone_code": "+255"},
    {"iso_code": "TG", "iso_code3": "TGO", "name_fr": "Togo", "name_en": "Togo", "name_ar": "توغو", "phone_code": "+228"},
    {"iso_code": "TN", "iso_code3": "TUN", "name_fr": "Tunisie", "name_en": "Tunisia", "name_ar": "تونس", "phone_code": "+216"},
    {"iso_code": "UG", "iso_code3": "UGA", "name_fr": "Ouganda", "name_en": "Uganda", "name_ar": "أوغندا", "phone_code": "+256"},
    {"iso_code": "ZM", "iso_code3": "ZMB", "name_fr": "Zambie", "name_en": "Zambia", "name_ar": "زامبيا", "phone_code": "+260"},
    {"iso_code": "ZW", "iso_code3": "ZWE", "name_fr": "Zimbabwe", "name_en": "Zimbabwe", "name_ar": "زيمبابوي", "phone_code": "+263"},
    # Europe francophone
    {"iso_code": "BE", "iso_code3": "BEL", "name_fr": "Belgique", "name_en": "Belgium", "name_ar": "بلجيكا", "phone_code": "+32"},
    {"iso_code": "FR", "iso_code3": "FRA", "name_fr": "France", "name_en": "France", "name_ar": "فرنسا", "phone_code": "+33"},
    {"iso_code": "LU", "iso_code3": "LUX", "name_fr": "Luxembourg", "name_en": "Luxembourg", "name_ar": "لوكسمبورغ", "phone_code": "+352"},
    {"iso_code": "MC", "iso_code3": "MCO", "name_fr": "Monaco", "name_en": "Monaco", "name_ar": "موناكو", "phone_code": "+377"},
    {"iso_code": "CH", "iso_code3": "CHE", "name_fr": "Suisse", "name_en": "Switzerland", "name_ar": "سويسرا", "phone_code": "+41"},
    # Amérique
    {"iso_code": "CA", "iso_code3": "CAN", "name_fr": "Canada", "name_en": "Canada", "name_ar": "كندا", "phone_code": "+1"},
    {"iso_code": "HT", "iso_code3": "HTI", "name_fr": "Haïti", "name_en": "Haiti", "name_ar": "هايتي", "phone_code": "+509"},
    # Asie / Moyen-Orient
    {"iso_code": "LB", "iso_code3": "LBN", "name_fr": "Liban", "name_en": "Lebanon", "name_ar": "لبنان", "phone_code": "+961"},
    # Océanie
    {"iso_code": "VU", "iso_code3": "VUT", "name_fr": "Vanuatu", "name_en": "Vanuatu", "name_ar": "فانواتو", "phone_code": "+678"},
]


class CoreService:
    """Service pour la gestion des données de référence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # COUNTRIES
    # =========================================================================

    async def get_countries(
        self,
        search: str | None = None,
        active: bool | None = None,
    ) -> select:
        """
        Construit une requête pour lister les pays.

        Args:
            search: Recherche sur code ISO ou nom.
            active: Filtrer par statut actif.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(Country)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Country.iso_code.ilike(search_filter),
                    Country.iso_code3.ilike(search_filter),
                    Country.name_fr.ilike(search_filter),
                    Country.name_en.ilike(search_filter),
                    Country.name_ar.ilike(search_filter),
                )
            )

        if active is not None:
            query = query.where(Country.active == active)

        return query

    async def get_country_by_id(self, country_id: str) -> Country | None:
        """Récupère un pays par son ID."""
        result = await self.db.execute(
            select(Country).where(Country.id == country_id)
        )
        return result.scalar_one_or_none()

    async def get_country_by_iso_code(self, iso_code: str) -> Country | None:
        """Récupère un pays par son code ISO."""
        result = await self.db.execute(
            select(Country).where(Country.iso_code == iso_code.upper())
        )
        return result.scalar_one_or_none()

    async def create_country(
        self,
        iso_code: str,
        name_fr: str,
        **kwargs,
    ) -> Country:
        """
        Crée un nouveau pays.

        Args:
            iso_code: Code ISO 2 lettres.
            name_fr: Nom en français.
            **kwargs: Autres champs optionnels.

        Returns:
            Pays créé.

        Raises:
            ConflictException: Si le code ISO existe déjà.
        """
        iso_code = iso_code.upper()
        existing = await self.get_country_by_iso_code(iso_code)
        if existing:
            raise ConflictException(f"Un pays avec le code ISO '{iso_code}' existe déjà")

        # Vérifier iso_code3 si fourni
        if "iso_code3" in kwargs and kwargs["iso_code3"]:
            kwargs["iso_code3"] = kwargs["iso_code3"].upper()
            result = await self.db.execute(
                select(Country).where(Country.iso_code3 == kwargs["iso_code3"])
            )
            if result.scalar_one_or_none():
                raise ConflictException(
                    f"Un pays avec le code ISO3 '{kwargs['iso_code3']}' existe déjà"
                )

        country = Country(
            id=str(uuid4()),
            iso_code=iso_code,
            name_fr=name_fr,
            **kwargs,
        )
        self.db.add(country)
        await self.db.flush()
        return country

    async def update_country(self, country_id: str, **kwargs) -> Country:
        """
        Met à jour un pays.

        Args:
            country_id: ID du pays.
            **kwargs: Champs à mettre à jour.

        Returns:
            Pays mis à jour.

        Raises:
            NotFoundException: Si le pays n'existe pas.
            ConflictException: Si le nouveau code ISO existe déjà.
        """
        country = await self.get_country_by_id(country_id)
        if not country:
            raise NotFoundException("Pays non trouvé")

        # Vérifier l'unicité du code ISO si modifié
        if "iso_code" in kwargs and kwargs["iso_code"]:
            kwargs["iso_code"] = kwargs["iso_code"].upper()
            if kwargs["iso_code"] != country.iso_code:
                existing = await self.get_country_by_iso_code(kwargs["iso_code"])
                if existing:
                    raise ConflictException(
                        f"Un pays avec le code ISO '{kwargs['iso_code']}' existe déjà"
                    )

        # Vérifier iso_code3 si modifié
        if "iso_code3" in kwargs and kwargs["iso_code3"]:
            kwargs["iso_code3"] = kwargs["iso_code3"].upper()
            if kwargs["iso_code3"] != country.iso_code3:
                result = await self.db.execute(
                    select(Country).where(Country.iso_code3 == kwargs["iso_code3"])
                )
                if result.scalar_one_or_none():
                    raise ConflictException(
                        f"Un pays avec le code ISO3 '{kwargs['iso_code3']}' existe déjà"
                    )

        await self.db.execute(
            update(Country).where(Country.id == country_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_country_by_id(country_id)

    async def toggle_country_active(self, country_id: str) -> Country:
        """Bascule le statut actif d'un pays."""
        country = await self.get_country_by_id(country_id)
        if not country:
            raise NotFoundException("Pays non trouvé")

        await self.db.execute(
            update(Country)
            .where(Country.id == country_id)
            .values(active=not country.active)
        )
        await self.db.flush()
        return await self.get_country_by_id(country_id)

    async def bulk_toggle_countries(
        self, country_ids: list[str], active: bool
    ) -> int:
        """
        Bascule le statut actif de plusieurs pays.

        Args:
            country_ids: Liste des IDs de pays.
            active: Nouveau statut actif.

        Returns:
            Nombre de pays modifiés.
        """
        result = await self.db.execute(
            update(Country)
            .where(Country.id.in_(country_ids))
            .values(active=active)
        )
        return result.rowcount

    async def import_iso_countries(self, overwrite_existing: bool = False) -> dict:
        """
        Importe les pays depuis les données ISO.

        Args:
            overwrite_existing: Écraser les pays existants.

        Returns:
            Statistiques de l'import.
        """
        created = 0
        updated = 0
        skipped = 0

        for country_data in ISO_COUNTRIES_DATA:
            existing = await self.get_country_by_iso_code(country_data["iso_code"])

            if existing:
                if overwrite_existing:
                    await self.db.execute(
                        update(Country)
                        .where(Country.id == existing.id)
                        .values(**country_data)
                    )
                    updated += 1
                else:
                    skipped += 1
            else:
                country = Country(
                    id=str(uuid4()),
                    **country_data,
                    active=True,
                )
                self.db.add(country)
                created += 1

        await self.db.flush()

        return {
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "total": len(ISO_COUNTRIES_DATA),
        }
