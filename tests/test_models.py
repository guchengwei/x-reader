import pytest

from xfetch.models import NormalizedDocument, derive_title, document_to_dict


def test_derive_title_uses_first_line_and_trims():
    assert derive_title("First line here\nSecond line", "123") == "First line here"


def test_derive_title_falls_back_to_external_id_when_text_empty():
    assert derive_title("   ", "123") == "X post 123"


def _doc(**overrides):
    values = dict(
        source_type="x", source_url="https://x.com/a/status/1", canonical_url="https://x.com/a/status/1",
        external_id="1", title="hello", author="alice", author_handle="alice", created_at=None,
        language=None, text="hello", markdown="# hello", summary=None,
    )
    values.update(overrides)
    return NormalizedDocument(**values)


def test_document_to_dict_preserves_capture_contract():
    data = document_to_dict(_doc())
    assert data["source_type"] == "x"
    assert data["external_id"] == "1"
    assert data["capture_status"] == "complete"
    assert data["content_kinds"] == ["text"]


def test_document_rejects_unknown_capture_status():
    with pytest.raises(ValueError, match="capture_status"):
        _doc(capture_status="maybe")
