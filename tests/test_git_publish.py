from pathlib import Path
import subprocess

import pytest

from xfetch.config import PublishTargetConfig
from xfetch.publishing.git_publish import publish_repo
from xfetch.publishing.url import build_pages_url


def test_build_pages_url_for_project_pages_repo():
    cfg = PublishTargetConfig(repo_owner="guchengwei", repo_name="link-vault")
    url = build_pages_url(cfg, slug="x-123-alice")
    assert url == "https://guchengwei.github.io/link-vault/d/x-123-alice/"


def _git(*args: str, cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _init_repo(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    target_repo = tmp_path / "target-repo"
    subprocess.run(["git", "init", "-b", "main", str(target_repo)], check=True, capture_output=True)
    _git("config", "user.name", "Hermes Agent", cwd=target_repo)
    _git("config", "user.email", "hermes@example.com", cwd=target_repo)
    _git("remote", "add", "origin", str(remote), cwd=target_repo)
    return target_repo, remote


def test_publish_repo_commits_and_pushes_to_local_remote(tmp_path):
    target_repo, remote = _init_repo(tmp_path)
    (target_repo / "README.md").write_text("hello\n", encoding="utf-8")
    revision = publish_repo(target_repo, branch="main", commit_message="publish: x-123-alice", paths=["README.md"])
    assert revision
    assert _git("rev-parse", "HEAD", cwd=target_repo) == revision
    remote_head = subprocess.run(
        ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert remote_head == revision


def test_publish_repo_leaves_unrelated_dirty_files_uncommitted(tmp_path):
    target_repo, _remote = _init_repo(tmp_path)
    (target_repo / "content/item").mkdir(parents=True)
    (target_repo / "content/item/document.json").write_text("{}\n", encoding="utf-8")
    (target_repo / "notes.txt").write_text("do not commit\n", encoding="utf-8")
    publish_repo(target_repo, branch="main", commit_message="publish item", paths=["content/item"])
    changed = _git("show", "--name-only", "--format=", "HEAD", cwd=target_repo)
    assert "content/item/document.json" in changed
    assert "notes.txt" not in changed
    assert "?? notes.txt" in _git("status", "--short", cwd=target_repo)


def test_publish_repo_rejects_unrelated_pre_staged_changes(tmp_path):
    target_repo, _remote = _init_repo(tmp_path)
    (target_repo / "content/item").mkdir(parents=True)
    (target_repo / "content/item/document.json").write_text("{}\n", encoding="utf-8")
    (target_repo / "notes.txt").write_text("staged\n", encoding="utf-8")
    _git("add", "notes.txt", cwd=target_repo)
    with pytest.raises(RuntimeError, match="unrelated staged"):
        publish_repo(target_repo, branch="main", commit_message="publish item", paths=["content/item"])


def test_publish_repo_rejects_unrelated_local_commits(tmp_path):
    target_repo, remote = _init_repo(tmp_path)
    (target_repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    publish_repo(target_repo, branch="main", commit_message="seed", paths=["seed.txt"])

    (target_repo / "notes.txt").write_text("local only\n", encoding="utf-8")
    _git("add", "notes.txt", cwd=target_repo)
    _git("commit", "-m", "local work", cwd=target_repo)
    remote_before = subprocess.run(
        ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    (target_repo / "content/item").mkdir(parents=True)
    (target_repo / "content/item/document.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="exactly at origin/main"):
        publish_repo(target_repo, branch="main", commit_message="publish: item", paths=["content/item"])

    remote_after = subprocess.run(
        ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert remote_after == remote_before
