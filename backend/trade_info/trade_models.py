from __future__ import annotations
from datetime import datetime, date, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Index

#거래 체결 시각알기 위함 (날짜 + 시간)
def utcnow() -> datetime:
    return datetime.now(timezone.utc)

#거래 1건을 DB 테이블 한 행으로 저장하기 위함
class TradeModel(SQLModel, table=True):
    #거래 기록 하나를 식별하는 번호 (DB가 자동으로 증가시킴)
    id: Optional[int] = Field(default=None, primary_key=True)

    market: str = Field(index= True) #어떤 코인 거래했는지
    side: str = Field(index = True) # buy or sell
    price: float
    volume: float # 수량
    fee: Optional[float] = Field(default=None) # 거래시 발생한 수수료

#해당 거래로 벌거나 잃은 금액
pnl: Optional[float] = Field(default=None)
#수익률
pnl_rate: Optional[float] = Field(default=None)
#체결 시각
traded_at: datetime = Field(default_factory=utcnow, index=True)
#복합 인덱스 셍성 (market + traded at)
__table_args__ = (
    Index("ix_trade_market_time", "market", "traded_at"),
)

class StrategyPerformance(SQLModel, table=True):
        id: int = Field(default=1, primary_key=True)

        total_trades: int = Field(default=0)  #거래 수 집계
        win_trades: int = Field(default=0)
        lose_trades: int = Field(default=0)

        total_pnl: float = Field(default=0.0) #누적 손익
        total_pnl_rate: float = Field(default=0.0) #누적 수익률

        max_drawdown: Optional[float] = Field(default=None) #최대 나폭
        win_rate: Optional[float] = Field(default=None) #승률

        #성과 통계가 언제 기준인지 표시
        last_updated_at: datetime = Field(default_factory=utcnow, index= True)

#하루가 끝났을 때의 계좌 상태와 성과
class DailySnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    #어느 날짜의 기록인지 확인
    snapshot_date: date = Field(index=True, unique=True)

    balance: float #하루 종료시 자산
    daily_pnl: float #일별 손익
    daily_pnl_rate: float

    # 누적 손익 (전략 시작 이후)
    cumulative_pnl: float
    cumulative_pnl_rate: float

    #스냅샷 생성 시각
    created_at: datetime = Field(default_factory=utcnow, index=True)

    __table_args__ = ( #인덱스 (날짜 기준 조회 성능 향상)
        Index("ix_snapshot_date", "snapshot_date"),
    )