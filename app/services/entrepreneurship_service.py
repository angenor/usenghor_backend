"""
Service Entrepreneuriat (PEI)
=============================

Logique métier du Pôle Entrepreneuriat et Innovation : dispositifs, cohortes,
ressources, portraits (lauréats FSE / étudiants-entrepreneurs) et partenaires du
pôle (CRUD admin, réordonnancement, activation / publication, traduction
automatique FR → EN/AR, tableau de bord) et lecture publique.

Toute écriture produit une entrée ``audit_logs`` explicite (``_audit``), avec
``record_id`` = UUID de la ligne ou ``None`` pour les actions en lot.
"""

import enum
import time
from types import SimpleNamespace
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import exists, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.core.media_utils import resolve_media_url
from app.models.entrepreneurship import (
    PeiCohort,
    PeiCohortType,
    PeiLaureate,
    PeiLaureateType,
    PeiPartner,
    PeiPartnerFamily,
    PeiProgram,
    PeiProgramPhase,
    PeiResource,
    PeiResourceType,
)
from app.models.faq import FaqCategory, FaqEntry
from app.models.media import Media
from app.models.organization import Service
from app.models.partner import Partner
from app.schemas.entrepreneurship import (
    MSG_DOCUMENT_REQUIRED,
    MSG_URL_REQUIRED,
    QUOTE_MAX_LEN,
    ActiveStatus,
    FeaturedStatus,
    PeiActiveCount,
    PeiCohortAdmin,
    PeiCohortCreate,
    PeiCohortPublic,
    PeiCohortsAdminPage,
    PeiCohortTranslateRequest,
    PeiCohortTranslateResponse,
    PeiCohortUpdate,
    PeiDashboardStats,
    PeiDdeService,
    PeiLaureateAdmin,
    PeiLaureateCohortRef,
    PeiLaureateCreate,
    PeiLaureateGroupPublic,
    PeiLaureatePublic,
    PeiLaureatesAdminPage,
    PeiLaureatesPublic,
    PeiLaureateStatsPublic,
    PeiLaureateTranslateRequest,
    PeiLaureateTranslateResponse,
    PeiLaureateUpdate,
    PeiPartnerAvailable,
    PeiPartnerEmbedded,
    PeiPartnerFamilyPublic,
    PeiPartnerLinkAdmin,
    PeiPartnerLinkCreate,
    PeiPartnerPublic,
    PeiProgramAdmin,
    PeiProgramCreate,
    PeiProgramPublic,
    PeiProgramsAdminPage,
    PeiProgramTranslateRequest,
    PeiProgramTranslateResponse,
    PeiProgramUpdate,
    PeiPublishedCount,
    PeiResourceAdmin,
    PeiResourceCreate,
    PeiResourcePublic,
    PeiResourcesAdminPage,
    PeiResourceTranslateRequest,
    PeiResourceTranslateResponse,
    PeiResourceUpdate,
    PeiTranslateMissingResponse,
    PublishStatus,
    ReorderResponse,
)
from app.services import translation_service
from app.services.editorial_service import EditorialService
from app.services.faq_service import FaqService
from app.services.identity_service import IdentityService

# Budget (secondes) d'un appel « Traduire les champs manquants », sous le
# proxy_read_timeout de nginx (90 s).
TRANSLATE_MISSING_TIME_BUDGET = 50.0

# Champs traduisibles (base_attr FR, kind) — convention additive (research R8).
_PROGRAM_TRANSLATABLE = [
    ("title", "text"),
    ("tagline", "text"),
    ("highlight", "text"),
    ("content_html", "html"),
    ("content_md", "text"),
]
_COHORT_TRANSLATABLE = [
    ("label", "text"),
    ("focus", "text"),
    ("summary_html", "html"),
    ("summary_md", "text"),
]
_RESOURCE_TRANSLATABLE = [
    ("title", "text"),
    ("description", "text"),
    ("category", "text"),
]
_LAUREATE_TRANSLATABLE = [
    ("department_label", "text"),
    ("quote", "text"),
]

# Ordre fixe des familles de partenaires (= ordre de déclaration de l'ENUM SQL).
PARTNER_FAMILY_ORDER = [
    PeiPartnerFamily.ACADEMIC,
    PeiPartnerFamily.SUPPORT,
    PeiPartnerFamily.INTERNATIONAL,
]

# Type de cohorte attendu pour chaque type de portrait (research R3).
_LAUREATE_COHORT_TYPE = {
    PeiLaureateType.FSE_LAUREATE.value: (
        PeiCohortType.FSE.value,
        "Un lauréat FSE doit appartenir à une cohorte FSE",
    ),
    PeiLaureateType.STUDENT_ENTREPRENEUR.value: (
        PeiCohortType.SEE.value,
        "Un étudiant-entrepreneur doit appartenir à une cohorte SEE",
    ),
}

DDE_SERVICE_KEY = "entrepreneurship.dde_service_id"


# ---------------------------------------------------------------------------
# Helpers de module
# ---------------------------------------------------------------------------


def _is_uuid(value: str | None) -> bool:
    if not value:
        return False
    try:
        UUID(str(value))
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def _jsonable(value):
    """Convertit une valeur ORM en valeur sérialisable JSONB (audit)."""
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return value


def _clamp_page(page: int, page_size: int) -> tuple[int, int]:
    return max(1, page), max(1, min(page_size, 100))


def _enum_value(value):
    return value.value if isinstance(value, enum.Enum) else value


def _format_amount(value) -> str | None:
    return None if value is None else f"{value:.2f}"


def _clamp_text(value: str | None, max_len: int = QUOTE_MAX_LEN) -> str | None:
    """Tronque proprement un texte trop long (coupure au dernier espace + « … »)."""
    if value is None or len(value) <= max_len:
        return value
    cut = value[: max_len - 1]
    space = cut.rfind(" ")
    if space > max_len // 2:
        cut = cut[:space]
    return cut.rstrip() + "…"


def _scope_conditions(model, scope: dict | None) -> list:
    return [getattr(model, key) == value for key, value in (scope or {}).items()]


def _translated_attrs(fields) -> list[str]:
    return [
        translation_service._lang_attr(base, lang)
        for base, _ in fields
        for lang in translation_service.SUPPORTED_TARGETS
    ]


class EntrepreneurshipService:
    """Service métier du pôle Entrepreneuriat et Innovation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ======================================================================
    # Helpers privés
    # ======================================================================

    async def _audit(
        self,
        action: str,
        user_id: str | None,
        record_id: str | None,
        table_name: str | None,
        old_values: dict | None = None,
        new_values: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        await IdentityService(self.db).create_audit_log(
            action=action,
            user_id=user_id,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def _next_display_order(self, model, **scope) -> int:
        """``MAX(display_order) + 1`` dans la portée (0 si elle est vide)."""
        result = await self.db.execute(
            select(func.max(model.display_order)).where(*_scope_conditions(model, scope))
        )
        current = result.scalar()
        return 0 if current is None else current + 1

    async def _renumber(self, model, **scope) -> None:
        """Renumérote ``display_order`` 0..n-1 dans une portée (sans commit)."""
        pk = model.__mapper__.primary_key[0]
        result = await self.db.execute(
            select(pk, model.display_order)
            .where(*_scope_conditions(model, scope))
            .order_by(model.display_order.asc(), model.created_at.asc())
        )
        for index, (row_id, order) in enumerate(result.all()):
            if order != index:
                await self.db.execute(
                    update(model).where(pk == row_id).values(display_order=index)
                )

    async def _reorder(
        self,
        model,
        ids: list[str],
        table_name: str,
        action: str,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        *,
        scope: dict | None = None,
    ) -> ReorderResponse:
        """Renumérote ``display_order = index`` (0..n-1) à partir d'une liste complète.

        ``scope`` (ex. ``{"cohort_id": …}`` ou ``{"family": …}``) restreint la
        liste attendue aux lignes de cette portée ; sans portée, toute la table.
        """
        if len(set(ids)) != len(ids):
            raise ValidationException("Liste invalide : identifiants en double")

        pk = model.__mapper__.primary_key[0]
        result = await self.db.execute(
            select(pk, model.display_order).where(*_scope_conditions(model, scope))
        )
        current = {str(row_id): order for row_id, order in result.all()}

        unknown = [i for i in ids if i not in current]
        if unknown:
            label = "inconnu(s) ou hors portée" if scope else "inconnu(s)"
            raise ValidationException(
                f"Identifiant(s) {label} : {', '.join(unknown)}"
            )
        missing = [i for i in current if i not in set(ids)]
        if missing:
            raise ValidationException(
                f"Liste incomplète : {len(missing)} identifiant(s) manquant(s)"
            )

        updated = 0
        for index, item_id in enumerate(ids):
            if current[item_id] != index:
                await self.db.execute(
                    update(model).where(pk == item_id).values(display_order=index)
                )
                updated += 1

        scope_values = {key: _jsonable(value) for key, value in (scope or {}).items()}
        await self._audit(
            action,
            user_id=user_id,
            record_id=None,
            table_name=table_name,
            new_values={**scope_values, "ids": ids},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        return ReorderResponse(updated=updated)

    @staticmethod
    def _media_url(media: Media | None) -> str | None:
        return resolve_media_url(media)

    async def _load_media(self, media_id: str | None) -> Media | None:
        if not _is_uuid(media_id):
            return None
        result = await self.db.execute(select(Media).where(Media.id == media_id))
        return result.scalar_one_or_none()

    async def _get_or_404(self, model, item_id: str, message: str):
        if not _is_uuid(item_id):
            raise NotFoundException(message)
        result = await self.db.execute(select(model).where(model.id == item_id))
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NotFoundException(message)
        return obj

    async def _assert_code_available(
        self, model, code: str, exclude_id: str | None = None
    ) -> None:
        stmt = select(model.id).where(model.code == code)
        if exclude_id:
            stmt = stmt.where(model.id != exclude_id)
        result = await self.db.execute(stmt)
        if result.first() is not None:
            raise ConflictException(f"Code déjà utilisé : {code}")

    @staticmethod
    async def _translate_request(data, fields) -> dict:
        """Traduit les champs FR d'une requête en EN/AR (sans persistance)."""
        out: dict[str, str | None] = {}
        for base, kind in fields:
            src = getattr(data, base, None)
            if not src:
                continue
            translate = (
                translation_service.translate_html
                if kind == "html"
                else translation_service.translate_text
            )
            for lang in translation_service.SUPPORTED_TARGETS:
                out[translation_service._lang_attr(base, lang)] = await translate(
                    src, lang
                )
        return out

    async def _apply_update(
        self,
        obj,
        changes: dict,
        fields,
        user_id: str | None,
    ) -> dict:
        """Applique ``changes`` sur ``obj``, complète les traductions vides.

        Renvoie les anciennes valeurs (JSON) des champs modifiés.
        """
        old: dict = {}
        for key, value in changes.items():
            old[key] = _jsonable(getattr(obj, key))
            setattr(obj, key, value)
        obj.updated_by = user_id
        await translation_service.autofill_translations(obj, fields)
        return old

    # ======================================================================
    # Dispositifs (pei_programs)
    # ======================================================================

    def _program_admin(self, program: PeiProgram, media: Media | None) -> PeiProgramAdmin:
        schema = PeiProgramAdmin.model_validate(program)
        schema.cover_image_url = self._media_url(media)
        return schema

    def _program_public(self, program: PeiProgram, media: Media | None) -> PeiProgramPublic:
        schema = PeiProgramPublic.model_validate(program)
        schema.cover_image_url = self._media_url(media)
        return schema

    async def list_programs(
        self,
        q: str | None = None,
        phase: PeiProgramPhase | None = None,
        active: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PeiProgramsAdminPage:
        page, page_size = _clamp_page(page, page_size)
        conditions = []
        if q:
            conditions.append(PeiProgram.title.ilike(f"%{q}%"))
        if phase is not None:
            conditions.append(PeiProgram.phase == phase)
        if active is not None:
            conditions.append(PeiProgram.active.is_(active))

        total = (
            await self.db.execute(select(func.count(PeiProgram.id)).where(*conditions))
        ).scalar() or 0

        result = await self.db.execute(
            select(PeiProgram, Media)
            .outerjoin(Media, PeiProgram.cover_image_external_id == Media.id)
            .where(*conditions)
            .order_by(PeiProgram.display_order.asc(), PeiProgram.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [self._program_admin(p, m) for p, m in result.all()]
        return PeiProgramsAdminPage(
            items=items, total=total, page=page, page_size=page_size
        )

    async def get_program(self, program_id: str) -> PeiProgramAdmin:
        program = await self._get_or_404(PeiProgram, program_id, "Dispositif introuvable")
        media = await self._load_media(program.cover_image_external_id)
        return self._program_admin(program, media)

    async def create_program(
        self,
        data: PeiProgramCreate,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PeiProgramAdmin:
        await self._assert_code_available(PeiProgram, data.code)

        program = PeiProgram(
            **data.model_dump(),
            display_order=await self._next_display_order(PeiProgram),
            created_by=user_id,
            updated_by=user_id,
        )
        await translation_service.autofill_translations(program, _PROGRAM_TRANSLATABLE)
        self.db.add(program)
        await self.db.flush()

        await self._audit(
            "entrepreneurship.program.create",
            user_id=user_id,
            record_id=program.id,
            table_name="pei_programs",
            new_values=data.model_dump(mode="json"),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(program)
        return await self.get_program(program.id)

    async def update_program(
        self,
        program_id: str,
        data: PeiProgramUpdate,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PeiProgramAdmin:
        program = await self._get_or_404(PeiProgram, program_id, "Dispositif introuvable")
        changes = data.model_dump(exclude_unset=True)
        if "code" in changes and changes["code"] != program.code:
            await self._assert_code_available(PeiProgram, changes["code"], program.id)

        old = await self._apply_update(program, changes, _PROGRAM_TRANSLATABLE, user_id)
        await self.db.flush()

        await self._audit(
            "entrepreneurship.program.update",
            user_id=user_id,
            record_id=program.id,
            table_name="pei_programs",
            old_values=old,
            new_values=data.model_dump(mode="json", exclude_unset=True),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(program)
        return await self.get_program(program.id)

    async def delete_program(
        self,
        program_id: str,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        program = await self._get_or_404(PeiProgram, program_id, "Dispositif introuvable")
        old = {"code": program.code, "title": program.title, "phase": _jsonable(program.phase)}
        record_id = program.id
        await self.db.delete(program)
        await self._audit(
            "entrepreneurship.program.delete",
            user_id=user_id,
            record_id=record_id,
            table_name="pei_programs",
            old_values=old,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()

    async def set_program_active(
        self,
        program_id: str,
        active: bool,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ActiveStatus:
        program = await self._get_or_404(PeiProgram, program_id, "Dispositif introuvable")
        old_active = program.active
        program.active = active
        program.updated_by = user_id
        await self.db.flush()
        await self._audit(
            "entrepreneurship.program.activate"
            if active
            else "entrepreneurship.program.deactivate",
            user_id=user_id,
            record_id=program.id,
            table_name="pei_programs",
            old_values={"active": old_active},
            new_values={"active": active},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(program)
        return ActiveStatus.model_validate(program)

    async def reorder_programs(
        self,
        ids: list[str],
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ReorderResponse:
        return await self._reorder(
            PeiProgram,
            ids,
            "pei_programs",
            "entrepreneurship.program.reorder",
            user_id,
            ip_address,
            user_agent,
        )

    async def translate_program_fields(
        self, data: PeiProgramTranslateRequest
    ) -> PeiProgramTranslateResponse:
        return PeiProgramTranslateResponse(
            **await self._translate_request(data, _PROGRAM_TRANSLATABLE)
        )

    async def list_public_programs(self) -> list[PeiProgramPublic]:
        result = await self.db.execute(
            select(PeiProgram, Media)
            .outerjoin(Media, PeiProgram.cover_image_external_id == Media.id)
            .where(PeiProgram.active.is_(True))
            .order_by(PeiProgram.display_order.asc(), PeiProgram.created_at.asc())
        )
        return [self._program_public(p, m) for p, m in result.all()]

    async def get_public_program(self, code: str) -> PeiProgramPublic:
        result = await self.db.execute(
            select(PeiProgram, Media)
            .outerjoin(Media, PeiProgram.cover_image_external_id == Media.id)
            .where(PeiProgram.code == code, PeiProgram.active.is_(True))
        )
        row = result.first()
        if row is None:
            raise NotFoundException("Dispositif introuvable")
        return self._program_public(row[0], row[1])

    # ======================================================================
    # Cohortes (pei_cohorts)
    # ======================================================================

    async def list_cohorts(
        self,
        q: str | None = None,
        type: PeiCohortType | None = None,  # noqa: A002 - nom du paramètre d'API
        active: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PeiCohortsAdminPage:
        page, page_size = _clamp_page(page, page_size)
        conditions = []
        if q:
            conditions.append(PeiCohort.label.ilike(f"%{q}%"))
        if type is not None:
            conditions.append(PeiCohort.type == type)
        if active is not None:
            conditions.append(PeiCohort.active.is_(active))

        total = (
            await self.db.execute(select(func.count(PeiCohort.id)).where(*conditions))
        ).scalar() or 0
        result = await self.db.execute(
            select(PeiCohort)
            .where(*conditions)
            .order_by(PeiCohort.display_order.asc(), PeiCohort.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [PeiCohortAdmin.model_validate(c) for c in result.scalars().all()]
        return PeiCohortsAdminPage(
            items=items, total=total, page=page, page_size=page_size
        )

    async def get_cohort(self, cohort_id: str) -> PeiCohortAdmin:
        cohort = await self._get_or_404(PeiCohort, cohort_id, "Cohorte introuvable")
        return PeiCohortAdmin.model_validate(cohort)

    async def create_cohort(
        self,
        data: PeiCohortCreate,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PeiCohortAdmin:
        await self._assert_code_available(PeiCohort, data.code)

        cohort = PeiCohort(
            **data.model_dump(),
            display_order=await self._next_display_order(PeiCohort),
            created_by=user_id,
            updated_by=user_id,
        )
        await translation_service.autofill_translations(cohort, _COHORT_TRANSLATABLE)
        self.db.add(cohort)
        await self.db.flush()

        await self._audit(
            "entrepreneurship.cohort.create",
            user_id=user_id,
            record_id=cohort.id,
            table_name="pei_cohorts",
            new_values=data.model_dump(mode="json"),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(cohort)
        return PeiCohortAdmin.model_validate(cohort)

    async def update_cohort(
        self,
        cohort_id: str,
        data: PeiCohortUpdate,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PeiCohortAdmin:
        cohort = await self._get_or_404(PeiCohort, cohort_id, "Cohorte introuvable")
        changes = data.model_dump(exclude_unset=True)
        if "code" in changes and changes["code"] != cohort.code:
            await self._assert_code_available(PeiCohort, changes["code"], cohort.id)

        old = await self._apply_update(cohort, changes, _COHORT_TRANSLATABLE, user_id)
        await self.db.flush()

        await self._audit(
            "entrepreneurship.cohort.update",
            user_id=user_id,
            record_id=cohort.id,
            table_name="pei_cohorts",
            old_values=old,
            new_values=data.model_dump(mode="json", exclude_unset=True),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(cohort)
        return PeiCohortAdmin.model_validate(cohort)

    async def _assert_cohort_deletable(self, cohort: PeiCohort) -> None:
        """Refuse (409) la suppression d'une cohorte référencée par des portraits."""
        count = (
            await self.db.execute(
                select(func.count(PeiLaureate.id)).where(PeiLaureate.cohort_id == cohort.id)
            )
        ).scalar() or 0
        if count > 0:
            raise ConflictException(f"Cohorte utilisée par {count} lauréats")

    async def delete_cohort(
        self,
        cohort_id: str,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        cohort = await self._get_or_404(PeiCohort, cohort_id, "Cohorte introuvable")
        await self._assert_cohort_deletable(cohort)
        old = {
            "code": cohort.code,
            "label": cohort.label,
            "year": cohort.year,
            "type": _jsonable(cohort.type),
        }
        record_id = cohort.id
        await self.db.delete(cohort)
        await self._audit(
            "entrepreneurship.cohort.delete",
            user_id=user_id,
            record_id=record_id,
            table_name="pei_cohorts",
            old_values=old,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()

    async def set_cohort_active(
        self,
        cohort_id: str,
        active: bool,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ActiveStatus:
        cohort = await self._get_or_404(PeiCohort, cohort_id, "Cohorte introuvable")
        old_active = cohort.active
        cohort.active = active
        cohort.updated_by = user_id
        await self.db.flush()
        await self._audit(
            "entrepreneurship.cohort.activate"
            if active
            else "entrepreneurship.cohort.deactivate",
            user_id=user_id,
            record_id=cohort.id,
            table_name="pei_cohorts",
            old_values={"active": old_active},
            new_values={"active": active},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(cohort)
        return ActiveStatus.model_validate(cohort)

    async def reorder_cohorts(
        self,
        ids: list[str],
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ReorderResponse:
        return await self._reorder(
            PeiCohort,
            ids,
            "pei_cohorts",
            "entrepreneurship.cohort.reorder",
            user_id,
            ip_address,
            user_agent,
        )

    async def translate_cohort_fields(
        self, data: PeiCohortTranslateRequest
    ) -> PeiCohortTranslateResponse:
        return PeiCohortTranslateResponse(
            **await self._translate_request(data, _COHORT_TRANSLATABLE)
        )

    async def list_public_cohorts(
        self, type: PeiCohortType | None = None  # noqa: A002
    ) -> list[PeiCohortPublic]:
        stmt = select(PeiCohort).where(PeiCohort.active.is_(True))
        if type is not None:
            stmt = stmt.where(PeiCohort.type == type)
        result = await self.db.execute(
            stmt.order_by(PeiCohort.display_order.asc(), PeiCohort.created_at.asc())
        )
        return [PeiCohortPublic.model_validate(c) for c in result.scalars().all()]

    async def get_public_cohort(self, code: str) -> PeiCohortPublic:
        result = await self.db.execute(
            select(PeiCohort).where(
                PeiCohort.code == code, PeiCohort.active.is_(True)
            )
        )
        cohort = result.scalar_one_or_none()
        if cohort is None:
            raise NotFoundException("Cohorte introuvable")
        return PeiCohortPublic.model_validate(cohort)

    # ======================================================================
    # Ressources (pei_resources)
    # ======================================================================

    @staticmethod
    def _validate_resource_source(obj) -> None:
        """Cohérence type / source (miroir de ``chk_pei_resources_source``)."""
        raw_type = obj.type.value if isinstance(obj.type, enum.Enum) else obj.type
        if raw_type == PeiResourceType.DOCUMENT.value and not obj.media_external_id:
            raise ValidationException(MSG_DOCUMENT_REQUIRED)
        if raw_type in (PeiResourceType.LINK.value, PeiResourceType.VIDEO.value) and not (
            obj.url and str(obj.url).strip()
        ):
            raise ValidationException(MSG_URL_REQUIRED)

    def _resource_admin(self, resource: PeiResource, media: Media | None) -> PeiResourceAdmin:
        schema = PeiResourceAdmin.model_validate(resource)
        schema.media_url = self._media_url(media)
        return schema

    def _resource_public(self, resource: PeiResource, media: Media | None) -> PeiResourcePublic:
        schema = PeiResourcePublic.model_validate(resource)
        schema.media_url = self._media_url(media)
        return schema

    async def list_resources(
        self,
        q: str | None = None,
        type: PeiResourceType | None = None,  # noqa: A002
        category: str | None = None,
        is_published: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PeiResourcesAdminPage:
        page, page_size = _clamp_page(page, page_size)
        conditions = []
        if q:
            conditions.append(PeiResource.title.ilike(f"%{q}%"))
        if type is not None:
            conditions.append(PeiResource.type == type)
        if category:
            conditions.append(PeiResource.category == category)
        if is_published is not None:
            conditions.append(PeiResource.is_published.is_(is_published))

        total = (
            await self.db.execute(select(func.count(PeiResource.id)).where(*conditions))
        ).scalar() or 0
        result = await self.db.execute(
            select(PeiResource, Media)
            .outerjoin(Media, PeiResource.media_external_id == Media.id)
            .where(*conditions)
            .order_by(PeiResource.display_order.asc(), PeiResource.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [self._resource_admin(r, m) for r, m in result.all()]
        return PeiResourcesAdminPage(
            items=items, total=total, page=page, page_size=page_size
        )

    async def list_resource_categories(self) -> list[str]:
        result = await self.db.execute(
            select(PeiResource.category)
            .where(PeiResource.category.is_not(None))
            .distinct()
            .order_by(PeiResource.category)
        )
        return [c for c in result.scalars().all() if c]

    async def get_resource(self, resource_id: str) -> PeiResourceAdmin:
        resource = await self._get_or_404(PeiResource, resource_id, "Ressource introuvable")
        media = await self._load_media(resource.media_external_id)
        return self._resource_admin(resource, media)

    async def create_resource(
        self,
        data: PeiResourceCreate,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PeiResourceAdmin:
        resource = PeiResource(
            **data.model_dump(),
            display_order=await self._next_display_order(PeiResource),
            created_by=user_id,
            updated_by=user_id,
        )
        self._validate_resource_source(resource)
        if resource.is_published:
            resource.published_at = datetime.now(timezone.utc)
        await translation_service.autofill_translations(resource, _RESOURCE_TRANSLATABLE)
        self.db.add(resource)
        await self.db.flush()

        await self._audit(
            "entrepreneurship.resource.create",
            user_id=user_id,
            record_id=resource.id,
            table_name="pei_resources",
            new_values=data.model_dump(mode="json"),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(resource)
        return await self.get_resource(resource.id)

    async def update_resource(
        self,
        resource_id: str,
        data: PeiResourceUpdate,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PeiResourceAdmin:
        resource = await self._get_or_404(PeiResource, resource_id, "Ressource introuvable")
        changes = data.model_dump(exclude_unset=True)

        # Validation sur l'objet fusionné AVANT toute mutation de l'instance ORM.
        merged = {
            "type": changes.get("type", resource.type),
            "media_external_id": changes.get("media_external_id", resource.media_external_id),
            "url": changes.get("url", resource.url),
        }
        self._validate_resource_source(SimpleNamespace(**merged))

        old = await self._apply_update(resource, changes, _RESOURCE_TRANSLATABLE, user_id)
        if resource.is_published and resource.published_at is None:
            resource.published_at = datetime.now(timezone.utc)
        await self.db.flush()

        await self._audit(
            "entrepreneurship.resource.update",
            user_id=user_id,
            record_id=resource.id,
            table_name="pei_resources",
            old_values=old,
            new_values=data.model_dump(mode="json", exclude_unset=True),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(resource)
        return await self.get_resource(resource.id)

    async def delete_resource(
        self,
        resource_id: str,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        resource = await self._get_or_404(PeiResource, resource_id, "Ressource introuvable")
        old = {
            "title": resource.title,
            "type": _jsonable(resource.type),
            "media_external_id": resource.media_external_id,
            "url": resource.url,
        }
        record_id = resource.id
        await self.db.delete(resource)
        await self._audit(
            "entrepreneurship.resource.delete",
            user_id=user_id,
            record_id=record_id,
            table_name="pei_resources",
            old_values=old,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()

    async def set_resource_published(
        self,
        resource_id: str,
        is_published: bool,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PublishStatus:
        resource = await self._get_or_404(PeiResource, resource_id, "Ressource introuvable")
        if is_published:
            self._validate_resource_source(resource)
            if resource.published_at is None:
                resource.published_at = datetime.now(timezone.utc)
        old_status = resource.is_published
        resource.is_published = is_published
        resource.updated_by = user_id
        await self.db.flush()
        await self._audit(
            "entrepreneurship.resource.publish"
            if is_published
            else "entrepreneurship.resource.unpublish",
            user_id=user_id,
            record_id=resource.id,
            table_name="pei_resources",
            old_values={"is_published": old_status},
            new_values={"is_published": is_published},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(resource)
        return PublishStatus.model_validate(resource)

    async def reorder_resources(
        self,
        ids: list[str],
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ReorderResponse:
        return await self._reorder(
            PeiResource,
            ids,
            "pei_resources",
            "entrepreneurship.resource.reorder",
            user_id,
            ip_address,
            user_agent,
        )

    async def translate_resource_fields(
        self, data: PeiResourceTranslateRequest
    ) -> PeiResourceTranslateResponse:
        return PeiResourceTranslateResponse(
            **await self._translate_request(data, _RESOURCE_TRANSLATABLE)
        )

    async def list_public_resources(
        self,
        type: PeiResourceType | None = None,  # noqa: A002
        category: str | None = None,
    ) -> list[PeiResourcePublic]:
        stmt = (
            select(PeiResource, Media)
            .outerjoin(Media, PeiResource.media_external_id == Media.id)
            .where(PeiResource.is_published.is_(True))
        )
        if type is not None:
            stmt = stmt.where(PeiResource.type == type)
        if category:
            stmt = stmt.where(PeiResource.category == category)
        result = await self.db.execute(
            stmt.order_by(PeiResource.display_order.asc(), PeiResource.created_at.asc())
        )
        return [self._resource_public(r, m) for r, m in result.all()]

    # ======================================================================
    # Portraits : lauréats FSE et étudiants-entrepreneurs (pei_laureates)
    # ======================================================================

    @staticmethod
    def _clamp_quote(obj) -> None:
        """Tronque les verbatims (FR / EN / AR) à ``QUOTE_MAX_LEN`` caractères."""
        for attr in ("quote", "quote_en", "quote_ar"):
            value = getattr(obj, attr, None)
            clamped = _clamp_text(value)
            if clamped != value:
                setattr(obj, attr, clamped)

    @staticmethod
    def _assert_laureate_cohort(laureate_type, cohort) -> None:
        """Cohérence type de portrait ↔ type de cohorte (422 sinon)."""
        expected = _LAUREATE_COHORT_TYPE.get(_enum_value(laureate_type))
        if expected is None:
            raise ValidationException("Type de portrait inconnu")
        cohort_type, message = expected
        if _enum_value(cohort.type) != cohort_type:
            raise ValidationException(message)

    def _laureate_admin(
        self, laureate: PeiLaureate, cohort: PeiCohort, media: Media | None
    ) -> PeiLaureateAdmin:
        data = {
            column.key: getattr(laureate, column.key)
            for column in PeiLaureate.__table__.columns
        }
        data["grant_amount"] = _format_amount(laureate.grant_amount)
        return PeiLaureateAdmin(
            **data,
            photo_url=self._media_url(media),
            cohort=PeiLaureateCohortRef(
                id=cohort.id,
                code=cohort.code,
                label=cohort.label,
                type=cohort.type,
                year=cohort.year,
                active=cohort.active,
            ),
        )

    @staticmethod
    def _laureate_select():
        return (
            select(PeiLaureate, PeiCohort, Media)
            .join(PeiCohort, PeiLaureate.cohort_id == PeiCohort.id)
            .outerjoin(Media, PeiLaureate.photo_external_id == Media.id)
        )

    async def list_laureates(
        self,
        q: str | None = None,
        cohort_id: str | None = None,
        type: PeiLaureateType | None = None,  # noqa: A002
        is_published: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PeiLaureatesAdminPage:
        page, page_size = _clamp_page(page, page_size)
        conditions = []
        if q:
            conditions.append(
                or_(
                    PeiLaureate.full_name.ilike(f"%{q}%"),
                    PeiLaureate.project_name.ilike(f"%{q}%"),
                )
            )
        if cohort_id:
            if not _is_uuid(cohort_id):
                return PeiLaureatesAdminPage(items=[], total=0, page=page, page_size=page_size)
            conditions.append(PeiLaureate.cohort_id == cohort_id)
        if type is not None:
            conditions.append(PeiLaureate.type == type)
        if is_published is not None:
            conditions.append(PeiLaureate.is_published.is_(is_published))

        total = (
            await self.db.execute(select(func.count(PeiLaureate.id)).where(*conditions))
        ).scalar() or 0
        result = await self.db.execute(
            self._laureate_select()
            .where(*conditions)
            .order_by(
                PeiCohort.display_order.asc(),
                PeiCohort.created_at.asc(),
                PeiLaureate.display_order.asc(),
                PeiLaureate.created_at.asc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [self._laureate_admin(lau, c, m) for lau, c, m in result.all()]
        return PeiLaureatesAdminPage(
            items=items, total=total, page=page, page_size=page_size
        )

    async def get_laureate(self, laureate_id: str) -> PeiLaureateAdmin:
        if not _is_uuid(laureate_id):
            raise NotFoundException("Portrait introuvable")
        row = (
            await self.db.execute(
                self._laureate_select().where(PeiLaureate.id == laureate_id)
            )
        ).first()
        if row is None:
            raise NotFoundException("Portrait introuvable")
        return self._laureate_admin(row[0], row[1], row[2])

    async def create_laureate(
        self,
        data: PeiLaureateCreate,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PeiLaureateAdmin:
        cohort = await self._get_or_404(PeiCohort, data.cohort_id, "Cohorte introuvable")
        self._assert_laureate_cohort(data.type, cohort)

        laureate = PeiLaureate(
            **data.model_dump(),
            display_order=await self._next_display_order(PeiLaureate, cohort_id=cohort.id),
            created_by=user_id,
            updated_by=user_id,
        )
        if laureate.is_published:
            laureate.published_at = datetime.now(timezone.utc)
        await translation_service.autofill_translations(laureate, _LAUREATE_TRANSLATABLE)
        self._clamp_quote(laureate)
        self.db.add(laureate)
        await self.db.flush()

        await self._audit(
            "entrepreneurship.laureate.create",
            user_id=user_id,
            record_id=laureate.id,
            table_name="pei_laureates",
            new_values=data.model_dump(mode="json"),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        return await self.get_laureate(laureate.id)

    async def update_laureate(
        self,
        laureate_id: str,
        data: PeiLaureateUpdate,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PeiLaureateAdmin:
        laureate = await self._get_or_404(PeiLaureate, laureate_id, "Portrait introuvable")
        changes = data.model_dump(exclude_unset=True)

        old_cohort_id = str(laureate.cohort_id)
        new_cohort_id = str(changes.get("cohort_id", old_cohort_id))
        cohort_changed = new_cohort_id != old_cohort_id
        if cohort_changed or "type" in changes:
            cohort = await self._get_or_404(PeiCohort, new_cohort_id, "Cohorte introuvable")
            self._assert_laureate_cohort(changes.get("type", laureate.type), cohort)

        new_order = (
            await self._next_display_order(PeiLaureate, cohort_id=new_cohort_id)
            if cohort_changed
            else None
        )
        old = await self._apply_update(laureate, changes, _LAUREATE_TRANSLATABLE, user_id)
        self._clamp_quote(laureate)
        if new_order is not None:
            old["display_order"] = laureate.display_order
            laureate.display_order = new_order
        if laureate.is_published and laureate.published_at is None:
            laureate.published_at = datetime.now(timezone.utc)
        await self.db.flush()
        if cohort_changed:
            await self._renumber(PeiLaureate, cohort_id=old_cohort_id)

        await self._audit(
            "entrepreneurship.laureate.update",
            user_id=user_id,
            record_id=laureate.id,
            table_name="pei_laureates",
            old_values=old,
            new_values=data.model_dump(mode="json", exclude_unset=True),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        return await self.get_laureate(laureate.id)

    async def delete_laureate(
        self,
        laureate_id: str,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        laureate = await self._get_or_404(PeiLaureate, laureate_id, "Portrait introuvable")
        old = {
            "full_name": laureate.full_name,
            "project_name": laureate.project_name,
            "type": _jsonable(laureate.type),
            "cohort_id": str(laureate.cohort_id),
        }
        record_id = laureate.id
        cohort_id = laureate.cohort_id
        await self.db.delete(laureate)
        await self.db.flush()
        await self._renumber(PeiLaureate, cohort_id=cohort_id)
        await self._audit(
            "entrepreneurship.laureate.delete",
            user_id=user_id,
            record_id=record_id,
            table_name="pei_laureates",
            old_values=old,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()

    async def set_laureate_published(
        self,
        laureate_id: str,
        is_published: bool,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PublishStatus:
        laureate = await self._get_or_404(PeiLaureate, laureate_id, "Portrait introuvable")
        old_status = laureate.is_published
        if is_published and laureate.published_at is None:
            laureate.published_at = datetime.now(timezone.utc)
        laureate.is_published = is_published
        laureate.updated_by = user_id
        await self.db.flush()
        await self._audit(
            "entrepreneurship.laureate.publish"
            if is_published
            else "entrepreneurship.laureate.unpublish",
            user_id=user_id,
            record_id=laureate.id,
            table_name="pei_laureates",
            old_values={"is_published": old_status},
            new_values={"is_published": is_published},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(laureate)
        return PublishStatus.model_validate(laureate)

    async def set_laureate_featured(
        self,
        laureate_id: str,
        is_featured: bool,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> FeaturedStatus:
        laureate = await self._get_or_404(PeiLaureate, laureate_id, "Portrait introuvable")
        old_status = laureate.is_featured
        laureate.is_featured = is_featured
        laureate.updated_by = user_id
        await self.db.flush()
        await self._audit(
            "entrepreneurship.laureate.feature"
            if is_featured
            else "entrepreneurship.laureate.unfeature",
            user_id=user_id,
            record_id=laureate.id,
            table_name="pei_laureates",
            old_values={"is_featured": old_status},
            new_values={"is_featured": is_featured},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        await self.db.refresh(laureate)
        return FeaturedStatus.model_validate(laureate)

    async def reorder_laureates(
        self,
        cohort_id: str,
        ids: list[str],
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ReorderResponse:
        if not _is_uuid(cohort_id):
            raise ValidationException("Identifiant de cohorte invalide")
        return await self._reorder(
            PeiLaureate,
            ids,
            "pei_laureates",
            "entrepreneurship.laureate.reorder",
            user_id,
            ip_address,
            user_agent,
            scope={"cohort_id": cohort_id},
        )

    async def translate_laureate_fields(
        self, data: PeiLaureateTranslateRequest
    ) -> PeiLaureateTranslateResponse:
        out = await self._translate_request(data, _LAUREATE_TRANSLATABLE)
        for key in ("quote_en", "quote_ar"):
            if key in out:
                out[key] = _clamp_text(out[key])
        return PeiLaureateTranslateResponse(**out)

    async def list_public_laureates(
        self, type: PeiLaureateType | None = None  # noqa: A002
    ) -> PeiLaureatesPublic:
        stmt = self._laureate_select().where(
            PeiLaureate.is_published.is_(True), PeiCohort.active.is_(True)
        )
        if type is not None:
            stmt = stmt.where(PeiLaureate.type == type)
        result = await self.db.execute(
            stmt.order_by(
                PeiCohort.display_order.asc(),
                PeiCohort.created_at.asc(),
                PeiLaureate.display_order.asc(),
                PeiLaureate.created_at.asc(),
            )
        )

        groups: dict[str, PeiLaureateGroupPublic] = {}
        count = 0
        max_grant = None
        for laureate, cohort, media in result.all():
            group = groups.get(cohort.id)
            if group is None:
                group = PeiLaureateGroupPublic(
                    cohort=PeiCohortPublic.model_validate(cohort), laureates=[]
                )
                groups[cohort.id] = group
            group.laureates.append(
                PeiLaureatePublic(
                    id=laureate.id,
                    type=laureate.type,
                    full_name=laureate.full_name,
                    project_name=laureate.project_name,
                    department_label=laureate.department_label,
                    department_label_en=laureate.department_label_en,
                    department_label_ar=laureate.department_label_ar,
                    quote=laureate.quote,
                    quote_en=laureate.quote_en,
                    quote_ar=laureate.quote_ar,
                    photo_url=self._media_url(media),
                    website_url=laureate.website_url,
                    linkedin_url=laureate.linkedin_url,
                    instagram_url=laureate.instagram_url,
                    facebook_url=laureate.facebook_url,
                    video_url=laureate.video_url,
                    is_featured=laureate.is_featured,
                    cohort_label=cohort.label,
                    cohort_label_en=cohort.label_en,
                    cohort_label_ar=cohort.label_ar,
                    display_order=laureate.display_order,
                )
            )
            count += 1
            if laureate.grant_amount is not None and (
                max_grant is None or laureate.grant_amount > max_grant
            ):
                max_grant = laureate.grant_amount

        return PeiLaureatesPublic(
            groups=list(groups.values()),
            stats=PeiLaureateStatsPublic(
                laureates=count,
                cohorts=len(groups),
                max_grant_amount=_format_amount(max_grant),
            ),
        )

    # ======================================================================
    # Partenaires du pôle (pei_partners)
    # ======================================================================

    @staticmethod
    def _partner_link_select():
        return (
            select(PeiPartner, Partner, Media)
            .join(Partner, Partner.id == PeiPartner.partner_id)
            .outerjoin(Media, Partner.logo_external_id == Media.id)
        )

    def _partner_link_admin(
        self, link: PeiPartner, partner: Partner, media: Media | None
    ) -> PeiPartnerLinkAdmin:
        return PeiPartnerLinkAdmin(
            partner_id=link.partner_id,
            family=link.family,
            display_order=link.display_order,
            created_at=link.created_at,
            updated_at=link.updated_at,
            partner=PeiPartnerEmbedded(
                id=partner.id,
                name=partner.name,
                type=_enum_value(partner.type),
                active=bool(partner.active),
                website=partner.website,
                logo_url=self._media_url(media),
                description=partner.description,
            ),
        )

    async def _get_partner_link_or_404(self, partner_id: str) -> PeiPartner:
        if not _is_uuid(partner_id):
            raise NotFoundException("Partenaire non rattaché au pôle")
        link = (
            await self.db.execute(select(PeiPartner).where(PeiPartner.partner_id == partner_id))
        ).scalar_one_or_none()
        if link is None:
            raise NotFoundException("Partenaire non rattaché au pôle")
        return link

    async def get_partner_link(self, partner_id: str) -> PeiPartnerLinkAdmin:
        row = (
            await self.db.execute(
                self._partner_link_select().where(PeiPartner.partner_id == partner_id)
            )
        ).first()
        if row is None:
            raise NotFoundException("Partenaire non rattaché au pôle")
        return self._partner_link_admin(row[0], row[1], row[2])

    async def list_partner_links(
        self, family: PeiPartnerFamily | None = None
    ) -> list[PeiPartnerLinkAdmin]:
        stmt = self._partner_link_select()
        if family is not None:
            stmt = stmt.where(PeiPartner.family == family)
        # Un ENUM PostgreSQL se trie dans l'ordre de déclaration (= PARTNER_FAMILY_ORDER).
        result = await self.db.execute(
            stmt.order_by(
                PeiPartner.family.asc(),
                PeiPartner.display_order.asc(),
                PeiPartner.created_at.asc(),
            )
        )
        return [self._partner_link_admin(link, p, m) for link, p, m in result.all()]

    async def list_available_partners(
        self, q: str | None = None, limit: int = 20
    ) -> list[PeiPartnerAvailable]:
        limit = max(1, min(limit, 50))
        stmt = (
            select(Partner, Media)
            .outerjoin(Media, Partner.logo_external_id == Media.id)
            .where(~exists().where(PeiPartner.partner_id == Partner.id))
        )
        if q:
            stmt = stmt.where(
                or_(Partner.name.ilike(f"%{q}%"), Partner.description.ilike(f"%{q}%"))
            )
        result = await self.db.execute(
            stmt.order_by(Partner.active.desc(), Partner.name.asc()).limit(limit)
        )
        return [
            PeiPartnerAvailable(
                id=partner.id,
                name=partner.name,
                type=_enum_value(partner.type),
                active=bool(partner.active),
                logo_url=self._media_url(media),
            )
            for partner, media in result.all()
        ]

    async def link_partner(
        self,
        data: PeiPartnerLinkCreate,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PeiPartnerLinkAdmin:
        partner = await self._get_or_404(Partner, data.partner_id, "Partenaire introuvable")
        existing = (
            await self.db.execute(
                select(PeiPartner.partner_id).where(PeiPartner.partner_id == partner.id)
            )
        ).first()
        if existing is not None:
            raise ConflictException("Ce partenaire est déjà rattaché au pôle")

        link = PeiPartner(
            partner_id=partner.id,
            family=data.family,
            display_order=await self._next_display_order(PeiPartner, family=data.family),
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(link)
        await self.db.flush()
        await self._audit(
            "entrepreneurship.partner.link",
            user_id=user_id,
            record_id=partner.id,
            table_name="pei_partners",
            new_values={"family": data.family.value, "display_order": link.display_order},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        return await self.get_partner_link(partner.id)

    async def update_partner_family(
        self,
        partner_id: str,
        family: PeiPartnerFamily,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PeiPartnerLinkAdmin:
        link = await self._get_partner_link_or_404(partner_id)
        old_family = PeiPartnerFamily(_enum_value(link.family))
        if old_family == family:
            return await self.get_partner_link(link.partner_id)

        old = {"family": old_family.value, "display_order": link.display_order}
        link.display_order = await self._next_display_order(PeiPartner, family=family)
        link.family = family
        link.updated_by = user_id
        await self.db.flush()
        await self._renumber(PeiPartner, family=old_family)
        await self._audit(
            "entrepreneurship.partner.update",
            user_id=user_id,
            record_id=link.partner_id,
            table_name="pei_partners",
            old_values=old,
            new_values={"family": family.value, "display_order": link.display_order},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        return await self.get_partner_link(link.partner_id)

    async def unlink_partner(
        self,
        partner_id: str,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        link = await self._get_partner_link_or_404(partner_id)
        family = PeiPartnerFamily(_enum_value(link.family))
        old = {"family": family.value, "display_order": link.display_order}
        record_id = link.partner_id
        await self.db.delete(link)
        await self.db.flush()
        await self._renumber(PeiPartner, family=family)
        await self._audit(
            "entrepreneurship.partner.unlink",
            user_id=user_id,
            record_id=record_id,
            table_name="pei_partners",
            old_values=old,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()

    async def reorder_partner_links(
        self,
        family: PeiPartnerFamily,
        ids: list[str],
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ReorderResponse:
        return await self._reorder(
            PeiPartner,
            ids,
            "pei_partners",
            "entrepreneurship.partner.reorder",
            user_id,
            ip_address,
            user_agent,
            scope={"family": family},
        )

    async def list_public_partners(self) -> list[PeiPartnerFamilyPublic]:
        result = await self.db.execute(
            self._partner_link_select()
            .where(Partner.active.is_(True))
            .order_by(PeiPartner.display_order.asc(), PeiPartner.created_at.asc())
        )
        groups = {family: [] for family in PARTNER_FAMILY_ORDER}
        for link, partner, media in result.all():
            groups[PeiPartnerFamily(_enum_value(link.family))].append(
                PeiPartnerPublic(
                    id=partner.id,
                    name=partner.name,
                    description=partner.description,
                    description_en=partner.description_en,
                    description_ar=partner.description_ar,
                    website=partner.website,
                    logo_url=self._media_url(media),
                    type=_enum_value(partner.type),
                    display_order=link.display_order,
                )
            )
        return [
            PeiPartnerFamilyPublic(family=family, partners=partners)
            for family, partners in groups.items()
        ]

    # ======================================================================
    # Tableau de bord et traduction en lot
    # ======================================================================

    async def get_dashboard_stats(self) -> PeiDashboardStats:
        programs = (
            await self.db.execute(
                select(
                    func.count(PeiProgram.id),
                    func.count(PeiProgram.id).filter(PeiProgram.active.is_(True)),
                )
            )
        ).one()
        cohorts = (
            await self.db.execute(
                select(
                    func.count(PeiCohort.id),
                    func.count(PeiCohort.id).filter(PeiCohort.active.is_(True)),
                )
            )
        ).one()
        resources = (
            await self.db.execute(
                select(
                    func.count(PeiResource.id),
                    func.count(PeiResource.id).filter(PeiResource.is_published.is_(True)),
                )
            )
        ).one()

        laureates = (
            await self.db.execute(
                select(
                    func.count(PeiLaureate.id),
                    func.count(PeiLaureate.id).filter(PeiLaureate.is_published.is_(True)),
                )
            )
        ).one()
        partners = (
            await self.db.execute(
                select(
                    func.count(PeiPartner.partner_id),
                    func.count(PeiPartner.partner_id).filter(Partner.active.is_(True)),
                )
                .select_from(PeiPartner)
                .join(Partner, Partner.id == PeiPartner.partner_id)
            )
        ).one()

        dde = PeiDdeService()
        content = await EditorialService(self.db).get_content_by_key(DDE_SERVICE_KEY)
        service_id = (content.value or "").strip() if content else ""
        if _is_uuid(service_id):
            row = (
                await self.db.execute(
                    select(Service.id, Service.name).where(Service.id == service_id)
                )
            ).first()
            if row is not None:
                dde = PeiDdeService(id=str(row[0]), name=row[1])

        return PeiDashboardStats(
            programs=PeiActiveCount(total=programs[0], active=programs[1]),
            cohorts=PeiActiveCount(total=cohorts[0], active=cohorts[1]),
            resources=PeiPublishedCount(total=resources[0], published=resources[1]),
            dde_service=dde,
            laureates=PeiPublishedCount(total=laureates[0], published=laureates[1]),
            partners=PeiActiveCount(total=partners[0], active=partners[1]),
        )

    async def _translate_missing_for(self, model, fields, deadline: float) -> tuple[int, bool]:
        """Complète les traductions vides d'une table ; s'arrête à ``deadline``.

        Renvoie ``(objets modifiés, table entièrement parcourue)``.
        """
        attrs = _translated_attrs(fields)
        result = await self.db.execute(select(model).order_by(model.display_order, model.created_at))
        changed = 0
        for obj in result.scalars().all():
            if time.monotonic() >= deadline:
                return changed, False
            before = tuple(getattr(obj, a) for a in attrs)
            await translation_service.autofill_translations(obj, fields, force=False)
            if isinstance(obj, PeiLaureate):
                self._clamp_quote(obj)
            if tuple(getattr(obj, a) for a in attrs) != before:
                changed += 1
        return changed, True

    async def _translate_missing_faq_see(self, deadline: float) -> tuple[int, bool]:
        """Complète les traductions vides des entrées FAQ **publiées** des catégories
        ``see-*`` (page Statut Étudiant-Entrepreneur, spec 025) ; s'arrête à ``deadline``.

        Les brouillons (réponses provisoires) sont exclus : ils sont traduits à leur
        enregistrement dans le backoffice FAQ.
        """
        attrs = [
            f"{field}_{lang}{suffix}"
            for lang in ("en", "ar")
            for field, suffix in (("question", ""), ("answer", "_html"), ("answer", "_md"))
        ]
        stmt = (
            select(FaqEntry)
            .join(FaqCategory, FaqEntry.category_id == FaqCategory.id)
            .where(
                FaqEntry.is_published.is_(True),
                FaqCategory.code.startswith("see-", autoescape=True),
                or_(*(or_(getattr(FaqEntry, a).is_(None), getattr(FaqEntry, a) == "") for a in attrs)),
            )
            .order_by(FaqCategory.display_order, FaqEntry.display_order, FaqEntry.created_at)
        )
        entries = (await self.db.execute(stmt)).scalars().all()
        faq_service = FaqService(self.db)
        changed = 0
        for entry in entries:
            if time.monotonic() >= deadline:
                return changed, False
            before = tuple(getattr(entry, a) for a in attrs)
            await faq_service.autofill_entry_translations(entry)
            if tuple(getattr(entry, a) for a in attrs) != before:
                changed += 1
        return changed, True

    async def translate_missing(
        self,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        time_budget: float = TRANSLATE_MISSING_TIME_BUDGET,
    ) -> PeiTranslateMissingResponse:
        # Budget de temps : chaque appel reste sous le délai du proxy (nginx 90 s) ;
        # le travail déjà fait est enregistré et le client relance tant que
        # ``complete`` est faux (les champs remplis ne sont plus retraduits).
        deadline = time.monotonic() + time_budget
        counts: dict[str, int] = {}
        complete = True
        for key, model, fields in (
            ("programs", PeiProgram, _PROGRAM_TRANSLATABLE),
            ("cohorts", PeiCohort, _COHORT_TRANSLATABLE),
            ("resources", PeiResource, _RESOURCE_TRANSLATABLE),
            ("laureates", PeiLaureate, _LAUREATE_TRANSLATABLE),
        ):
            if not complete:
                counts[key] = 0
                continue
            counts[key], complete = await self._translate_missing_for(model, fields, deadline)
        if complete:
            counts["faq_see"], complete = await self._translate_missing_faq_see(deadline)
        else:
            counts["faq_see"] = 0
        result = PeiTranslateMissingResponse(**counts, complete=complete)
        await self.db.flush()
        await self._audit(
            "entrepreneurship.translate_missing",
            user_id=user_id,
            record_id=None,
            table_name=None,
            new_values=result.model_dump(),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.commit()
        return result
