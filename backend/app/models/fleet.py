from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base


class Fleet(Base):
    __tablename__ = "fleets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)