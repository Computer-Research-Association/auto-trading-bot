from decimal import Decimal
from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

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

    slot_no: int  # 슬롯 번호 (1 ~ 4)
    is_active: bool  # 슬롯 가동 여부
    ticker: str  # 현재 추적 중인 종목묭
    strategy_id: str  # 적용 전략 클래스 명칭
    params: Dict  # 전략용 변수
    budget: Decimal = Field(..., ge=0)  # 슬롯에 할당한 예산, 0이상 검증
    updated_at: datetime = Field(default_factory=datetime.now)  # 타임 스탬프 추가

# 2. Bot States 도메인 DTO: 런타임 실시간 상황판


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
    slot_no: int  # 해당 슬롯 번호
    is_holding: bool  # 현재 코인 보유 여부
    avg_buy_price: Decimal = Field(default=Decimal('0'), ge=0)  # 매수 평균 단가
    total_quantity: Decimal = Field(default=Decimal('0'), ge=0)  # 보유 중인 코인 수량
    stop_loss_price: Decimal = Field(default=Decimal('0'), ge=0)  # 실시간 갱신 손절가
    buy_cost: Decimal = Field(default=Decimal('0'), ge=0)  # 수수료 포함 실제 투입 총액
    updated_at: datetime = Field(default_factory=datetime.now)

# 3. Candidate Pool 도메인 DTO: 유망 종목 대기실


class CandidateDTO(BaseModel):
    """스캐너가 발굴한 유망 종목 정보
    ticker: str               # 추천 종목명
    score: Decimal            # 스캐너가 부여한 우선순위 점수
    """
    model_config = ConfigDict(frozen=True)

    ticker: str  # 추천 종목명
    score: Decimal  # 추천 점수
    recommended_at: datetime = Field(default_factory=datetime.now)  # 추천 발생 시간

# 4. Trade History 도메인 DTO: 거래 장부


class TradeDTO(BaseModel):
    """
    slot_no: int  # 슬롯 번호
    ticker: str  # 매매 종목
    side: str  # 매매 신호
    price: Decimal  # 체결 가격
    quantity: Decimal  # 체결 수량
    fee: Decimal # 거래 수수료
    profit_pct: Decimal # 매도 시 확정 수익률
    reason: Optional[str] # 매매 판단 근거
    created_at: datetime = Field(default_factory=datetime.now)  # 거래 발생 시간
    """
    model_config = ConfigDict(frozen=True)

    slot_no: int  # 슬롯 번호
    ticker: str  # 매매 종목
    side: str  # 매매 신호
    price: Decimal = Field(..., gt=0)  # 체결 가격
    quantity: Decimal = Field(..., gt=0)  # 체결 수량
    fee: Decimal = Field(default=Decimal('0'), ge=0)  # 거래 수수료
    profit_pct: Decimal = Decimal('0')  # 매도 시 확정 수익률
    reason: Optional[str] = None  # 매매 판단 근거
    created_at: datetime = Field(default_factory=datetime.now)  # 거래 발생 시간


class LogDTO(BaseModel):
    """
    봇의 상세 동작 및 시스템 상태 기록 데이터
    slot_no: Optional[int]    # 관련 슬롯 번호 (시스템 로그 시 None)
    level: str                # 로그 심각도 (INFO, WARNING, ERROR, CRITICAL)
    message: str              # 실제 로그 내용
    created_at: datetime      # 로그 생성 시각
    """
    model_config = ConfigDict(frozen=True)

    slot_no: Optional[int] = None  # 관련 슬롯 번호, 시스템 로그일 경우 Null(None)
    level: str  # 로그 심각도 등급
    message: str  # 실제 발생한 동작 내용이나 상세 메세지
    created_at: datetime = Field(default_factory=datetime.now)  # 로그가 기록된 시점