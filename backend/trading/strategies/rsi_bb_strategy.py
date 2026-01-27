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

    def decide(self, ohlcv_df: pd.DataFrame, account_info: dict, context: dict) -> dict:
        """
        RSI와 볼린저 밴드 지표를 바탕으로 매매 결정을 내립니다.
        """

        # 최신 데이터 행 추출
        last = ohlcv_df.iloc[-1]
        is_holding = account_info.get('is_holding', False)

        # 지표 및 현재가 추출
        rsi = last["rsi"]
        bb_upper = last["bb_bb_upper"]
        bb_lower = last["bb_bb_lower"]
        current_price = last["close"]

        decision = "HOLD"
        percentage = 0.0
        # 기본 reason에 현재 지표 상태 요약 포함
        reason = f"관망: 조건 미충족 (RSI {rsi: .2f}, 가격: {current_price:,.0f})"
        trade_params = {}

        # 매수 로직 (미보유 시)
        # 조건: SI 30 이하(과매도) AND 현재가가 볼린저 밴드 하단선 터치 이하
        if not is_holding:
            if rsi <= 30 and current_price <= bb_lower:
                decision = "BUY"
                percentage = 1.0
                reason = f"매수: 과매도(RSI: {rsi:.2f}) 및 BB 하단({bb_lower:,.0f})"
                # 권장 손절가
                trade_params = {"stop_loss": current_price * 0.97}

        # 매도 로직
        # 조건: RSI 70 이상(과매수) OR 현재가가 볼린저 밴드 상단선 돌파 이상
        elif is_holding:
            if rsi >= 70 or current_price >= bb_upper:
                decision = "SELL"
                percentage = 1.0
                reason = f"매도: 과매수(RSI:{rsi:.2f}) 또는 BB 상단({bb_upper:,.0f}) 도달"

        return {
            "decision": decision,
            "percentage": percentage,
            "reason": reason,
            "trade_params": trade_params
        }
