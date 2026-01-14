import pandas as pd
from .base_strategy import BaseStrategy


class MacdBbRsiStrategy(BaseStrategy):
    """
    MACD, Bollinger Bands, rsi를 결합한 전략 클래스
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # self.params.get()을 사용하여 외부 주입 값이 없을 때의 안전성 확보
        self.rsi_col = f"RSI_{self.params.get('rsi_len', 14)}"
        self.bb_up_col = "bb_upper"
        self.bb_low_col = "bb_lower"
        self.macd_hist_col = "MACDh_12_26_9"

        # 외부 설정이 없을 때 기본 지표 리스트 생성
        if not self.indicator_list:
            self.indicator_list = [
                {"name": "rsi", "params": {"length": self.params.get("rsi_len", 14)}},
                {"name": "bb", "params": {"length": self.params.get("bb_len", 20), "std": self.params.get("bb_std", 2.0)}},
                {"name": "macd", "params": {"fast": 12, "slow": 26, "signal": 9}}
            ]
