import pandas as pd
import pandas_ta as ta


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """[지표 계산] 데이터프레임에 MACD, BB, RSI 지표를 추가합니다."""
    df = df.copy()

    # 지표 계산
    macd = df.ta.macd(fast=12, slow=26, signal=9)
    bb = df.ta.bbands(length=20, std=2)
    rsi = df.ta.rsi(length=14)

    # 결합 및 결측치 제거
    target_df = pd.concat([df, macd, bb, rsi], axis=1).dropna()
    return target_df


def check_buy_signal(curr: pd.Series, prev: pd.Series) -> bool:
    """매수판단: 현재와 이전 데이터를 비교하여 매수 신호 여부를 반환한다"""
    # 조건 정의
    is_uptrend = curr['MACD_12_26_9'] > 0
    is_oversold = curr['close'] <= curr['BBL_20_2.0'] or prev['close'] <= prev ['BBL_20_2.0']
    is_low_rsi = curr['RSI_14'] < 40

    # 하단선 이탈 후 복귀 시점 포착
    is_rebounding = prev['close'] <= prev['BBL_20_2.0'] and curr['close'] > curr['BBL_20_2.0']
    return is_uptrend and is_oversold and is_low_rsi and is_rebounding


def check_sell_signal(curr: pd.Series, prev: pd.Series) -> bool:
    """매도 판단: 현재 데이터를 기준으로 익절/손절 신호 여부를 반환한다."""
    # 익절 조건
    take_profit_mid = curr['close'] >= curr['BBM_20_2.0']
    take_profit_high = curr['close'] >= curr['BBU_20_2.0'] or curr['RSI_14'] > 70

    # 손절 조건 (MACD 추세 꺾임)
    stop_loss = curr['MACD_12_26_9'] < 0

    return take_profit_mid or take_profit_high or stop_loss


def analyze_strategy(df: pd.DataFrame, is_holding: bool = False) -> str:
    """메인 전략: 분리된 함수들을 조합하여 최종 의사결정 내림"""
    if len(df) < 30:
        return "HOLD"

    target_df = add_indicators(df)

    if len(target_df) < 2:
        return "HOLD"

    curr = target_df.iloc[-1]
    prev = target_df.iloc[-2]

    if not is_holding:
        if check_buy_signal(curr, prev):
            return "BUY"
    else:
        if check_sell_signal(curr, prev):
            return "SELL"
    
    return "HOLD"
