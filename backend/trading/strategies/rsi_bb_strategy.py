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
        반환값의 trade_params 객체 안에 목표 매수, 익절, 손절가를 할당하여 
        bot.py의 모니터링 루프로 전파합니다.
        """
        if len(ohlcv_df) < 3:
            return {"decision": "HOLD", "percentage": 0.0, "reason": "데이터 부족", "trade_params": {}}

        # 최신 데이터 행 추출
        last = ohlcv_df.iloc[-1]
        is_holding = account_info.get('is_holding', False)

        # 지표 및 현재가 추출
        rsi = last["rsi"]
        bb_upper = last["bb_bb_upper"]
        bb_lower = last["bb_bb_lower"]
        bb_mid = last["bb_bb_middle"]
        current_price = last["close"]

        # 폭포수(Waterfall) 방어: 최근 3캔들 동안의 하단 밴드 급락률(Slope) 검사
        bb_lower_series = ohlcv_df["bb_bb_lower"]
        drop_rate = (bb_lower_series.iloc[-1] - bb_lower_series.iloc[-3]) / bb_lower_series.iloc[-3]
        is_waterfall = drop_rate < -0.02  # 3캔들 내 하단 밴드가 2% 이상 하락 중이면 급락으로 간주

        decision = "HOLD"
        percentage = 0.0
        reason = f"관망: 조건 미충족 (RSI {rsi:.2f})"
        
        # trade_params에 목표 타겟들을 기본 할당 (0이면 미지정)
        trade_params = {
            "target_buy_price": 0.0,
            "target_sell_price": 0.0,
            "target_stop_loss": 0.0,
            "reason": reason
        }

        # [1] 매수 시그널 및 전략 타겟 수립 (미보유 시)
        if not is_holding:
            if rsi <= 30:
                if is_waterfall:
                    reason = f"[방어] 폭포수 감지 (하락률: {drop_rate*100:.2f}%) - 매수 대기"
                    trade_params["reason"] = reason
                else:
                    decision = "BUY"
                    percentage = 1.0
                    reason = f"매수 대기: 과매도(RSI: {rsi:.2f}) 통과"
                    
                    # 봇의 집행관(monitor loop)이 바라볼 절대 가격 세팅
                    # BB 하단에 닿거나 더 떨어지면 즉각 매수, 매수 후 익절은 BB 상단, 손절은 -3%
                    trade_params["target_buy_price"] = bb_lower
                    trade_params["target_sell_price"] = bb_upper * 0.997
                    trade_params["target_stop_loss"] = bb_lower * 0.97
                    trade_params["reason"] = reason

        # [2] 매도 시그널 및 전략 타겟 갱신 (보유 시)
        elif is_holding:
            if rsi >= 70:
                decision = "SELL"
                percentage = 1.0
                reason = f"매도 대기: 과매수(RSI:{rsi:.2f}) 도달"
                # 목표 매도가는 보수적으로 설정
                trade_params["target_sell_price"] = current_price
                trade_params["reason"] = reason
            else:
                # 홀딩 중: 실시간으로 변하는 BB 상단/하단을 익/손절 라인으로 지속 추적.
                # 전략 지휘관 함수로서 봇의 메모리를 갱신함
                decision = "HOLD"
                reason = f"보유 중: 목표가 추적 갱신 (RSI: {rsi:.2f})"
                trade_params["target_sell_price"] = bb_upper * 0.997
                trade_params["target_stop_loss"] = (bb_mid - ((bb_upper - bb_mid) * 1.5)) # 유동적 손절선
                trade_params["reason"] = reason

        return {
            "decision": decision,
            "percentage": percentage,
            "reason": reason,
            "trade_params": trade_params
        }
