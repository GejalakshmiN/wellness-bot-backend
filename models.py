from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    message = Column(String)
    reply = Column(String)
    sentiment = Column(String)
    stress_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
