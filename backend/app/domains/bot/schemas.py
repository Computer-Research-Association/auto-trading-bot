from pydantic import BaseModel
from datetime import datetime

class BotStatusResponse(BaseModel):
    is_active: bool
    is_dry_run: bool
    strategy_name: str
    balance: float
    is_holding: bool
    avg_buy_price: float
    target_price: float # Deprecated
    stop_loss: float    # Deprecated
    target_buy_price: float = 0.0
    target_sell_price: float = 0.0
    target_stop_loss: float = 0.0
    last_reason: str
    timestamp: datetime
    profit_rate: float
    sparkline_data: list[float] = []
