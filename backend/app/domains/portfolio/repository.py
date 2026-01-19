from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session




class PortfolioRepository:
    def get_latest_snapshot(self, session: Session) -> PortfolioSnapshot | None:
        stmt = select(PortfolioSnapshot).order_by(PortfolioSnapshot.id.desc()).limit(1)
        return session.execute(stmt).scalars().first()

    def save_snapshot(self, session: Session, snapshot: PortfolioSnapshot) -> None:
        session.add(snapshot)
        session.commit()
        session.refresh(snapshot)