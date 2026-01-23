from __future__ import annotations
from dataclasses import dataclass
from app.utills.upbit_client import client
from typing import Any, Iterable
from app.domains.portfolio.schemas import AssetItem, PortfolioAssetsResponse,PortfolioSummary


async def get_assets() -> PortfolioAssetsResponse:
    balances = client.get_balances()
    balances = client.get_balances()
    if not isinstance(balances, list):
        from fastapi import HTTPException
        raise HTTPException(status_code=502, detail=f"Upbit balances invalid: {balances}")

    rows, krw_total, krw_available = _normalize_balances(balances)

    tickers = [r.ticker for r in rows]
    prices: dict[str, float] = {}
    if tickers:
        prices = _safe_prices(client.get_current_prices(tickers), tickers)

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
    total_pnl_rate = (
        (total_pnl_krw / total_buy_krw * 100.0) if total_buy_krw > 0 else 0.0
    )
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


def _normalize_balances(
    balances: Iterable[dict[str, Any]],
) -> tuple[list[_BalanceRow], float, float]:
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


@staticmethod
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
