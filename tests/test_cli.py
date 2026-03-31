from xfetch.cli import build_parser, main
from xfetch.config import load_config
from xfetch.models import NormalizedDocument


def test_build_parser_exposes_ingest_command():
    parser = build_parser()
    args = parser.parse_args(["ingest", "https://x.com/a/status/1"])
    assert args.command == "ingest"
    assert args.url == "https://x.com/a/status/1"



def test_load_config_prefers_explicit_content_root(tmp_path, monkeypatch):
    monkeypatch.setenv("XFETCH_CONTENT_ROOT", "/tmp/wrong")
    cfg = load_config(content_root=tmp_path)
    assert cfg.content_root == tmp_path.resolve()



def test_load_config_uses_repo_local_defaults_when_no_args_or_env(monkeypatch):
    monkeypatch.delenv("XFETCH_CONTENT_ROOT", raising=False)
    monkeypatch.delenv("XFETCH_SITE_ROOT", raising=False)
    cfg = load_config()
    assert cfg.content_root.name == "content-out"
    assert cfg.site_root.name == "site-out"



def test_cli_ingest_writes_bundle(tmp_path, monkeypatch):
    doc = NormalizedDocument(
        source_type="x",
        source_url="https://x.com/alice/status/123",
        canonical_url="https://x.com/alice/status/123",
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

    class FakeConnector:
        def fetch(self, url):
            return doc

    monkeypatch.setattr("xfetch.cli.pick_connector", lambda url: FakeConnector())
    rc = main(["ingest", "https://x.com/alice/status/123", "--content-root", str(tmp_path)])
    assert rc == 0



def test_cli_returns_2_for_unsupported_url(tmp_path):
    rc = main(["ingest", "https://example.com/post/123", "--content-root", str(tmp_path)])
    assert rc == 2
