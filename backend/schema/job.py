from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class RunBase(BaseModel):
    repo_url: str


class RunResponse(BaseModel):
    run_id: str
    status: str
    created_at: datetime
    doc_artifact_ids: Optional[list[int]] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


class RunCreate(RunBase):
    pass