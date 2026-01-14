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

        def decide(self, ohlcv_df: pd.DataFrame, account_info: dict, context: dict) -> dict:
            last = ohlcv_df.iloc[-1]

            is_holding = account_info.get('is_holding', False)

            rsi = last[self.rsi_col]
            bb_upper = last[self.bb_up_col]
            macd_hist = last[self.macd_hist_col]

            decision = "HOLD"
            percentage = 0.0
            reason = "조건 미충족"
            
            # 매수 로직 (미보유 시에만)
            if not is_holding:
                if rsi <= self.params.get("rsi_buy_level", 30) and last['close'] <= bb_lower:
                    if macd_hist > 0:
                        decision = "BUY"
                        percentage = 1.0
                        reason = f"과매도 구간 탈출 신호 (RSI: {rsi: .2f})"

            # 매도 로직 (보유 시에만)
            elif is_holding:
                if rsi >= self.params.get("rsi_sell_level", 70) or last['close'] > bb_upper:
                    decision = "SELL"
                    percentage = 1.0
                    reason = f"과매수 구간 /BB 상단 도달 (RSI: {rsi: .2f})"

            return {"decision": decision, "percentage": percentage, "reason": reason, "metadata": {}}