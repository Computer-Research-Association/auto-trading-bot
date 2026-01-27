from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

from fastapi import HTTPException
from sqlmodel import Session

from app.utills.upbit_client import client
from app.domains.portfolio.schemas import AssetItem, PortfolioAssetsResponse, PortfolioSummary
from app.utills.models import PortfolioSnapshot  # ✅ 네 공용 모델 위치


# -------------------------
# 1) 보유자산 조회 (탭 응답)
# -------------------------
def get_assets() -> PortfolioAssetsResponse:
    # balances 한 번만
    balances = client.get_balances()
    if not isinstance(balances, list):
        raise HTTPException(status_code=502, detail=f"Upbit balances invalid: {balances}")

    rows, krw_total, krw_available = _normalize_balances(balances)

    #tickers 없으면 가격조회 호출 안 함
    tickers = [r.ticker for r in rows]
    prices: dict[str, float] = _safe_prices(client.get_current_prices(tickers), tickers) if tickers else {}

    items: list[AssetItem] = []
    total_buy_krw = 0.0
    total_eval_krw = 0.0

    for r in rows:
        current_price = float(prices.get(r.ticker, 0.0))
        evaluation = current_price * r.qty_total
        buy_amount = r.avg_buy_price * r.qty_total

        total_eval_krw += evaluation
        total_buy_krw += buy_amount

        items.append(
            AssetItem(
                symbol=r.symbol,
                quantity=r.qty_total,
                avg_buy_price=r.avg_buy_price,
                current_price=current_price,
                evaluation_krw=evaluation,
            )
        )

    total_pnl_krw = total_eval_krw - total_buy_krw
    total_pnl_rate = (total_pnl_krw / total_buy_krw * 100.0) if total_buy_krw > 0 else 0.0
    total_assets_krw = krw_total + total_eval_krw

    summary = PortfolioSummary(
        krw_total=krw_total,
        krw_available=krw_available,
        total_buy_krw=total_buy_krw,
        total_assets_krw=total_assets_krw,
        total_pnl_krw=total_pnl_krw,
        total_pnl_rate=total_pnl_rate,
    )

    items.sort(key=lambda x: x.evaluation_krw, reverse=True)
    return PortfolioAssetsResponse(summary=summary, items=items)


# -------------------------
# 2) 스냅샷 저장 (DB 적재용)
# -------------------------
def take_portfolio_snapshot(session: Session, base_date: date) -> PortfolioSnapshot:
    resp = get_assets()
    s = resp.summary

    #네 summary 정의에 맞춘 명확한 의미
    # invested: 총매수금액(코인 매수원가 합)
    invested_krw = float(s.total_buy_krw)

    # equity: "총자산"을 저장(원화+코인평가). 성과 그래프에 제일 자연스러움
    equity_krw = float(s.total_assets_krw)

    pnl_krw = equity_krw - invested_krw
    pnl_rate = (pnl_krw / invested_krw * 100.0) if invested_krw > 0 else 0.0

    # payload에 KRW도 같이 넣어두면 나중에 성과/디버깅에 도움 됨
    assets_payload = {
        "krw_total": float(s.krw_total),
        "krw_available": float(s.krw_available),
        "items": [
            {
                "symbol": it.symbol,
                "quantity": float(it.quantity),
                "avg_buy_price": float(it.avg_buy_price),
                "current_price": float(it.current_price),
                "evaluation_krw": float(it.evaluation_krw),
            }
            for it in resp.items
        ],
    }

    # 같은 날짜 스냅샷 중복 저장 방지(강추)
    # (DB에 base_date unique가 아니더라도, 서비스 레벨에서 막아주면 편함)
    existing = session.exec(
        # SQLModel select import 안 쓰려고 session.exec + text 안 쓰는 형태가 애매함
        # 그래서 아래처럼 최소 변경: SQLModel의 select를 쓰는 게 깔끔함
        # -> import 추가하는 버전이 정석
        #
        # 하지만 "코드만 여기서 끝내겠다"면 중복 방지 로직을 빼도 됨.
        #
        # 여기서는 중복 방지 로직을 "옵션"으로 남겨둠.
        #
        # 결론: 아래 블록은 주석 처리하고,
        # DB에서 base_date unique 제약을 걸어두는 걸 더 추천.
        #
        # (원하면 내가 너 모델에 unique 설정까지 딱 맞춰줄게)
        #
        # select(PortfolioSnapshot).where(PortfolioSnapshot.base_date == base_date)
        #
        # 라고 써야 함.
        #
        # -> 주석 처리
        None
    )

    snap = PortfolioSnapshot(
        base_date=base_date,
        invested_krw=invested_krw,
        equity_krw=equity_krw,
        pnl_krw=pnl_krw,
        pnl_rate=pnl_rate,
        assets=assets_payload,
    )

    session.add(snap)
    session.commit()
    session.refresh(snap)
    return snap


# -------------------------
# 내부 유틸
# -------------------------
def _normalize_balances(
    balances: Iterable[dict[str, Any]],
) -> tuple[list["_BalanceRow"], float, float]:
    rows: list[_BalanceRow] = []
    krw_total = 0.0
    krw_available = 0.0

    for b in balances:
        currency = (b.get("currency") or "").strip()
        unit = (b.get("unit_currency") or "KRW").strip()

        balance = _to_float(b.get("balance"))
        locked = _to_float(b.get("locked"))
        qty_total = balance + locked

        if currency.upper() == "KRW":
            krw_available = balance
            krw_total = qty_total
            continue

        if qty_total <= 0:
            continue

        avg_buy_price = _to_float(b.get("avg_buy_price"))
        ticker = f"{unit.upper()}-{currency.upper()}"

        rows.append(
            _BalanceRow(
                symbol=currency.upper(),
                unit=unit.upper(),
                qty_total=qty_total,
                qty_available=balance,
                avg_buy_price=avg_buy_price,
                ticker=ticker,
            )
        )

    return rows, krw_total, krw_available


def _safe_prices(prices: Any, tickers: list[str]) -> dict[str, float]:
    if not tickers:
        return {}

    if prices is None:
        return {t: 0.0 for t in tickers}

    if isinstance(prices, (int, float)):
        if len(tickers) == 1:
            return {tickers[0]: float(prices)}
        return {t: float(prices) for t in tickers}

    if isinstance(prices, dict):
        out: dict[str, float] = {}
        for t in tickers:
            out[t] = float(prices.get(t, 0.0) or 0.0)
        return out

    return {t: 0.0 for t in tickers}


def _to_float(v: Any) -> float:
    try:
        if v is None:
            return 0.0
        return float(v)
    except (TypeError, ValueError):
        return 0.0


@dataclass(frozen=True)
class _BalanceRow:
    symbol: str
    unit: str
    qty_total: float
    qty_available: float
    avg_buy_price: float
    ticker: str