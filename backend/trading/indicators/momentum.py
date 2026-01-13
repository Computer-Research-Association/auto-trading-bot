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
    avg_gain = gain.ewm(com=length - 1, min_periods=length).mean()
    avg_loss = loss.ewm(com=length - 1, min_periods=length).mean()

    # 0으로 나누기 방지 및 rsi 계산
    # $RSI = 100 - \frac{100}{1 + RS}$
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    return rsi.fillna(50)  # 초기값이나 에러 발생 시 중립값(50) 반환


def calculate_stochastic(df: pd.DataFrame, k_length: int = 14, d_length: int=3) -> pd.DataFrame:
    """
    Stochastic Oscillator (%K, %D) 계산
    횡보장 (High == Low)에서의 Zero Division 에러 방지 로직 포함
    """
    
    low_min = df['low'].rolling(window=k_length).min()
    high_max = df['high'].rolling(window=k_length).max()

    # 분모(Range) 계산: $High_{max} - Low_{min}$
    diff = high_max - low_min

    # %K line: $\%K = 100 \times \frac{Close - Low_{min}}{High_{max} - Low_{min}}$
    # diff가 0인 경우(가장 높은 가와 낮은 가가 같을 때) NaN 처리 후 0으로 채움
    k_line = 100 * ((df['close'] - low_min) / diff.replace(0, np.nan))
    k_line = k_line.fillna(0)

    # %D line: K라인의 단순 이동 평균
    d_line = k_line.rolling(window=d_length).mean()

    return pd.DataFrame({
        'stoch_k': k_line,
        'stoch_d': d_line

    })