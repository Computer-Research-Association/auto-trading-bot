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

#전략 성과 업데이트
def update_strategy_performance(
    session: Session,
    pnl: float,
    pnl_rate: float,
) -> None:

    perf = session.get(StrategyPerformance, 1)

    if perf is None:
        perf = StrategyPerformance(id=1)
        session.add(perf)

    perf.total_trades += 1
    perf.total_pnl += pnl
    perf.total_pnl_rate += pnl_rate

    if pnl > 0:
        perf.win_trades += 1
    else:
        perf.lose_trades += 1

    perf.win_rate = (perf.win_trades / perf.total_trades) * 100
    perf.last_updated_at = utcnow()

    session.commit()