import subprocess
from sqlalchemy.orm import Session

from models.doc_artifact import Document
from core.synthesis_agent import generate_adr


def _get_commit_diff(repo_path: str, sha: str, filepath: str, max_chars: int = 3000) -> str:
    """
    Fetches the diff for a specific file in a specific commit, from the
    already-cloned local repo (no extra network call). Truncated to keep
    prompts a reasonable size.
    """
    result = subprocess.run(
        ["git", "show", sha, "--", filepath],
        cwd=repo_path,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )

    if result.returncode != 0 or not result.stdout:
        return "(diff unavailable)"

    diff = result.stdout
    if len(diff) > max_chars:
        diff = diff[:max_chars] + "\n... (truncated)"
    return diff


def synthesize_docs(run_id: str, repo_path: str, correlations: list[dict], db: Session) -> list[Document]:
    """
    Synthesis Agent: for each deduplicated correlation, fetch the real
    diff, generate an ADR via the LLM, and store it as a DocArtifact.
    """
    created_docs = []

    for correlation in correlations:
        code_unit = correlation["code_unit"]
        commit = correlation["commit"]
        message = correlation["message"]

        diff = _get_commit_diff(repo_path, commit.sha, code_unit.path)

        result = generate_adr(
            commit_diff=diff,
            correlated_messages=[message.text],
            commit_sha=commit.sha[:8],
        )

        if result.get("error"):
            # skip artifacts that failed to generate cleanly, rather than
            # storing broken/empty content
            continue

        doc = Document(
            title=result.get("title", f"Decision: {code_unit.name}"),
            content=result.get("content", ""),
            type="adr",
            status="draft",
            sources=[commit.sha, str(message.id)],
        )
        db.add(doc)
        created_docs.append(doc)

    db.commit()
    return created_docs