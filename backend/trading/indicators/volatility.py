import pandas as pd
import numpy as np


def get_bbands(
    df: pd.DataFrame, length: int = 20, std: float = 2.0
) -> pd.DataFrame:
    """
    볼린저 밴드 계산 (BB).

    - bb_middle: 중심선 (SMA)
    - bb_upper/bb_lower: 상/하단 밴드
    - bb_width: 밴드 폭 (변동성 수축/ 확장 측정)
    """
    if 'close' not in df.columns:
        raise ValueError("BB 계산을 위해 'close' 컬럼이 필요합니다.")

    # 중심선 및 표준편차 계산
    middle_band = df['close'].rolling(window=length).mean()
    std_dev = df['close'].rolling(window=length).std()

    upper_band = middle_band + (std_dev * std)
    lower_band = middle_band - (std_dev * std)

    # 0으로 나누기 방지 및 밴드폭 계산
    denom = middle_band.replace(0, np.nan)
    bandwidth = (upper_band - lower_band) / denom

    return pd.DataFrame({
        'bb_middle': middle_band,
        'bb_upper': upper_band,
        'bb_lower': lower_band,
        'bb_width': bandwidth.fillna(0)
    })
