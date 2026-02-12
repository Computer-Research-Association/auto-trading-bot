from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.deps import get_database
from app.domains.log import schemas, service

router = APIRouter()

@router.get("/", response_model=schemas.LogResponse)
async def get_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_database)
):
    return await service.get_logs(db, limit=limit)
