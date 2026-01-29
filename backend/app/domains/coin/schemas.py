from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

TxType = Literal["all", "buy", "sell", "deposit", "withdraw"]
Period = Literal["7d", "30d", "90d", "180d"]

class TradeHistoryQuery(BaseModel):
    period: Period = "30d"
    tx_type: TxType = "all"
    keyword: None
    page: int = 1
    size: int = 20

class TradeHistoryRow(BaseModel):
    executed_at: datetime
    market: str
    tx_type: TxType
    qty: float
    price_krw: float
    amount_krw: float
    fee_krw: float = 0
    strategy: None

class TradeHistoryResponse(BaseModel):
    rows: List[TradeHistoryRow] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    size: int = 20
