import pandas as pd
from abc import ABC, abstractmethod
from .indicators import add_indicators


class BaseStrategy(ABC):
    """
    모든 트레이디 전략의 추상 베이스 클래스 (interface).
    설계 문서에 정의된 표준 입력 및 출력 규격을 준수한다.
    """