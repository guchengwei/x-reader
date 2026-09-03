import json

from xfetch.config import RuntimeConfig
from xfetch.models import NormalizedDocument
from xfetch.pipeline import bundle as bundle_module
from xfetch.pipeline.bundle import write_bundle
from xfetch.pipeline.card import GeneratedVisual


def _doc(**overrides):
    values = dict(
        source_type="web",
        source_url="https://example.com/article",
        canonical_url="https://example.com/article",
        external_id="article-1",
        title="A specific source title",
        author="Alice",
        author_handle="alice",
        created_at="2026-09-03T00:00:00Z",
        language="en",
        text=(
            "The capture pipeline turns fetched pages into portable bookmark bundles. "
            "It keeps the original content available for a durable detail page."
        ),
        markdown=(
            "# A specific source title\n\n"
            "- Source: https://example.com/article\n"
            "- Author: Alice\n\n"
            "The capture pipeline turns fetched pages into portable bookmark bundles.\n"
        ),
        summary=None,
    )
    values.update(overrides)
    return NormalizedDocument(**values)


def _config(tmp_path):
    return RuntimeConfig(content_root=tmp_path / "content", site_root=tmp_path / "site")


def _read_document(bundle_dir):
    return json.loads((bundle_dir / "document.json").read_text(encoding="utf-8"))


class _NeverGenerate:
    def generate(self, request):
        raise AssertionError("source visuals must be preferred")


def test_reuses_suitable_source_image_without_generation(tmp_path, monkeypatch):
    monkeypatch.setattr(
        bundle_module,
        "_download_asset",
        lambda url, timeout=20: (b"source-image" * 200, "image/jpeg"),
    )
    doc = _doc(
        assets=[
            {
                "url": "https://example.com/hero.jpg",
                "type": "image",
                "source": "article_image",
                "width": 1200,
                "height": 675,
            }
        ]
    )

    bundle_dir = write_bundle(doc, _config(tmp_path), visual_generator=_NeverGenerate())
    card = _read_document(bundle_dir)["card"]

    assert card["image"] == "assets/image-01.jpg"
    assert card["visual_kind"] == "source_image"
    assert (bundle_dir / card["image"]).is_file()
    assert "diagram" not in card


def test_video_source_selects_downloaded_thumbnail(tmp_path, monkeypatch):
    monkeypatch.setattr(
        bundle_module,
        "_download_asset",
        lambda url, timeout=20: (b"video-thumbnail" * 200, "image/jpeg"),
    )
    doc = _doc(
        source_type="youtube",
        source_url="https://www.youtube.com/watch?v=abc",
        canonical_url="https://www.youtube.com/watch?v=abc",
        external_id="abc",
        assets=[{"url": "https://i.ytimg.com/vi/abc/maxresdefault.jpg", "type": "image"}],
    )

    bundle_dir = write_bundle(doc, _config(tmp_path))
    card = _read_document(bundle_dir)["card"]

    assert card == {
        "title": "A specific source title",
        "opening": "The capture pipeline turns fetched pages into portable bookmark bundles.",
        "image": "assets/image-01.jpg",
        "visual_kind": "source_image",
    }


class _RecordingGenerator:
    def __init__(self, error=None):
        self.error = error
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return GeneratedVisual(b"generated-webp", "image/webp")


def test_conceptual_article_can_generate_diagram_without_live_api(tmp_path):
    generator = _RecordingGenerator()
    doc = _doc(
        text=(
            "The architecture has a fetcher, a normalizer, and a bundle writer. "
            "The pipeline sends normalized content through these components before publication."
        )
    )

    bundle_dir = write_bundle(doc, _config(tmp_path), visual_generator=generator)
    card = _read_document(bundle_dir)["card"]

    assert len(generator.requests) == 1
    assert generator.requests[0].kind == "diagram"
    assert generator.requests[0].width == 1200
    assert generator.requests[0].height == 800
    assert card["diagram"] == "assets/card-diagram.webp"
    assert card["visual_kind"] == "generated_diagram"
    assert (bundle_dir / card["diagram"]).read_bytes() == b"generated-webp"


def test_non_structural_content_requests_text_free_cover(tmp_path):
    generator = _RecordingGenerator()
    doc = _doc(text="A personal account of walking through Kyoto during a quiet autumn morning.")

    document = _read_document(write_bundle(doc, _config(tmp_path), visual_generator=generator))

    assert generator.requests[0].kind == "cover"
    assert "text-free" in generator.requests[0].instructions
    assert document["card"]["image"] == "assets/card-cover.webp"
    assert document["card"]["visual_kind"] == "generated_cover"


def test_generation_failure_keeps_valid_text_card_and_capture_status(tmp_path):
    generator = _RecordingGenerator(RuntimeError("provider unavailable"))
    bundle_dir = write_bundle(_doc(), _config(tmp_path), visual_generator=generator)
    document = _read_document(bundle_dir)

    assert document["capture_status"] == "complete"
    assert document["card"]["title"]
    assert document["card"]["opening"]
    assert document["card"]["visual_kind"] == "text"
    assert "image" not in document["card"]
    assert "diagram" not in document["card"]
    assert document["metadata"]["card_enrichment"]["status"] == "partial"
    assert "RuntimeError" in document["metadata"]["card_enrichment"]["visual_error"]


def test_unexpected_enrichment_failure_does_not_abort_bundle(tmp_path, monkeypatch):
    def fail_enrichment(*args, **kwargs):
        raise RuntimeError("unexpected enrichment bug")

    monkeypatch.setattr(bundle_module, "enrich_card", fail_enrichment)
    document = _read_document(write_bundle(_doc(), _config(tmp_path)))

    assert document["capture_status"] == "complete"
    assert document["card"]["title"] == "A specific source title"
    assert document["card"]["opening"]
    assert document["card"]["visual_kind"] == "text"
    assert document["metadata"]["card_enrichment"]["status"] == "partial"


def test_generic_x_author_title_is_replaced_from_post_content(tmp_path):
    doc = _doc(
        source_type="x",
        source_url="https://x.com/alice/status/123",
        canonical_url="https://x.com/alice/status/123",
        external_id="123",
        title="@alice",
        text=(
            "Portable bookmark bundles should retain their source assets and normalized introduction. "
            "Publishing remains independent from optional visual enrichment."
        ),
    )

    document = _read_document(write_bundle(doc, _config(tmp_path)))

    assert document["card"]["title"] == "Portable bookmark bundles should retain their source assets and normalized…"
    assert document["card"]["opening"] == "Publishing remains independent from optional visual enrichment."
    assert document["title"] == document["card"]["title"]


def test_malicious_or_missing_local_asset_path_falls_back_safely(tmp_path):
    doc = _doc(
        assets=[
            {"type": "image", "local_path": "assets/../../secret.png", "width": 1200, "height": 675},
            {"type": "image", "local_path": "assets/missing.png", "width": 1200, "height": 675},
        ]
    )

    document = _read_document(write_bundle(doc, _config(tmp_path)))

    assert document["card"]["visual_kind"] == "text"
    assert "image" not in document["card"]
    assert "diagram" not in document["card"]


def test_logo_and_tiny_source_images_are_not_used_as_card_visuals(tmp_path, monkeypatch):
    def fake_download(url, timeout=20):
        size = 200 if "tiny" in url else 2000
        return b"image" * size, "image/png"

    monkeypatch.setattr(bundle_module, "_download_asset", fake_download)
    generator = _RecordingGenerator()
    doc = _doc(
        assets=[
            {
                "url": "https://example.com/company-logo.png",
                "type": "image",
                "source": "open_graph",
                "width": 1200,
                "height": 675,
            },
            {
                "url": "https://example.com/tiny.png",
                "type": "image",
                "source": "article_image",
                "width": 120,
                "height": 120,
            },
        ]
    )

    document = _read_document(write_bundle(doc, _config(tmp_path), visual_generator=generator))

    assert len(generator.requests) == 1
    assert document["card"]["visual_kind"].startswith("generated_")


def test_index_markdown_starts_with_card_h1_opening_and_section(tmp_path):
    bundle_dir = write_bundle(_doc(), _config(tmp_path))
    document = _read_document(bundle_dir)
    markdown = (bundle_dir / "index.md").read_text(encoding="utf-8")

    expected_prefix = f"# {document['card']['title']}\n\n{document['card']['opening']}\n\n## Source details\n"
    assert markdown.startswith(expected_prefix)
    assert document["markdown"] == markdown
    assert "## Captured content" in markdown
