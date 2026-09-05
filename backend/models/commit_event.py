from sqlalchemy import Column, Integer, String, DateTime, JSON
from db.database import Base


class CommitEvent(Base):
    __tablename__ = "commit_events"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, index=True)  # which run this belongs to
    sha = Column(String, index=True, nullable=False)
    author = Column(String, nullable=True)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=True)
    files_changed = Column(JSON, nullable=True)  # list of file paths touched