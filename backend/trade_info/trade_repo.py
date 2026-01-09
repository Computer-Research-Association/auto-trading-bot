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

#일별 스냅샷 저장( 하루 1개)
    def upsert_daily_snapshot(
            session: Session,
            *,
            snapshot_date: date,
            balance: float,
            daily_pnl: float,
            daily_pnl_rate: float,
            cumulative_pnl: float,
            cumulative_pnl_rate: float,
    ) -> None:

        snapshot = session.exec(
            select(DailySnapshot)
            .where(DailySnapshot.snapshot_date == snapshot_date)
        ).first()

        if snapshot is None:
            snapshot = DailySnapshot(
                snapshot_date=snapshot_date,
                balance=balance,
                daily_pnl=daily_pnl,
                daily_pnl_rate=daily_pnl_rate,
                cumulative_pnl=cumulative_pnl,
                cumulative_pnl_rate=cumulative_pnl_rate,
            )
            session.add(snapshot)
        else:
            snapshot.balance = balance
            snapshot.daily_pnl = daily_pnl
            snapshot.daily_pnl_rate = daily_pnl_rate
            snapshot.cumulative_pnl = cumulative_pnl
            snapshot.cumulative_pnl_rate = cumulative_pnl_rate

        session.commit()

        #최근 거래 조회
        def get_recent_trades(
                session: Session,
                limit: int = 20,
        ):
            return session.exec(
                select(TradeModel)
                .order_by(TradeModel.traded_at.desc())
                .limit(limit)
            ).all()

        #기간별 거래 조회
        def get_trades_between(
                session: Session,
                start: datetime,
                end: datetime,
        ):
            return session.exec(
                select(TradeModel)
                .where(TradeModel.traded_at >= start)
                .where(TradeModel.traded_at <= end)
                .order_by(TradeModel.traded_at.asc())
            ).all()
