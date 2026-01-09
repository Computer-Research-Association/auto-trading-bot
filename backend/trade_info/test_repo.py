from datetime import date
from sqlmodel import SQLModel, Session, create_engine

from .trade_models import TradeModel
from .trade_repo import get_recent_trades, upsert_daily_snapshot, update_strategy_performance

DATABASE_URL = "sqlite:///./test_v2.db"
engine = create_engine(DATABASE_URL, echo=True)

def main():
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        trade = TradeModel(
            market="BTC-KRW",
            side="buy",
            price=42000000,
            volume=0.01,
            fee=50.0,
            # traded_at은 TradeModel의 default_factory로 자동 생성되게 두는 걸 추천
        )
        session.add(trade)
        session.commit()
        session.refresh(trade)  # id 등 자동 생성값 반영(추천)

        recent = get_recent_trades(session, limit=5)
        print("recent trades:")
        for t in recent:
            print(t.model_dump())

        update_strategy_performance(session, pnl=5000, pnl_rate=0.3)

        upsert_daily_snapshot(
            session,
            snapshot_date=date.today(),
            balance=1000000,
            daily_pnl=5000,
            daily_pnl_rate=0.3,
            cumulative_pnl=5000,
            cumulative_pnl_rate=0.3,
        )

        print("✅ repo smoke test done")

if __name__ == "__main__":
    main()