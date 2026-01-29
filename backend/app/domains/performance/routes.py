from __future__ import annotations

from datetime import timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from core.deps import get_database
from app.domains.performance.schemas import *
import app.domains.performance.service  as perf_service
from app.domains.performance import schemas

router = APIRouter(prefix="/performance")

@router.get("/chart", response_model=PerformanceChartResponse)
def performance_chart(
    request_data: PerformanceChartRequest = Depends(),
    db: AsyncSession = Depends(get_database),
):
    query = PerformanceQuery.model_validate(request_data)
    return perf_service.get_chart(query, db)

@router.get("/daily", response_model=schemas.PerformanceDailyResponse)
def performance_daily(
    request_data: PerformanceChartRequest = Depends(),
):
    query = PerformanceQuery.model_validate(request_data)
    return perf_service.get_daily_table(query)

@router.get("/summary", response_model=schemas.PerformanceResponse)
async def performance_summary(
    request_data: schemas.PerformanceChartRequest = Depends(),
    db: AsyncSession = Depends(get_database),
):
    print("🔥 ChartRequest required:",
          {k: v.is_required() for k, v in schemas.PerformanceChartRequest.model_fields.items()})
    print("🔥 request_data:", request_data)
