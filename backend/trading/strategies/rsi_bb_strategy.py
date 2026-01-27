import pandas as pd
from .base_strategy import BaseStrategy


class RSIBBStrategy(BaseStrategy):
    """
    RSI와 볼린저 밴드를 결합한 실전 매매 전략 (Ver 1.0)
    평균 회귀(Mean Reversion) 로직을 기반으로 합니다.
    """
    def __init__(self, **kwargs):
        # 1. 식별 정보 고정 (Identity)
        kwargs["strategy_id"] = "RSI_BB_V1"
        kwargs["required_candles"] = 200  # 최소 200개 캔들 필요
        super().__init__(**kwargs)

        # 2. 파라미터 하드코딩
        # 외부 주입 없이 전략 내부에서 최적 수치 고정
        self.rsi_length = 14
        self.bb_length = 20
        self.bb_std = 2.0

        # 3. 지표 리스트 설정
        # indicators 패키지 리스트 생성
        self.indicator_list = [
            {
                "name": "rsi",
                "output_name": "rsi",
                "params": {"length": self.rsi_length}
            },
            {
                "name": "bb",
                "output_name": "bb",
                "params": {"length": self.bb_length, "std": self.bb_std}
            }
        ]