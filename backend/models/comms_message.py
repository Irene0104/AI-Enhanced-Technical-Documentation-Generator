from sqlalchemy import Column, Integer, String, DateTime, Boolean
from db.database import Base


class CommsMessage(Base):
    __tablename__ = "comms_messages"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, index=True)  # which run this belongs to
    author = Column(String, nullable=True)
    text = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=True)
    is_decision = Column(Boolean, default=False)
    summary = Column(String, nullable=True)  # LLM-extracted one-line summary, if is_decision