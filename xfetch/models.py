from dataclasses import asdict, dataclass, field
from typing import Any


_CAPTURE_STATUSES = {"complete", "partial", "metadata_only", "failed"}


@dataclass(slots=True)
class NormalizedDocument:
    source_type: str
    source_url: str
    canonical_url: str
    external_id: str
    title: str
    author: str
    author_handle: str
    created_at: str | None
    language: str | None
    text: str
    markdown: str
    summary: str | None
    card: dict[str, Any] | None = None
    tags: list[str] = field(default_factory=list)
    assets: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    lineage: dict[str, Any] = field(default_factory=dict)
    capture_status: str = "complete"
    content_kinds: list[str] = field(default_factory=lambda: ["text"])

    def __post_init__(self) -> None:
        if self.capture_status not in _CAPTURE_STATUSES:
            raise ValueError(f"invalid capture_status: {self.capture_status}")


def derive_title(text: str, external_id: str) -> str:
    for line in text.splitlines():
        collapsed = " ".join(line.split())
        if collapsed:
            return collapsed[:80]
    return f"X post {external_id}"


def render_markdown(doc: NormalizedDocument, body: str | None = None) -> str:
    created = doc.created_at or "unknown"
    body_source = body if body is not None else doc.text
    return (
        f"# {doc.title}\n\n"
        f"- Source: {doc.canonical_url}\n"
        f"- Author: @{doc.author_handle}\n"
        f"- Created: {created}\n\n"
        f"{body_source}\n"
    )


def document_to_dict(doc: NormalizedDocument) -> dict[str, Any]:
    return asdict(doc)
