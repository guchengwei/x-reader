import json

from xfetch.config import RuntimeConfig
from xfetch.models import NormalizedDocument
from xfetch.pipeline import bundle as bundle_module
from xfetch.pipeline.bundle import build_slug, bundle_month, write_bundle


def test_build_slug_uses_external_id_and_handle():
    assert build_slug("x", "123", "Elon_Musk") == "x-123-elon-musk"


def test_bundle_month_falls_back_to_fetched_at_when_created_at_missing():
    assert bundle_month(None, "2026-03-31T12:34:56Z") == "2026-03"


def _doc(**overrides):
    values = dict(
        source_type="x",
        source_url="https://x.com/a/status/123",
        canonical_url="https://x.com/a/status/123",
        external_id="123",
        title="hello",
        author="alice",
        author_handle="alice",
        created_at="2026-03-31T00:00:00Z",
        language=None,
        text="hello",
        markdown="# hello",
        summary=None,
    )
    values.update(overrides)
    return NormalizedDocument(**values)


def test_write_bundle_creates_expected_files(tmp_path):
    cfg = RuntimeConfig(content_root=tmp_path, site_root=tmp_path / "site")
    bundle_dir = write_bundle(_doc(), cfg)
    assert (bundle_dir / "document.json").exists()
    assert (bundle_dir / "index.md").exists()
    assert (bundle_dir / "publish.json").exists()
    assert (bundle_dir / "assets").is_dir()


def test_write_bundle_downloads_assets_and_rewrites_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(bundle_module, "_download_asset", lambda url, timeout=20: (b"jpeg-bytes", "image/jpeg"))
    cfg = RuntimeConfig(content_root=tmp_path, site_root=tmp_path / "site")
    doc = _doc(
        markdown="# hello\n\n![](https://example.com/image.jpg)\n",
        assets=[{"url": "https://example.com/image.jpg", "type": "image", "source": "article_inline", "media_id": "m1"}],
        content_kinds=["text", "images"],
    )
    bundle_dir = write_bundle(doc, cfg)
    assert (bundle_dir / "assets" / "image-01.jpg").read_bytes() == b"jpeg-bytes"
    assert "![](assets/image-01.jpg)" in (bundle_dir / "index.md").read_text(encoding="utf-8")
    document = json.loads((bundle_dir / "document.json").read_text(encoding="utf-8"))
    assert document["assets"][0]["local_path"] == "assets/image-01.jpg"
    assert document["capture_status"] == "complete"


def test_asset_failure_downgrades_complete_capture(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise ValueError("blocked asset")
    monkeypatch.setattr(bundle_module, "_download_asset", fail)
    cfg = RuntimeConfig(content_root=tmp_path, site_root=tmp_path / "site")
    bundle_dir = write_bundle(
        _doc(assets=[{"url": "http://127.0.0.1/private.jpg", "type": "image"}], content_kinds=["text", "images"]),
        cfg,
    )
    document = json.loads((bundle_dir / "document.json").read_text(encoding="utf-8"))
    assert document["capture_status"] == "partial"
    assert document["metadata"]["asset_capture_failures"] == 1
    assert document["assets"][0]["capture_error"] == "blocked asset"
