from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class LogBase(BaseModel):
    level: str
    category: str
    event_name: str = Field(..., alias="eventname") # 외부=eventname, 내부=event_name
    message: str
    timestamp: Optional[datetime] = None

    class Config:
        populate_by_name = True

class LogCreate(LogBase):
    pass

class LogResponse(LogBase):
    log_id: int = Field(..., alias="id") # 외부=id, 내부=log_id
    timestamp: datetime # Pydantic v2는 기본적으로 ISO 8601 문자열로 직렬화함

    class Config:
        from_attributes = True
        populate_by_name = True

class LogListResponse(BaseModel):
    items: List[LogResponse]
    total_count: int

class LogStreamItem(BaseModel):
    id: int
    timestamp: str # SSE는 명시적으로 문자열 포맷팅 권장
    category: str
    eventname: str = Field(..., alias="event_name") # 외부=eventname, 내부=event_name
    level: str
    message: str

    class Config:
        from_attributes = True
        populate_by_name = True
