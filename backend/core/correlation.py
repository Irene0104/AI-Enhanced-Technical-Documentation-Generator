import re
from datetime import timedelta
from sqlalchemy.orm import Session

from models.code_unit import CodeUnit
from models.commit_event import CommitEvent
from models.comms_message import CommsMessage

# Messages and commits within this window of each other get a time-proximity boost
TIME_PROXIMITY_WINDOW = timedelta(days=7)


def _mentions_identifier(text: str, identifier: str) -> bool:
    """
    Word-boundary match so 'int' doesn't falsely match inside
    'int_to_bytes' — we want exact identifier mentions only.
    """
    pattern = r"\b" + re.escape(identifier) + r"\b"
    return re.search(pattern, text) is not None


def _time_proximity_score(msg_time, commit_time) -> float:
    """Returns 1.0 for same-instant, decaying to 0.0 at the edge of the window, 0 beyond it."""
    if msg_time is None or commit_time is None:
        return 0.0

    delta = abs((msg_time - commit_time).total_seconds())
    window_seconds = TIME_PROXIMITY_WINDOW.total_seconds()

    if delta > window_seconds:
        return 0.0

    return 1.0 - (delta / window_seconds)


def correlate(run_id: str, db: Session) -> list[dict]:
    """
    Correlation Agent: for every comms message flagged as a decision,
    find code units it mentions by name, then find commits that touched
    those code units' files, and score each match by how close in time
    the message and commit occurred.

    Returns a list of correlation dicts, each with:
      - code_unit, commit, message, confidence_score
    """
    code_units = db.query(CodeUnit).filter(CodeUnit.run_id == run_id).all()
    commits = db.query(CommitEvent).filter(CommitEvent.run_id == run_id).all()
    decision_messages = (
        db.query(CommsMessage)
        .filter(CommsMessage.run_id == run_id, CommsMessage.is_decision == True)  # noqa: E712
        .all()
    )

    # Index commits by which files they touched, for fast lookup
    commits_by_file = {}
    for commit in commits:
        for filepath in (commit.files_changed or []):
            commits_by_file.setdefault(filepath, []).append(commit)

    correlations = []

    for message in decision_messages:
        for code_unit in code_units:
            if not _mentions_identifier(message.text, code_unit.name):
                continue

            matching_commits = commits_by_file.get(code_unit.path, [])
            if not matching_commits:
                # code unit is mentioned but no commit touched its file — weak signal, skip
                continue

            for commit in matching_commits:
                time_score = _time_proximity_score(message.timestamp, commit.timestamp)

                # base confidence for the name match itself, boosted by time proximity
                confidence = 0.5 + (0.5 * time_score)

                correlations.append({
                    "code_unit": code_unit,
                    "commit": commit,
                    "message": message,
                    "confidence_score": round(confidence, 2),
                })

    # highest-confidence correlations first
    correlations.sort(key=lambda c: c["confidence_score"], reverse=True)

    return _deduplicate(correlations)


def _deduplicate(correlations: list[dict]) -> list[dict]:
    """
    Keep only the single best commit per (code_unit, message) pair —
    a message might match a code unit against many historical commits
    that touched the same file, but we only want one ADR per decision,
    not one per commit. Tiebreak on confidence, then most recent commit.
    """
    best_by_pair = {}

    for c in correlations:
        key = (c["code_unit"].id, c["message"].id)
        existing = best_by_pair.get(key)

        if existing is None:
            best_by_pair[key] = c
            continue

        existing_time = existing["commit"].timestamp
        candidate_time = c["commit"].timestamp
        existing_file_count = len(existing["commit"].files_changed or [])
        candidate_file_count = len(c["commit"].files_changed or [])

        is_better_score = c["confidence_score"] > existing["confidence_score"]

        # among tied scores, prefer the more targeted commit (fewer files) —
        # broad refactors touching many files are less likely to be the
        # actual decision commit than a focused change
        is_tied_but_more_targeted = (
            c["confidence_score"] == existing["confidence_score"]
            and candidate_file_count > 0
            and (existing_file_count == 0 or candidate_file_count < existing_file_count)
        )

        # final tiebreak if still tied on both: most recent
        is_tied_but_newer = (
            c["confidence_score"] == existing["confidence_score"]
            and candidate_file_count == existing_file_count
            and candidate_time is not None
            and existing_time is not None
            and candidate_time > existing_time
        )

        if is_better_score or is_tied_but_more_targeted or is_tied_but_newer:
            best_by_pair[key] = c

    deduped = list(best_by_pair.values())
    deduped.sort(key=lambda c: c["confidence_score"], reverse=True)
    return deduped