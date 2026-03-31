from xfetch.config import RuntimeConfig
from xfetch.models import NormalizedDocument
from xfetch.pipeline.bundle import build_slug, bundle_month, write_bundle


def test_build_slug_uses_external_id_and_handle():
    assert build_slug("x", "123", "Elon_Musk") == "x-123-elon-musk"



def test_bundle_month_falls_back_to_fetched_at_when_created_at_missing():
    assert bundle_month(None, "2026-03-31T12:34:56Z") == "2026-03"



def test_write_bundle_creates_expected_files(tmp_path):
    cfg = RuntimeConfig(content_root=tmp_path, site_root=tmp_path / "site")
    doc = NormalizedDocument(
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
    bundle_dir = write_bundle(doc, cfg)
    assert (bundle_dir / "document.json").exists()
    assert (bundle_dir / "index.md").exists()
    assert (bundle_dir / "publish.json").exists()
    assert (bundle_dir / "assets").is_dir()
