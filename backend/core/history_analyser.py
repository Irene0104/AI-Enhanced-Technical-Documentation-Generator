import subprocess
from datetime import datetime
from sqlalchemy.orm import Session

from models.commit_event import CommitEvent

COMMIT_MARKER = "@@COMMIT@@"
FIELD_SEP = "||"


def analyze_history(repo_path: str, run_id: str, db: Session) -> list[CommitEvent]:
    """
    Reads git log from the locally cloned repo (same clone used by
    the Code Analyzer) and stores each commit as a CommitEvent row,
    including which files it touched.
    """
    # %H=full sha, %an=author name, %ad=author date, %s=subject line
    log_format = f"{COMMIT_MARKER}%H{FIELD_SEP}%an{FIELD_SEP}%ad{FIELD_SEP}%s"

    result = subprocess.run(
        [
            "git", "log",
            f"--pretty=format:{log_format}",
            "--date=iso",
            "--name-only",
        ],
        cwd=repo_path,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(f"git log failed: {result.stderr}")

    created_commits = []
    current_commit = None
    current_files = []

    for line in result.stdout.splitlines():
        if line.startswith(COMMIT_MARKER):
            # flush the previous commit before starting a new one
            if current_commit is not None:
                current_commit.files_changed = current_files
                db.add(current_commit)
                created_commits.append(current_commit)

            sha, author, date_str, message = line[len(COMMIT_MARKER):].split(FIELD_SEP, 3)

            try:
                timestamp = datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                timestamp = None

            current_commit = CommitEvent(
                run_id=run_id,
                sha=sha,
                author=author,
                message=message,
                timestamp=timestamp,
            )
            current_files = []

        elif line.strip():
            # a file path belonging to the current commit
            current_files.append(line.strip())

    # flush the final commit after the loop ends
    if current_commit is not None:
        current_commit.files_changed = current_files
        db.add(current_commit)
        created_commits.append(current_commit)

    db.commit()
    return created_commits