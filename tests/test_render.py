from xfetch.storage.render import render_bundle_page


def test_render_bundle_page_writes_index_html(tmp_path):
    bundle_dir = tmp_path / "2026-03" / "x-123-alice"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "document.json").write_text(
        '{"title":"Hello","canonical_url":"https://x.com/alice/status/123","author_handle":"alice","created_at":"2026-03-31T00:00:00Z","text":"hello world"}',
        encoding="utf-8",
    )
    out_dir = tmp_path / "site"
    page = render_bundle_page(bundle_dir, out_dir, public_url="https://guchengwei.github.io/x-reader/d/x-123-alice/")
    assert page == out_dir / "d" / "x-123-alice" / "index.html"
    html = page.read_text(encoding="utf-8")
    assert "<title>Hello</title>" in html
    assert "rel=\"canonical\"" in html
