from fastapi import Request
from trading.bot import TradingBot

def get_bot(request: Request) -> TradingBot:
    """TradingBot 인스턴스 주입을 위한 의존성 함수"""
    return request.app.state.bot
