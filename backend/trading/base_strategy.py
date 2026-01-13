import pandas as pd
from abc import ABC, abstractmethod
from .indicators import add_indicators


class BaseStrategy(ABC):
    """
    모든 트레이디 전략의 추상 베이스 클래스 (interface).
    설계 문서에 정의된 표준 입력 및 출력 규격을 준수한다.
    """

    def __init__(self):
        # 1. 필수 식별 정보 (Strategy Indentity)
        self.strategy_id = "BASE_STRATEGY"
        self.display_name = "Base Strategy"
        self.version = "1.0.0"
        self.required_candles = 120  # 판단에 필요한 최소 캔들 수
        self.data_interval = "minute15"  # 분석 분봉 단위

        # 2. 이 전략에서 사용할 지표 목록 (자식 클래스에서 오버라이드)
        self.indicator_list = []

    def get_info(self) -> dict:
        """
        전략의 정보를 반환하여 웹 UI 및 엔진 관리에 사용한다.
        """
        return {
            "strategy_id": self.strategy_id,
            "display_name": self.display_name,
            "version": self.version,
            "required_candles": self.required_candles,
            "data_interval": self.data_interval
        }

    def validate_data(self, df: pd.DataFrame) -> tuple[bool, str]:
        """
        데이터의 충분성 및 신뢰성을 최종 검사한다.
        """
        if df is None or df.empty:
            return False, "데이터가 존재하지 않습니다."
        
        # 캔들 개수 검증
        if len(df) < self.required_candles:
            return False, f"데이터 부족 (필요: {self.required_candles}, 현재: {len(df)})"
        
        # 시간 순서 정렬 확인 (과거 -> 현재)
        if not df['datetime'].is_monotonic_increasing:
            return False, "데이터가 시간 순서로 정렬되지 않았습니다."
        
        return True, "Success"
    
    def apply_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        부모 클래스에서 정의된 indicator_list를 기반으로 지표를 일괄 추가한다.
        자식 클래스는 리스트만 채우면 되도록 로직 공통화
        """
        if not self.indicator_list:
            return df
        return add_indicators(df, self.indicator_list)