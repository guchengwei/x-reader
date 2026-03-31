from __future__ import annotations

import json
from pathlib import Path
import shutil

from .base import PublishResult


REQUIRED_BUNDLE_FILES = ("document.json", "index.md", "publish.json", "assets")


def _validate_bundle_dir(bundle_dir: Path) -> None:
    missing = [name for name in REQUIRED_BUNDLE_FILES if not (bundle_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"bundle missing required paths: {', '.join(missing)}")
    if bundle_dir.parent == bundle_dir:
        raise ValueError("invalid bundle directory")


def _copy_path(src: Path, dest: Path) -> None:
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def sync_bundle_to_repo(bundle_dir: str | Path, target_repo: str | Path, target_subdir: str = "content") -> PublishResult:
    bundle_path = Path(bundle_dir).resolve()
    repo_path = Path(target_repo).resolve()
    _validate_bundle_dir(bundle_path)
    repo_path.mkdir(parents=True, exist_ok=True)

    month = bundle_path.parent.name
    slug = bundle_path.name
    target_path = f"{target_subdir}/{month}/{slug}"
    destination_dir = repo_path / target_subdir / month / slug
    destination_dir.mkdir(parents=True, exist_ok=True)

    for name in REQUIRED_BUNDLE_FILES:
        _copy_path(bundle_path / name, destination_dir / name)

    publish_payload = {
        "published": False,
        "public_url": None,
        "target": {
            "type": "github_repo_sync",
            "path": target_path,
        },
        "revision": None,
    }
    encoded = json.dumps(publish_payload, ensure_ascii=False, indent=2) + "\n"
    (bundle_path / "publish.json").write_text(encoded, encoding="utf-8")
    (destination_dir / "publish.json").write_text(encoded, encoding="utf-8")

    return PublishResult(
        destination_dir=destination_dir,
        target_path=target_path,
        published=False,
        public_url=None,
        revision=None,
    )
