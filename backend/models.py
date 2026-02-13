from sqlalchemy.orm import Mapped, mapped_column
from app.utills.models import BaseEntity

class User(BaseEntity):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)