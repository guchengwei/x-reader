from __future__ import annotations

from pathlib import Path
import subprocess


def _run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def publish_repo(target_repo: Path, branch: str, commit_message: str) -> str:
    repo = Path(target_repo).resolve()
    if not (repo / ".git").exists():
        raise FileNotFoundError(f"not a git repo: {repo}")

    _run_git(repo, "add", "-A")
    status = _run_git(repo, "status", "--short")
    if status:
        try:
            _run_git(repo, "commit", "-m", commit_message)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(exc.stderr.strip() or exc.stdout.strip()) from exc

    try:
        _run_git(repo, "push", "-u", "origin", branch)
    except subprocess.CalledProcessError:
        _run_git(repo, "push", "-u", "origin", f"HEAD:{branch}")
    return _run_git(repo, "rev-parse", "HEAD")
