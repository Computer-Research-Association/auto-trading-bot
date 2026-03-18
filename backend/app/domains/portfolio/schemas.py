from __future__ import annotations

from pydantic import BaseModel


class AssetItem(BaseModel):
    symbol: str
    quantity: float
    avg_buy_price: float
    current_price: float
    evaluation_krw: float


class PortfolioSummary(BaseModel):
    krw_total: float
    krw_available: float
    total_buy_krw: float
    total_assets_krw: float
    total_pnl_krw: float
    total_pnl_rate: float


class PortfolioAssetsResponse(BaseModel):
    summary: PortfolioSummary
    items: list[AssetItem]