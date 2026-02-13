from __future__ import annotations
from datetime import datetime
from typing import List
from pydantic import BaseModel

class LogRow(BaseModel):
    id: int
    timestamp: datetime
    level: str
    category: str
    event_name: str
    message: str

    class Config:
        from_attributes = True

class LogResponse(BaseModel):
    rows: List[LogRow]
    total: int
