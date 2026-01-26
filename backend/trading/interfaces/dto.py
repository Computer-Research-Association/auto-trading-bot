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
