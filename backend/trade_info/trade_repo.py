from datetime import date
from sqlmodel import Session, select

from .trade_models import (
    TradeModel,
    StrategyPerformance,
    DailySnapshot,
    utcnow,
)

#거래 1건 저장
def save_trade(session: Session, trade: TradeModel) -> TradeModel:
    session.add(trade)
    session.commit()
    session.refresh(trade)
    return trade