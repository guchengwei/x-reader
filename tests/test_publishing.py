import json
from pathlib import Path

from xfetch.config import PublishTargetConfig
from xfetch.publishing.github_repo_sync import sync_bundle_to_repo


def _make_bundle(root: Path) -> Path:
    bundle_dir = root / "2026-03" / "x-123-alice"
    assets_dir = bundle_dir / "assets"
    assets_dir.mkdir(parents=True)
    (bundle_dir / "document.json").write_text('{"external_id": "123"}\n', encoding="utf-8")
    (bundle_dir / "index.md").write_text("# hello\n", encoding="utf-8")
    (bundle_dir / "publish.json").write_text(
        json.dumps(
            {
                "published": False,
                "public_url": None,
                "target": None,
                "revision": None,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    (assets_dir / "image.jpg").write_text("fake-image", encoding="utf-8")
    return bundle_dir


def test_sync_bundle_to_repo_copies_bundle_only(tmp_path):
    bundle_dir = _make_bundle(tmp_path / "source-content")
    target_repo = tmp_path / "target-repo"
    target_repo.mkdir()
    publish_target = PublishTargetConfig(repo_owner="guchengwei", repo_name="link-vault")

    result = sync_bundle_to_repo(
        bundle_dir,
        target_repo,
        publish_target=publish_target,
        target_subdir="content",
    )

    dest_dir = target_repo / "content" / "2026-03" / "x-123-alice"
    assert result.bundle_destination_dir == dest_dir
    assert result.site_destination_path is None
    assert (dest_dir / "document.json").exists()
    assert (dest_dir / "index.md").exists()
    assert (dest_dir / "publish.json").exists()
    assert (dest_dir / "assets" / "image.jpg").exists()
    assert not (target_repo / "site").exists()


def test_sync_bundle_to_repo_updates_publish_metadata(tmp_path):
    bundle_dir = _make_bundle(tmp_path / "source-content")
    target_repo = tmp_path / "target-repo"
    target_repo.mkdir()
    publish_target = PublishTargetConfig(repo_owner="guchengwei", repo_name="link-vault")

    sync_bundle_to_repo(
        bundle_dir,
        target_repo,
        publish_target=publish_target,
        target_subdir="content",
    )

    publish_data = json.loads((bundle_dir / "publish.json").read_text(encoding="utf-8"))
    assert publish_data["published"] is False
    assert publish_data["public_url"] is None
    assert publish_data["target"]["type"] == "github_pages"
    assert publish_data["target"]["repo_owner"] == "guchengwei"
    assert publish_data["target"]["repo_name"] == "link-vault"
    assert publish_data["target"]["branch"] == "main"
    assert publish_data["target"]["bundle_path"] == "content/2026-03/x-123-alice"
    assert "site_path" not in publish_data["target"]
