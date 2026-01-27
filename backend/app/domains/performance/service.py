from __future__ import annotations

from typing import List, Any

from .repository import PerformanceRepository
from .schemas import (
    PerformanceQuery,
    PerformanceSummary,
    PerformancePoint,
    PerformanceChartResponse,
    PerformanceDailyRow,
    PerformanceDailyResponse,
    PerformanceResponse,
)

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
def get_summary(repo: PerformanceRepository, q: PerformanceQuery) -> PerformanceSummary:
    snaps = repo.get_daily_snapshots(q.start_date, q.end_date)

    if not snaps:
        return PerformanceSummary()

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


def get_chart(repo: PerformanceRepository, q: PerformanceQuery) -> PerformanceChartResponse:
    snaps = repo.get_daily_snapshots(q.start_date, q.end_date)

    points: List[PerformancePoint] = []
    if not snaps:
        return PerformanceChartResponse(points=points)

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


def get_daily_table(repo: PerformanceRepository, q: PerformanceQuery) -> PerformanceDailyResponse:
    snaps = repo.get_daily_snapshots(q.start_date, q.end_date)

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


def get_all_performance(repo: PerformanceRepository, q: PerformanceQuery) -> PerformanceResponse:
    # 1. 한 번만 조회
    try:
        print(f"DEBUG: get_all_performance called with start={q.start_date}, end={q.end_date}")
        snaps = repo.get_daily_snapshots(q.start_date, q.end_date)
    
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
                points.append(PerformancePoint(
                    base_date=d,
                    assets_krw=float(val),
                    pnl_krw=float(pnl),
                    pnl_rate=float(pnl_rate)
                ))
    
                # 일별 데이터 행 생성
                rows.append(PerformanceDailyRow(
                    base_date=d,
                    assets_krw=float(val),
                    pnl_krw=float(pnl),
                    pnl_rate=float(pnl_rate)
                ))
    
        # 2. 요약 정보 생성
        pnl_total = end_assets - start_assets
        pnl_rate_total = (pnl_total / start_assets) if start_assets != 0 else 0.0
    
        summary = PerformanceSummary(
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ERROR in get_all_performance: {e}")
        raise e
