"""
Router Public - Champs disciplinaires
======================================

Endpoint public pour lister les champs disciplinaires (certificats).
"""

from fastapi import APIRouter

from app.core.dependencies import DbSession
from app.models.academic import ProgramField
from app.schemas.academic import ProgramFieldRead
from app.services.academic_service import AcademicService

router = APIRouter(prefix="/program-fields", tags=["Program Fields"])


@router.get("", response_model=list[ProgramFieldRead])
async def list_fields(
    db: DbSession,
) -> list[ProgramField]:
    """Liste les champs disciplinaires (pour filtrage public des certificats)."""
    service = AcademicService(db)
    query = await service.get_fields()
    result = await db.execute(query)
    return list(result.scalars().all())
