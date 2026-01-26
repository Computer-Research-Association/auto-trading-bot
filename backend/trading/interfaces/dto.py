from decimal import Decimal
from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict

# 모든 DTO는 데이터를 보호하기 위해 frozen(불변) 상태로 설정합니다.
# 또한 Decimal 타입을 지원하여 금융 데이터의 정밀도를 유지합니다.


class SlotDTO(BaseModel):
    """
    각 슬롯의 운영 정책과 현재 할당된 종목 정보
    slot_no: int              # 슬롯 번호 (1 ~ 4)
    is_active: bool           # 슬롯 가동 여부
    ticker: str               # 현재 추적 중인 종목명
    strategy_id: str          # 적용 전략 클래스 명칭
    params: Dict              # 전략용 변수 (JSON에서 변환됨)
    budget: Decimal           # 슬롯에 할당된 가용 예산
    """
    model_config = ConfigDict(frozen=True)

    slot_no = int  # 슬롯 번호 (1 ~ 4)
    is_active: bool  # 슬롯 가동 여부
    ticker: str  # 현재 추적 중인 종목묭
    strategy_id: str  # 적용 전략 클래스 명칭
    paprams: Dict  # 전략용 변수
    budget: Decimal  # 슬롯에 할당한 예산


class BotStateDTO(BaseModel):
    """
    워커의 실시간 매매 상태 및 복구용 데이터
    lot_no: int              # 해당 슬롯 번호
    is_holding: bool          # 현재 코인 보유 여부
    avg_buy_price: Decimal    # 매수 평균 단가
    total_quantity: Decimal   # 보유 중인 코인 수량
    stop_loss_price: Decimal  # 실시간 갱신되는 손절가
    buy_cost: Decimal         # 수수료 포함 실제 투입 총액
    """
    model_config = ConfigDict(frozen=True)
    slot_no = int  # 해당 슬롯 번호
    is_holding: bool  # 현재 코인 보유 여부
    avg_buy_price: Decimal  # 매수 평균 단가
    total_quantity: Decimal  # 보유 중인 코인 수량
    stop_loss_price: Decimal  # 실시간 갱신되는 손절가
    buy_cost: Decimal  # 수수료 포함 실제 투입 총액
