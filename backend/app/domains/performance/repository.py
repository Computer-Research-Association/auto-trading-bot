from __future__ import annotations

from datetime import date
from sqlmodel import Session, select

from app.utills.models import PortfolioSnapshot


class PerformanceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_snapshots(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> list[PortfolioSnapshot]:
        stmt = select(PortfolioSnapshot)

        if start is not None:
            stmt = stmt.where(PortfolioSnapshot.base_date >= start)
        if end is not None:
            stmt = stmt.where(PortfolioSnapshot.base_date <= end)

        stmt = stmt.order_by(PortfolioSnapshot.base_date.asc())
        return list(self.session.exec(stmt).all())

    # service가 기대하는 이름을 맞춰주는 alias 메서드 추가
    def get_daily_snapshots(self, start: date, end: date) -> list[PortfolioSnapshot]:
        return self.get_snapshots(start=start, end=end)

