from typing import List,Optional,Dict
from datetime import datetime
from pydantic import BaseModel


class DocArtifactBase(BaseModel):
    title: str
    run_id: Optional[str] = None

    class Config:
        from_attributes = True


class CreateRunRequest(BaseModel):
    repo_url: str


class DocArtifactResponse(DocArtifactBase):
    id: int
    created_at: datetime
    content: str
    type: str = "adr"
    status: str = "draft"
    sources: List[str] = []

    class Config:
        from_attributes = True