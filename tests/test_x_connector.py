from pathlib import Path
import json

from xfetch.backends.fxtwitter import parse_fxtwitter_payload
from xfetch.connectors.x import XConnector


def test_parse_fxtwitter_payload_extracts_minimum_fields():
    payload = json.loads(Path("tests/fixtures/fxtwitter_single_tweet.json").read_text())
    raw = parse_fxtwitter_payload(payload)
    assert raw["tweet_id"]
    assert raw["screen_name"]
    assert raw["text"]
    assert raw["markdown"]


def test_x_connector_normalizes_fixture_payload():
    payload = json.loads(Path("tests/fixtures/fxtwitter_single_tweet.json").read_text())
    doc = XConnector().normalize_payload(source_url="https://x.com/alice/status/123", payload=payload)
    assert doc.source_type == "x"
    assert doc.external_id == "123"
    assert doc.author_handle == "alice"
    assert doc.metadata["platform"] == "x"
    assert doc.lineage["backend"] == "fxtwitter"
    assert doc.capture_status == "complete"
    assert "# hello from fixture" in doc.markdown.lower()


def test_x_connector_uses_partial_oembed_fallback(monkeypatch):
    monkeypatch.setattr("xfetch.connectors.x.fetch_fxtwitter_json", lambda url: (_ for _ in ()).throw(RuntimeError("down")))
    monkeypatch.setattr(
        "xfetch.connectors.x.fetch_oembed_json",
        lambda url: {"author_name": "Alice", "html": "<blockquote><p>Hello from fallback with enough real content to be useful.</p></blockquote>"},
    )
    doc = XConnector().fetch("https://x.com/alice/status/123")
    assert doc.capture_status == "partial"
    assert doc.lineage["backend"] == "oembed"
    assert doc.metadata["fallback_from"] == "fxtwitter"
