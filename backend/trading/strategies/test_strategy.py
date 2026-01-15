import pandas as pd
from .base_strategy import BaseStrategy


class MacdBbRsiStrategy(BaseStrategy):
    """
    MACD, Bollinger Bands, rsi를 결합한 전략 클래스
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # self.params.get()을 사용하여 외부 주입 값이 없을 때의 안전성 확보
        # 전략파일에서 반환 받을 접두어 이름을 정의한다
        self.rsi_key = "rsi"
        self.bb_prefix = "bb"
        self.macd_prefix = "macd"

        # 세부 컬럼명 변수화. 
        # macd, bb와 같이 한 지표에 여러 종류 반환이 있을 때를 대비
        # indicatrors의 내부 함수에서 반환 명칭이 바뀔 경우 여기서 수정
        self.col_bb_upper = f"{self.bb_prefix}_bb_upper"
        self.col_bb_lower = f"{self.bb_prefix}_bb_lower"
        self.col_macd_hist = f"{self.macd_prefix}_MACDh_12_26_9"

        # 외부 설정이 없을 때 기본 지표 리스트 생성
        if not self.indicator_list:
            self.indicator_list = [
                {"name": "rsi", "output_name": self.rsi_key, "params": {"length": self.params.get("rsi_len", 14)}},
                {"name": "bb", "output_name": self.bb_prefix, "params": {"length": self.params.get("bb_len", 20), "std": self.params.get("bb_std", 2.0)}},
                {"name": "macd", "output_name": self.macd_prefix, "params": {"fast": 12, "slow": 26, "signal": 9}}
            ]

    def decide(self, ohlcv_df: pd.DataFrame, account_info: dict, context: dict) -> dict:
        last = ohlcv_df.iloc[-1]
        is_holding = account_info.get('is_holding', False)
        
        # 미리 정의한 변수를 사용해 데이터 추출
        rsi = last[self.rsi_key]
        bb_upper = last[self.col_bb_upper]
        bb_lower = last[self.col_bb_lower]
        macd_hist = last[self.col_macd_hist]

        decision = "HOLD"
        percentage = 0.0
        reason = "조건 미충족"
            
        # 매수 로직 (미보유 시에만)
        if not is_holding:
            if rsi <= self.params.get("rsi_buy_level", 30) and last['close'] <= bb_lower:
                if macd_hist > 0:
                    decision = "BUY"
                    percentage = 1.0
                    reason = f"과매도 구간 탈출 신호 (RSI: {rsi:.2f})"

        # 매도 로직 (보유 시에만)
        elif is_holding:
            if rsi >= self.params.get("rsi_sell_level", 70) or last['close'] > bb_upper:
                decision = "SELL"
                percentage = 1.0
                reason = f"과매수 구간 /BB 상단 도달 (RSI: {rsi:.2f})"

        return {
            "decision": decision, 
            "percentage": percentage, 
            "reason": reason,        
            "metadata": {
                "rsi": float(rsi),
                "macd_hist": float(macd_hist),
                "params": self.params
            }
        }    