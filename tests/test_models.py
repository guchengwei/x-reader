from xfetch.models import NormalizedDocument, derive_title, document_to_dict


def test_derive_title_uses_first_line_and_trims():
    text = "First line here\nSecond line"
    assert derive_title(text, "123") == "First line here"



def test_derive_title_falls_back_to_external_id_when_text_empty():
    assert derive_title("   ", "123") == "X post 123"



def test_document_to_dict_preserves_required_fields():
    doc = NormalizedDocument(
        source_type="x",
        source_url="https://x.com/a/status/1",
        canonical_url="https://x.com/a/status/1",
        external_id="1",
        title="hello",
        author="alice",
        author_handle="alice",
        created_at=None,
        language=None,
        text="hello",
        markdown="# hello",
        summary=None,
    )
    data = document_to_dict(doc)
    assert data["source_type"] == "x"
    assert data["external_id"] == "1"
