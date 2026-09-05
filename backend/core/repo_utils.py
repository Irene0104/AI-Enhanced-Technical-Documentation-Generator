import subprocess
import tempfile
import shutil
import os


def clone_repo(repo_url: str) -> str:
    """
    Clones repo_url into a fresh temp directory and returns the local path.
    Caller is responsible for cleaning it up with cleanup_repo() when done.
    """
    temp_dir = tempfile.mkdtemp(prefix="docgen_")

    result = subprocess.run(
        ["git", "clone", "--depth", "200", repo_url, temp_dir],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )

    if result.returncode != 0:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"git clone failed: {result.stderr}")

    return temp_dir


def cleanup_repo(local_path: str) -> None:
    """Deletes the cloned repo from disk once analysis is done."""
    shutil.rmtree(local_path, ignore_errors=True)