from dataclasses import asdict, dataclass, field
from typing import Any


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
    tags: list[str] = field(default_factory=list)
    assets: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    lineage: dict[str, Any] = field(default_factory=dict)


def derive_title(text: str, external_id: str) -> str:
    for line in text.splitlines():
        collapsed = " ".join(line.split())
        if collapsed:
            return collapsed[:80]
    return f"X post {external_id}"


def render_markdown(doc: NormalizedDocument) -> str:
    created = doc.created_at or "unknown"
    return (
        f"# {doc.title}\n\n"
        f"- Source: {doc.canonical_url}\n"
        f"- Author: @{doc.author_handle}\n"
        f"- Created: {created}\n\n"
        f"{doc.text}\n"
    )


def document_to_dict(doc: NormalizedDocument) -> dict[str, Any]:
    return asdict(doc)
