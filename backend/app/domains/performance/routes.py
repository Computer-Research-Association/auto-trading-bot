from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from core.deps import get_database
from app.domains.performance import schemas
import app.domains.performance.service as perf_service

router = APIRouter(prefix="/performance")


@router.get("/chart", response_model=schemas.PerformanceChartResponse)
async def performance_chart(
    request_data: schemas.PerformanceChartRequest = Depends(),
    db: AsyncSession = Depends(get_database),
):
    query = schemas.PerformanceQuery.model_validate(request_data.model_dump())
    return await perf_service.get_chart(query, db)


@router.get("/daily", response_model=schemas.PerformanceDailyResponse)
async def performance_daily(
    request_data: schemas.PerformanceChartRequest = Depends(),
    db: AsyncSession = Depends(get_database),
):
    query = schemas.PerformanceQuery.model_validate(request_data.model_dump())
    return await perf_service.get_daily_table(query, db)


@router.get("/summary", response_model=schemas.PerformanceResponse)
async def performance_summary(
    request_data: schemas.PerformanceChartRequest = Depends(),
    db: AsyncSession = Depends(get_database)
):
    query = schemas.PerformanceQuery.model_validate(request_data.model_dump())
    return await perf_service.get_all_performance(db, query)