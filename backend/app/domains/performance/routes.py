from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_session
from .repository import PerformanceRepository
from .schemas import (
    PerformanceQuery,
    PerformanceSummary,
    PerformanceChartResponse,
    PerformanceDailyResponse,
    Granularity,
    ReturnType,
    PerformanceResponse,
)
from . import service as perf_service

print("### PERF SERVICE FILE:", perf_service.__file__)
print("### HAS get_summary:", hasattr(perf_service, "get_summary"))

router = APIRouter()


def get_repo(session: Session = Depends(get_session)) -> PerformanceRepository:
    return PerformanceRepository(session)


def _default_dates(period: str) -> tuple[date, date]:
    today = date.today()
    if period.endswith("d") and period[:-1].isdigit():
        days = int(period[:-1])
    else:
        days = 30
    return today - timedelta(days=days), today

@router.get("/chart", response_model=PerformanceChartResponse)
def performance_chart(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: str = "30d",
    granularity: Granularity = "daily",
    return_type: ReturnType = "simple",
    repo: PerformanceRepository = Depends(get_repo),
):
    if start_date is None or end_date is None:
        start_date, end_date = _default_dates(period)

    q = PerformanceQuery(
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
        return_type=return_type,
    )
    return perf_service.get_chart(repo, q)


@router.get("/daily", response_model=PerformanceDailyResponse)
def performance_daily(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: str = "30d",
    granularity: Granularity = "daily",
    return_type: ReturnType = "simple",
    repo: PerformanceRepository = Depends(get_repo),
):
    if start_date is None or end_date is None:
        start_date, end_date = _default_dates(period)

    q = PerformanceQuery(
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
        return_type=return_type,
    )
    return perf_service.get_daily_table(repo, q)


@router.get("/summary", response_model=PerformanceResponse)
def performance_summary(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "30d",
        granularity: Granularity = "daily",
        return_type: ReturnType = "simple",
        repo: PerformanceRepository = Depends(get_repo),
):
    if start_date is None or end_date is None:
        start_date, end_date = _default_dates(period)
    q = PerformanceQuery(
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
        return_type=return_type,
    )

    # 새로 만든 통합 함수 호출
    return perf_service.get_all_performance(repo, q)
