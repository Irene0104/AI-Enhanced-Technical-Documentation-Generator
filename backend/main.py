from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from routers import docs_router, job

from db.database import Base, engine
from models.doc_artifact import Document
from models.job import Run
from models.code_unit import CodeUnit
from models.commit_event import CommitEvent

Base.metadata.create_all(bind=engine)

app= FastAPI(
    title="AI-Enhanced technical documentation generator",
    description="api to generate codebase documentation from slack comms, git history and codebases",
    version= "0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"^https://ai-enhanced-technical-documentation(-generator-[a-z0-9]+)?\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]

)
app.include_router(docs_router.router, prefix=settings.API_PREFIX)
app.include_router(job.router, prefix=settings.API_PREFIX)

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)
    print("Hello")