from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

TxType = Literal["all", "buy", "sell", "deposit", "withdraw"]
Period = Literal["7d", "30d", "90d", "180d", "all"]

class TradeHistoryQuery(BaseModel):
    period: Period = "30d"
    tx_type: TxType = "all"
    keyword: Optional[str] = None
    page: int = 1
    limit: int = 20

class TradeHistoryRow(BaseModel):
    timestamp: datetime
    market: str
    side: str
    volume: float
    price: float
    amount: float
    fee: float = 0
    strategy: Optional[str] = None

    class Config:
        from_attributes = True

class TradeHistoryResponse(BaseModel):
    rows: List[TradeHistoryRow] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    limit: int = 20

    class Config:
        from_attributes = True
