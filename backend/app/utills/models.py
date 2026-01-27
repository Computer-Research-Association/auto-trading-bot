from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class PortfolioSnapshot(SQLModel, table=True):
    __tablename__ = "portfolio_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)

    # “어느 날의 결과”를 안정적으로 보여주려면 date가 제일 좋아
    base_date: date = Field(index=True)

    # 총 투자원금 / 현재평가 / 손익
    invested_krw: float
    equity_krw: float
    pnl_krw: float

    # 수익률은 저장해도 되고, 계산해도 됨
    pnl_rate: float  # 예: 0.023 (2.3%)

    # (선택) 자산 구성 상세: 화면에서 종목별도 보여주고 싶으면 저장
    assets: dict = Field(sa_column=Column(JSONB), default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)