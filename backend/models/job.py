from sqlalchemy import Column, Integer, String, DateTime,JSON
from sqlalchemy.sql import func
from db.database import Base

class Run(Base):
    __tablename__="runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, index=True, unique=True)
    session_id = Column(String, index=True)
    repo_url = Column(String)
    status = Column(String)
    doc_artifact_ids = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
