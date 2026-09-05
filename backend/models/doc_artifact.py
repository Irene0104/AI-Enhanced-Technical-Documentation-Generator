from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey,JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base

class Document(Base):
    __tablename__="doc_artifacts"

    id= Column(Integer,primary_key=True,index=True)
    title=Column(String,nullable=False)
    content=Column(String, nullable=False)
    type=Column(String,default="adr")
    status=Column(String,default="draft")
    sources=Column(JSON,nullable=True)
    created_at=Column(DateTime(timezone=True),server_default=func.now())