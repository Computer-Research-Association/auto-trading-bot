import pandas as pd
import numpy as np


def calculate_rsi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """
    RSI 계산
    SMMA 방식을 사용하여 업계 표준값 산출
    """
    delta = df['close'].diff()

    # gain(상승분)과 loss(하락분) 분리 (clip을 사용하여 가독성 향상)
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder 방식: ewm의 com을 period -1로 설정
    # $RS = \frac{\text{Avg Gain}}{\text{Avg Loss}}$
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    # 0으로 나누기 방지 및 rsi 계산
    # $RSI = 100 - \frac{100}{1 + RS}$
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    return rsi.fillna(50) # 초기값이나 에러 발생 시 중립값(50) 반환

    def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int=3) -> pd.DataFrame:
        """
        Stochastic Oscillator (%K, %D) 계산
        횡보장 (High == Low)에서의 Zero Division 에러 방지 로직 포함
        """
        