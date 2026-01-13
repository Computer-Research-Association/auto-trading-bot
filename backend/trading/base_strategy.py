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

    
