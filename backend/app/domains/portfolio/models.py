from __future__ import annotations

from datetime import date
from typing import Any, Dict

from sqlalchemy import Date, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.utills.models import BaseEntity


class PortfolioSnapshot(BaseEntity):
    __tablename__ = "portfolio_snapshots"

    base_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    invested_krw: Mapped[float] = mapped_column(Float, nullable=False)
    equity_krw: Mapped[float] = mapped_column(Float, nullable=False)
    pnl_krw: Mapped[float] = mapped_column(Float, nullable=False)
    pnl_rate: Mapped[float] = mapped_column(Float, nullable=False)

    assets: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
