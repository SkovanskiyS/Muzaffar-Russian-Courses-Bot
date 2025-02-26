from sqlalchemy import Column, BigInteger, String, Boolean, Integer
from database.db import Base

class Students(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique primary key
    user_id = Column(BigInteger, unique=True, nullable=False)  # Telegram user ID
    username = Column(String, unique=True, nullable=True)
    first_name = Column(String, default="", nullable=False)
    last_name = Column(String, default="", nullable=True)
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    is_paid = Column(Boolean, default=False)
