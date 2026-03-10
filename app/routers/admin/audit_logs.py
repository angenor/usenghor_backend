"""
Router Admin - Logs d'audit
============================

Endpoints pour consulter et gérer les logs d'audit.
"""

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.pagination import PaginationParams, paginate
from app.models.identity import AuditLog, User
from app.schemas.common import MessageResponse
from app.schemas.identity import (
    AuditLogPurge,
    AuditLogRead,
    AuditLogReadWithUser,
    AuditLogStatistics,
    AuditLogUserInfo,
)
from app.services.identity_service import IdentityService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=dict)
async def list_audit_logs(
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    user_id: str | None = Query(None, description="Filtrer par utilisateur"),
    table_name: str | None = Query(None, description="Filtrer par table"),
    action: str | None = Query(None, description="Filtrer par action"),
    date_from: datetime | None = Query(None, description="Date de début"),
    date_to: datetime | None = Query(None, description="Date de fin"),
    ip_address: str | None = Query(None, description="Filtrer par adresse IP"),
    search: str | None = Query(None, description="Recherche textuelle"),
    _: bool = Depends(PermissionChecker("admin.audit")),
) -> dict:
    """Liste les logs d'audit avec pagination et filtres, enrichis avec les infos utilisateur."""
    service = IdentityService(db)
    query = await service.get_audit_logs(
        user_id=user_id,
        table_name=table_name,
        action=action,
        date_from=date_from,
        date_to=date_to,
        ip_address=ip_address,
        search=search,
    )
    result = await paginate(db, query, pagination, AuditLog, AuditLogRead)

    # Enrichir les items avec les données utilisateur
    items: list[AuditLogRead] = result["items"]
    user_ids = {item.user_id for item in items if item.user_id}
    users_map: dict[str, User] = {}
    if user_ids:
        users_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users_map = {str(u.id): u for u in users_result.scalars().all()}

    enriched_items = []
    for item in items:
        item_dict = item.model_dump()
        user = users_map.get(item.user_id) if item.user_id else None
        item_dict["user"] = AuditLogUserInfo.from_user(user).model_dump() if user else None
        enriched_items.append(item_dict)

    result["items"] = enriched_items
    return result


@router.get("/statistics", response_model=AuditLogStatistics)
async def get_audit_statistics(
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("admin.audit")),
) -> dict:
    """Récupère les statistiques des logs d'audit."""
    service = IdentityService(db)
    return await service.get_audit_statistics()


@router.get("/export")
async def export_audit_logs(
    db: DbSession,
    current_user: CurrentUser,
    user_id: str | None = Query(None, description="Filtrer par utilisateur"),
    table_name: str | None = Query(None, description="Filtrer par table"),
    action: str | None = Query(None, description="Filtrer par action"),
    date_from: datetime | None = Query(None, description="Date de début"),
    date_to: datetime | None = Query(None, description="Date de fin"),
    ip_address: str | None = Query(None, description="Filtrer par adresse IP"),
    format: str = Query("csv", pattern="^(csv)$", description="Format d'export"),
    _: bool = Depends(PermissionChecker("admin.audit")),
):
    """Exporte les logs d'audit en CSV."""
    service = IdentityService(db)
    query = await service.get_audit_logs(
        user_id=user_id,
        table_name=table_name,
        action=action,
        date_from=date_from,
        date_to=date_to,
        ip_address=ip_address,
    )

    # Exécuter la requête
    result = await db.execute(query.order_by(AuditLog.created_at.desc()).limit(10000))
    logs = result.scalars().all()

    # Créer le CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # En-têtes
    writer.writerow([
        "ID",
        "Date",
        "Utilisateur",
        "Action",
        "Table",
        "Enregistrement",
        "Adresse IP",
    ])

    # Données
    for log in logs:
        writer.writerow([
            log.id,
            log.created_at.isoformat() if log.created_at else "",
            log.user_id or "",
            log.action,
            log.table_name or "",
            log.record_id or "",
            log.ip_address or "",
        ])

    output.seek(0)

    filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/user/{user_id}", response_model=dict)
async def get_user_audit_logs(
    user_id: str,
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    _: bool = Depends(PermissionChecker("admin.audit")),
) -> dict:
    """Récupère les logs d'audit d'un utilisateur."""
    service = IdentityService(db)
    query = await service.get_audit_logs(user_id=user_id)
    return await paginate(db, query, pagination, AuditLog, AuditLogRead)


@router.get("/record/{table_name}/{record_id}", response_model=dict)
async def get_record_audit_logs(
    table_name: str,
    record_id: str,
    db: DbSession,
    current_user: CurrentUser,
    pagination: PaginationParams = Depends(),
    _: bool = Depends(PermissionChecker("admin.audit")),
) -> dict:
    """Récupère les logs d'audit d'un enregistrement."""
    service = IdentityService(db)
    query = await service.get_audit_logs(table_name=table_name, record_id=record_id)
    return await paginate(db, query, pagination, AuditLog, AuditLogRead)


@router.get("/{log_id}", response_model=dict)
async def get_audit_log(
    log_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("admin.audit")),
) -> dict:
    """Récupère un log d'audit par son ID, enrichi avec les infos utilisateur."""
    service = IdentityService(db)
    log = await service.get_audit_log_by_id(log_id)
    if not log:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Log d'audit non trouvé")

    log_data = AuditLogRead.model_validate(log).model_dump()

    # Enrichir avec les données utilisateur
    if log.user_id:
        user_result = await db.execute(
            select(User).where(User.id == log.user_id)
        )
        user = user_result.scalar_one_or_none()
        log_data["user"] = AuditLogUserInfo.from_user(user).model_dump() if user else None

    return log_data


@router.post("/purge", response_model=MessageResponse)
async def purge_audit_logs(
    purge_data: AuditLogPurge,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("admin.settings")),
) -> MessageResponse:
    """Purge les logs d'audit avant une date."""
    service = IdentityService(db)
    count = await service.purge_audit_logs(purge_data.before_date)
    return MessageResponse(message=f"{count} log(s) d'audit supprimé(s)")
