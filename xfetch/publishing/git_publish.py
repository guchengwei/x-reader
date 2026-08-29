from __future__ import annotations

from pathlib import Path
import subprocess


def _run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, check=check, capture_output=True, text=True)


def _stdout(repo: Path, *args: str) -> str:
    return _run_git(repo, *args).stdout.strip()


def _normalize_paths(repo: Path, paths: list[str | Path]) -> list[str]:
    normalized: list[str] = []
    for value in paths:
        raw = Path(value)
        candidate = raw.resolve() if raw.is_absolute() else (repo / raw).resolve()
        try:
            relative = candidate.relative_to(repo)
        except ValueError as exc:
            raise ValueError(f"publish path escapes target repo: {value}") from exc
        text = relative.as_posix()
        if text in {"", "."}:
            raise ValueError("refusing to stage the whole target repo")
        normalized.append(text)
    if not normalized:
        raise ValueError("publish paths must not be empty")
    return sorted(set(normalized))


def _is_allowed(path: str, allowed: list[str]) -> bool:
    return any(path == root or path.startswith(root.rstrip("/") + "/") for root in allowed)


def _assert_no_unrelated_staged_changes(repo: Path, allowed: list[str]) -> None:
    staged = [line for line in _stdout(repo, "diff", "--cached", "--name-only").splitlines() if line]
    unexpected = [path for path in staged if not _is_allowed(path, allowed)]
    if unexpected:
        raise RuntimeError("target repo already has unrelated staged changes: " + ", ".join(unexpected))


def assert_publish_base(target_repo: Path, branch: str) -> None:
    repo = Path(target_repo).resolve()
    if not (repo / ".git").exists():
        raise FileNotFoundError(f"not a git repo: {repo}")

    probe = _run_git(repo, "ls-remote", "--exit-code", "--heads", "origin", branch, check=False)
    if probe.returncode != 0:
        local = _run_git(repo, "rev-parse", "--verify", "HEAD", check=False)
        if local.returncode != 0:
            return
        count = _stdout(repo, "rev-list", "--count", "HEAD")
        subject = _stdout(repo, "log", "-1", "--format=%s")
        if count == "1" and subject.startswith("publish: "):
            return
        raise RuntimeError(f"origin/{branch} does not exist but target repo already has local commits")

    current = _run_git(repo, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    current_branch = current.stdout.strip()
    if current.returncode != 0 or current_branch != branch:
        raise RuntimeError(f"target repo must be on branch {branch}; current branch is {current_branch or '<detached>'}")

    _stdout(repo, "fetch", "origin", f"{branch}:refs/remotes/origin/{branch}")
    local = _stdout(repo, "rev-parse", "HEAD")
    remote = _stdout(repo, "rev-parse", f"origin/{branch}")
    if local != remote:
        ahead = _stdout(repo, "rev-list", "--count", f"origin/{branch}..HEAD")
        subject = _stdout(repo, "log", "-1", "--format=%s")
        if ahead == "1" and subject.startswith("publish: "):
            return
        raise RuntimeError(f"target repo must be exactly at origin/{branch} before publishing")


def commit_repo(target_repo: Path, branch: str, commit_message: str, paths: list[str | Path]) -> str:
    repo = Path(target_repo).resolve()
    if not (repo / ".git").exists():
        raise FileNotFoundError(f"not a git repo: {repo}")

    allowed = _normalize_paths(repo, paths)
    _assert_no_unrelated_staged_changes(repo, allowed)
    assert_publish_base(repo, branch)
    _stdout(repo, "add", "--", *allowed)
    staged = _stdout(repo, "diff", "--cached", "--name-only")
    if staged:
        try:
            _stdout(repo, "commit", "-m", commit_message)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(exc.stderr.strip() or exc.stdout.strip()) from exc
    return _stdout(repo, "rev-parse", "HEAD")


def push_repo(target_repo: Path, branch: str) -> str:
    repo = Path(target_repo).resolve()
    try:
        _stdout(repo, "push", "origin", f"HEAD:{branch}")
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr.strip() or exc.stdout.strip()) from exc
    return _stdout(repo, "rev-parse", "HEAD")


def publish_repo(target_repo: Path, branch: str, commit_message: str, paths: list[str | Path]) -> str:
    revision = commit_repo(target_repo, branch=branch, commit_message=commit_message, paths=paths)
    push_repo(target_repo, branch=branch)
    return revision
