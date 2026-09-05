import uuid
from db.database import Base, engine, SessionLocal
from models.code_unit import CodeUnit
from models.commit_event import CommitEvent
from models.comms_message import CommsMessage
from models.doc_artifact import Document
from core.repo_utils import clone_repo, cleanup_repo
from core.code_analyzer import analyze_code
from core.history_analyser import analyze_history
from core.comms_analyser import analyze_comms
from core.correlation import correlate
from core.synthesis import synthesize_docs
from core.fixtures.sample_comms import SAMPLE_COMMS_MESSAGES

Base.metadata.create_all(bind=engine)

RUN_ID = str(uuid.uuid4())
print(f"Run ID: {RUN_ID}")

db = SessionLocal()
repo_path = clone_repo("https://github.com/pallets/itsdangerous")

try:
    units = analyze_code(repo_path, run_id=RUN_ID, db=db)
    print(f"Found {len(units)} code units")

    commits = analyze_history(repo_path, run_id=RUN_ID, db=db)
    print(f"Found {len(commits)} commits")

    comms = analyze_comms(run_id=RUN_ID, db=db, messages=SAMPLE_COMMS_MESSAGES)
    print(f"Found {len(comms)} comms messages")

    correlations = correlate(run_id=RUN_ID, db=db)
    print(f"Found {len(correlations)} correlations (deduplicated)")

    docs = synthesize_docs(run_id=RUN_ID, repo_path=repo_path, correlations=correlations, db=db)
    print(f"\nGenerated {len(docs)} ADRs")
    for d in docs:
        print(f"\n--- {d.title} ---")
        print(d.content)
finally:
    cleanup_repo(repo_path)
    db.close()