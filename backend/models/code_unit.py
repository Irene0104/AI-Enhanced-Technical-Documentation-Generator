from sqlalchemy import Column, Integer, String
from db.database import Base


class CodeUnit(Base):
    __tablename__ = "code_units"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, index=True)  # which run this belongs to
    path = Column(String, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "function" or "class"
    lineno = Column(Integer, nullable=False)