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

from app.core.dependencies import CurrentUser, DbSession, PermissionChecker
from app.core.pagination import PaginationParams, paginate
from app.models.identity import AuditLog
from app.schemas.common import MessageResponse
from app.schemas.identity import (
    AuditLogPurge,
    AuditLogRead,
    AuditLogStatistics,
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
    _: bool = Depends(PermissionChecker("admin.audit")),
) -> dict:
    """Liste les logs d'audit avec pagination et filtres."""
    service = IdentityService(db)
    query = await service.get_audit_logs(
        user_id=user_id, table_name=table_name, action=action
    )
    return await paginate(db, query, pagination, AuditLog)


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
    format: str = Query("csv", pattern="^(csv)$", description="Format d'export"),
    _: bool = Depends(PermissionChecker("admin.audit")),
):
    """Exporte les logs d'audit en CSV."""
    service = IdentityService(db)
    query = await service.get_audit_logs(
        user_id=user_id, table_name=table_name, action=action
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
    return await paginate(db, query, pagination, AuditLog)


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
    return await paginate(db, query, pagination, AuditLog)


@router.get("/{log_id}", response_model=AuditLogRead)
async def get_audit_log(
    log_id: str,
    db: DbSession,
    current_user: CurrentUser,
    _: bool = Depends(PermissionChecker("admin.audit")),
) -> AuditLog:
    """Récupère un log d'audit par son ID."""
    service = IdentityService(db)
    log = await service.get_audit_log_by_id(log_id)
    if not log:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Log d'audit non trouvé")
    return log


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
