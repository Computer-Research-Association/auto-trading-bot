from __future__ import annotations

from typing import List, Any

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

import app.domains.performance.repository as performance_repository
from app.domains.performance.schemas import *

# =============================================================================
# 내부 유틸: 스냅샷 객체에서 날짜/자산 필드 안전하게 꺼내기
# =============================================================================
def _snap_date(s: Any):
    # 모델에 따라 date 또는 base_date로 들어올 수 있어 둘 다 대응
    return getattr(s, "date", None) or getattr(s, "base_date", None)

def _snap_assets(s) -> float:
    # PortfolioSnapshot 기준: equity_krw가 현재 평가금액
    if hasattr(s, "equity_krw"):
        return float(getattr(s, "equity_krw", 0.0))
    # 혹시 invested만 있는 경우 fallback
    if hasattr(s, "invested_krw"):
        return float(getattr(s, "invested_krw", 0.0))
    return 0.0


# =============================================================================
# 공개 API (routes.py가 호출하는 함수들) - 반드시 존재해야 함
# =============================================================================
async def get_summary( q: PerformanceQuery) -> PerformanceSummary:

    if q.start_date and q.end_date and q.start_date > q.end_date:
        raise HTTPException(status_code=422, detail="start_date must be <= end_date")

    snaps = await performance_repository.get_daily_snapshots(q.start_date, q.end_date)

    if not snaps:
        raise HTTPException(status_code=404, detail="No snapshots found for given date range")

    start_assets = _snap_assets(snaps[0])
    end_assets = _snap_assets(snaps[-1])

    pnl = end_assets - start_assets
    pnl_rate = (pnl / start_assets) if start_assets != 0 else 0.0

    return PerformanceSummary(
        start_assets_krw=float(start_assets),
        end_assets_krw=float(end_assets),
        pnl_krw=float(pnl),
        pnl_rate=float(pnl_rate),
    )

async def get_chart(q: PerformanceQuery, db: AsyncSession ) -> PerformanceChartResponse:

    if q.start_date and q.end_date and q.start_date > q.end_date:
        raise HTTPException(status_code=422, detail="start_date must be <= end_date")

    snaps = await performance_repository.get_daily_snapshots(
        db,
        q.start_date,
        q.end_date,
    )

    if not snaps:
        raise HTTPException(status_code=404, detail="No snapshots found for given date range")

    points: List[PerformancePoint] = []

    start_assets = _snap_assets(snaps[0]) or 1.0

    for s in snaps:
        d = _snap_date(s)
        assets = _snap_assets(s)
        pnl = assets - start_assets
        pnl_rate = (pnl / start_assets) if start_assets != 0 else 0.0

        points.append(
            PerformancePoint(
                base_date=d,
                assets_krw=float(assets),
                pnl_krw=float(pnl),
                pnl_rate=float(pnl_rate),
            )
        )

    return PerformanceChartResponse(points=points)


async def get_daily_table(q: PerformanceQuery) -> PerformanceDailyResponse:

    if q.start_date and q.end_date and q.start_date > q.end_date:
        raise HTTPException(status_code=422, detail="start_date must be <= end_date")

    snaps = await performance_repository.get_daily_snapshots(q.start_date, q.end_date)

    if not snaps:
        raise HTTPException(status_code=404, detail="No snapshots found for given date range")

    rows: List[PerformanceDailyRow] = []

    if not snaps:
        return PerformanceDailyResponse(rows=rows)

    start_assets = _snap_assets(snaps[0]) or 1.0

    for s in snaps:
        d = _snap_date(s)
        assets = _snap_assets(s)
        pnl = assets - start_assets
        pnl_rate = (pnl / start_assets) if start_assets != 0 else 0.0

        rows.append(
            PerformanceDailyRow(
                base_date=d,
                assets_krw=float(assets),
                pnl_krw=float(pnl),
                pnl_rate=float(pnl_rate),
            )
        )

        return PerformanceDailyResponse(rows=rows)


async def get_all_performance(db: AsyncSession, q: PerformanceQuery) -> PerformanceResponse:
    if q.start_date and q.end_date and q.start_date > q.end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    snaps = await performance_repository.get_daily_snapshots(db=db, start=q.start_date, end=q.end_date)
    if not snaps:
        raise HTTPException(status_code=404, detail="No snapshots found for given date range")

    points: List[PerformancePoint] = []
    rows: List[PerformanceDailyRow] = []

    start_assets = 0.0
    end_assets = 0.0

    if snaps:
        # 시작 자산/종료 자산 계산
        start_assets = _snap_assets(snaps[0])
        end_assets = _snap_assets(snaps[-1])

        # 기준 자산 (0으로 나누기 방지)
        base_assets = start_assets if start_assets != 0 else 1.0

        for s in snaps:
            d = _snap_date(s)
            val = _snap_assets(s)
            pnl = val - base_assets
            pnl_rate = (pnl / base_assets) if base_assets != 0 else 0.0

            # 차트용 포인트 생성
            if hasattr(d, "date"):
                d = d.date()

            points.append(
                PerformancePoint(
                    date=d,
                    assets_krw=float(val),
                    pnl_krw=float(pnl),
                    pnl_rate=float(pnl_rate),
                )
            )

            # 일별 데이터 행 생성
            rows.append(PerformanceDailyRow(
                date=d,
                assets_krw=float(val),
                pnl_krw=float(pnl),
                pnl_rate=float(pnl_rate)
            ))

    # 2. 요약 정보 생성
    pnl_total = end_assets - start_assets
    pnl_rate_total = (pnl_total / start_assets) if start_assets != 0 else 0.0

    summary = PerformanceSummary(
        period_label=q.period,
        start_assets_krw=float(start_assets),
        end_assets_krw=float(end_assets),
        pnl_krw=float(pnl_total),
        pnl_rate=float(pnl_rate_total)
    )

    # 3. 통합 응답 반환
    return PerformanceResponse(
        summary=summary,
        chart=points,
        daily=rows
    )
