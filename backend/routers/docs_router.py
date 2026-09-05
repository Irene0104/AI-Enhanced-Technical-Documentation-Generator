import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from db.database import get_db, SessionLocal
from models.doc_artifact import Document
from models.job import Run
from schema.doc_artifact import DocArtifactResponse
from schema.job import RunResponse, RunCreate

from core.repo_utils import clone_repo, cleanup_repo
from core.code_analyzer import analyze_code
from core.history_analyser import analyze_history
from core.comms_analyser import analyze_comms
from core.correlation import correlate
from core.synthesis import synthesize_docs
from core.fixtures.sample_comms import SAMPLE_COMMS_MESSAGES

router = APIRouter(
    prefix="/runs",
    tags=["runs"]
)

@router.post("/create", response_model=RunResponse)
def create_run(
    request: RunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    run_id = str(uuid.uuid4())

    run = Run(
        run_id=run_id,
        repo_url=request.repo_url,
        status="pending"
    )
    db.add(run)
    db.commit()

    background_tasks.add_task(
        generate_docs_task,
        run_id=run_id,
        repo_url=request.repo_url
    )

    return run

def generate_docs_task(run_id: str, repo_url: str):
    db = SessionLocal()
    repo_path = None

    try:
        run = db.query(Run).filter(Run.run_id == run_id).first()
        if not run:
            return

        try:
            run.status = "processing"
            db.commit()

            repo_path = clone_repo(repo_url)

            code_units = analyze_code(repo_path, run_id, db)          # Code Analyzer
            commits = analyze_history(repo_path, run_id, db)           # History Analyzer

            # NOTE: no real comms integration yet — using fixture data
            # as a stand-in until a real Slack/comms source is wired up.
            comms = analyze_comms(run_id, db, SAMPLE_COMMS_MESSAGES)   # Comms Analyzer

            correlations = correlate(run_id, db)                      # Correlation Agent
            artifacts = synthesize_docs(run_id, repo_path, correlations, db)  # Synthesis Agent

            run.doc_artifact_ids = [a.id for a in artifacts]
            run.status = "completed"
            run.completed_at = datetime.now()
            db.commit()

        except Exception as e:
            run.status = "failed"
            run.completed_at = datetime.now()
            run.error = str(e)
            db.commit()
    finally:
        if repo_path:
            cleanup_repo(repo_path)
        db.close()

@router.get("/{run_id}/artifacts", response_model=list[DocArtifactResponse])
def get_run_artifacts(run_id: str, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if not run.doc_artifact_ids:
        return []

    artifacts = db.query(Document).filter(Document.id.in_(run.doc_artifact_ids)).all()
    return artifacts