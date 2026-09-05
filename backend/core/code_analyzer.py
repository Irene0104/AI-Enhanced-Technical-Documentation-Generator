import ast
import os
from sqlalchemy.orm import Session

from models.code_unit import CodeUnit


def analyze_code(repo_path: str, run_id: str, db: Session) -> list[CodeUnit]:
    """
    Walks a locally-cloned repo, parses each .py file with the ast module,
    extracts top-level function/class definitions, and stores them as
    CodeUnit rows tied to this run.
    """
    created_units = []

    for root, dirs, files in os.walk(repo_path):
        # skip noise directories entirely
        dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__", "node_modules")]

        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, repo_path).replace(os.sep, "/")

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source, filename=rel_path)
            except (SyntaxError, UnicodeDecodeError):
                continue  # skip files that don't parse cleanly

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    unit_type = "class" if isinstance(node, ast.ClassDef) else "function"

                    code_unit = CodeUnit(
                        run_id=run_id,
                        path=rel_path,
                        name=node.name,
                        type=unit_type,
                        lineno=node.lineno,
                    )
                    db.add(code_unit)
                    created_units.append(code_unit)

    db.commit()
    return created_units