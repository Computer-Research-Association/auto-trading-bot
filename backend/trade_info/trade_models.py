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
    fee: Optional[float] = Field(default=None # 거래시 발생한 수수료

