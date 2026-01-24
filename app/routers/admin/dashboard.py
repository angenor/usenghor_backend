"""
Router Admin - Dashboard
========================

Endpoints admin pour le tableau de bord.
"""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession, PermissionChecker
from app.schemas.dashboard import (
    GlobalStats,
    PendingTasksResponse,
    RecentActivityResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    response_model=GlobalStats,
    dependencies=[Depends(PermissionChecker("dashboard.view"))],
)
async def get_global_stats(
    db: DbSession,
) -> GlobalStats:
    """
    Récupère les statistiques globales du tableau de bord.

    Inclut les compteurs pour:
    - Utilisateurs (total, actifs, inactifs, vérifiés)
    - Actualités (total, publiées, brouillons, archivées)
    - Événements (total, publiés, brouillons, archivés)
    - Candidatures (total, par statut)
    - Appels à candidature (total, en cours, à venir, fermés)
    - Newsletter (abonnés, campagnes)
    - Projets institutionnels (total, par statut)
    - Programmes, partenaires, pays, campus
    """
    service = DashboardService(db)
    return await service.get_global_stats()


@router.get(
    "/recent-activity",
    response_model=RecentActivityResponse,
    dependencies=[Depends(PermissionChecker("dashboard.view"))],
)
async def get_recent_activity(
    db: DbSession,
    limit: int = Query(20, ge=1, le=100, description="Nombre d'éléments"),
    action: str | None = Query(None, description="Filtrer par action"),
    table_name: str | None = Query(None, description="Filtrer par table"),
) -> RecentActivityResponse:
    """
    Récupère l'activité récente depuis les logs d'audit.

    Retourne les dernières actions effectuées par les utilisateurs:
    - Créations, modifications, suppressions
    - Connexions, déconnexions
    - Autres actions tracées

    Peut être filtré par type d'action ou par table concernée.
    """
    service = DashboardService(db)
    return await service.get_recent_activity(
        limit=limit,
        action=action,
        table_name=table_name,
    )


@router.get(
    "/pending-tasks",
    response_model=PendingTasksResponse,
    dependencies=[Depends(PermissionChecker("dashboard.view"))],
)
async def get_pending_tasks(
    db: DbSession,
) -> PendingTasksResponse:
    """
    Récupère les tâches en attente.

    Regroupe les éléments nécessitant une action:
    - Actualités en brouillon à publier
    - Événements en brouillon à publier
    - Candidatures à examiner
    - Appels à candidature expirant bientôt
    - Événements à venir cette semaine

    Les tâches sont organisées par catégorie avec un indicateur de priorité.
    """
    service = DashboardService(db)
    return await service.get_pending_tasks()
