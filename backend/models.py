from sqlmodel import SQLModel, Field
from typing import Optional


class User(SQLModel, table=True):  # table=True가 있어야 실제 DB에 테이블이 생깁니다.
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str