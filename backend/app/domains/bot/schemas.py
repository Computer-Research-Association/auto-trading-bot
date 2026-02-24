from pydantic import BaseModel
from datetime import datetime

class BotStatusResponse(BaseModel):
    is_active: bool
    is_dry_run: bool
    strategy_name: str
    balance: float
    is_holding: bool
    avg_buy_price: float
    target_price: float
    stop_loss: float
    last_reason: str
    timestamp: datetime
    profit_rate: float
