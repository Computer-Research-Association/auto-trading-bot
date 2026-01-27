import pandas as pd
from .base_strategy import BaseStrategy

class RSIBBStrategy(BaseStrategy):
    """
    RSI와 볼린저 밴드를 결합한 실전 매매 전략 (Ver 1.0)
    평균 회귀(Mean Reversion) 로직을 기반으로 합니다.
    """