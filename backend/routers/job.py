from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from models.job import Run
from schema.job import RunResponse

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.get("/{run_id}", response_model=RunResponse)
def get_job_status(run_id: str, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.run_id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Job not found")

    return run