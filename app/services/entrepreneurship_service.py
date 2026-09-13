"""
Service Entrepreneuriat (PEI)
=============================

Logique métier du Pôle Entrepreneuriat et Innovation : dispositifs, cohortes,
ressources (CRUD admin, réordonnancement, activation / publication, traduction
automatique FR → EN/AR, tableau de bord) et lecture publique.

Toute écriture produit une entrée ``audit_logs`` explicite (``_audit``), avec
``record_id`` = UUID de la ligne ou ``None`` pour les actions en lot.
"""

import enum
import time
from types import SimpleNamespace
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
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
    PeiProgram,
    PeiProgramPhase,
    PeiResource,
    PeiResourceType,
)
from app.models.media import Media
from app.models.organization import Service
from app.schemas.entrepreneurship import (
    MSG_DOCUMENT_REQUIRED,
    MSG_URL_REQUIRED,
    ActiveStatus,
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
    return value


def _clamp_page(page: int, page_size: int) -> tuple[int, int]:
    return max(1, page), max(1, min(page_size, 100))


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

    async def _next_display_order(self, model) -> int:
        """``MAX(display_order) + 1`` (0 sur une table vide)."""
        result = await self.db.execute(select(func.max(model.display_order)))
        current = result.scalar()
        return 0 if current is None else current + 1

    async def _reorder(
        self,
        model,
        ids: list[str],
        table_name: str,
        action: str,
        user_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ReorderResponse:
        """Renumérote ``display_order = index`` (0..n-1) à partir d'une liste complète."""
        if len(set(ids)) != len(ids):
            raise ValidationException("Liste invalide : identifiants en double")

        result = await self.db.execute(select(model.id, model.display_order))
        current = {str(row_id): order for row_id, order in result.all()}

        unknown = [i for i in ids if i not in current]
        if unknown:
            raise ValidationException(
                f"Identifiant(s) inconnu(s) : {', '.join(unknown)}"
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
                    update(model).where(model.id == item_id).values(display_order=index)
                )
                updated += 1

        await self._audit(
            action,
            user_id=user_id,
            record_id=None,
            table_name=table_name,
            new_values={"ids": ids},
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
        """Point d'extension de la suppression d'une cohorte.

        No-op dans la feature 021. Feature 022 : compter les lauréats rattachés
        (``pei_laureates.cohort_id``) et, s'il y en a, lever
        ``ConflictException(f"Cohorte utilisée par {n} lauréats")``.
        """
        return None

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
            if tuple(getattr(obj, a) for a in attrs) != before:
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
        ):
            if not complete:
                counts[key] = 0
                continue
            counts[key], complete = await self._translate_missing_for(model, fields, deadline)
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
