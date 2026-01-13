import pandas as pd
import numpy as np


def get_bolinger_bands(
    df: pd.DataFrame, length: int = 20, num_std: float = 2.0
) -> pd.DataFrame:
    """
    볼린저 밴드 계산 (BB).

    - bb_middle: 중심선 (SMA)
    - bb_upper/bb_lower: 상/하단 밴드
    - bb_width: 밴드 폭 (변동성 수축/ 확장 측정)
    """
    if 'close' not in df.columns:
        raise ValueError("BB 계산을 위해 'close 컬럼이 필요합니다.")
