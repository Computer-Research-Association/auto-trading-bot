from __future__ import annotations

from datetime import date
from typing import List, Literal

from pydantic import BaseModel, Field


Granularity = Literal["daily", "monthly", "yearly"]
ReturnType = Literal["simple", "detailed"]

class PerformanceQuery(BaseModel):
    start_date: date
    end_date: date
    period: str
    granularity: Granularity = "daily"
    return_type: ReturnType = "simple"

class PerformanceSummary(BaseModel):
    period_label: str
    start_assets_krw: float = 0
    end_assets_krw: float = 0
    pnl_krw: float = 0
    pnl_rate: float = 0

# (차트 한 점 / 일별 한 점 모두 커버 가능하게 구성)
class PerformancePoint(BaseModel):
    date: date
    assets_krw: float
    pnl_krw: float = 0
    pnl_rate: float = 0

class PerformanceChartResponse(BaseModel):
    points: List[PerformancePoint] = Field(default_factory=list)

class PerformanceDailyRow(BaseModel):
    date: date
    assets_krw: float
    pnl_krw: float = 0
    pnl_rate: float = 0

class PerformanceDailyResponse(BaseModel):
    rows: List[PerformanceDailyRow] = Field(default_factory=list)

# (프론트에서 한 번에 받는 형태로도 쓸 수 있게)
class PerformanceResponse(BaseModel):
    summary: PerformanceSummary
    chart: List[PerformancePoint] = Field(default_factory=list)
    daily: List[PerformanceDailyRow] = Field(default_factory=list)


class PerformanceChartRequest(BaseModel):
    start_date: date
    end_date: date
    period: str = "30d"
    granularity: Granularity = "daily"
    return_type: ReturnType = "simple"



