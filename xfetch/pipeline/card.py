from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from html import unescape
from pathlib import Path, PurePosixPath
import re
from typing import Literal, Protocol
from urllib.parse import urlparse

from xfetch.models import NormalizedDocument


_IMAGE_SUFFIXES = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
_GENERIC_TITLES = {
    "home",
    "homepage",
    "index",
    "untitled",
    "无标题",
    "無題",
}
_REJECTED_VISUAL_WORDS = {
    "avatar",
    "badge",
    "decorative",
    "emoji",
    "favicon",
    "icon",
    "logo",
    "pixel",
    "profile",
    "sprite",
    "tracker",
    "tracking",
}
_DIAGRAM_TERMS = {
    "architecture",
    "comparison",
    "components",
    "hierarchy",
    "pipeline",
    "process",
    "relationship",
    "stages",
    "versus",
    "workflow",
    "体系结构",
    "关系",
    "对比",
    "层级",
    "架构",
    "比较",
    "流程",
    "组件",
}


@dataclass(frozen=True, slots=True)
class VisualRequest:
    kind: Literal["diagram", "cover"]
    title: str
    opening: str
    source_type: str
    content: str
    width: int
    height: int
    instructions: str
    max_long_edge: int = 1600
    target_bytes: int = 350 * 1024


@dataclass(frozen=True, slots=True)
class GeneratedVisual:
    data: bytes
    media_type: str = "image/webp"


class VisualGenerator(Protocol):
    def generate(self, request: VisualRequest) -> GeneratedVisual | None: ...


def _plain_text(value: str) -> str:
    text = value or ""
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*(?:[-*+] |\d+[.)] ).*$", " ", text, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", unescape(text)).strip(" \t\r\n-–—|:")


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    shortened = value[: limit - 1].rstrip()
    if " " in shortened:
        candidate = shortened.rsplit(" ", 1)[0].rstrip(" ,;:，；：")
        if len(candidate) >= limit // 2:
            shortened = candidate
    return shortened.rstrip(" ,;:，；：") + "…"


def _generic_title(doc: NormalizedDocument, title: str) -> bool:
    normalized = title.casefold().strip(" \t\r\n-–—|:/")
    host = urlparse(doc.canonical_url or doc.source_url).netloc.casefold().removeprefix("www.")
    identities = {
        host,
        doc.author.casefold().strip(),
        doc.author_handle.casefold().lstrip("@").strip(),
        f"@{doc.author_handle.casefold().lstrip('@').strip()}",
    }
    if not normalized or normalized in _GENERIC_TITLES or normalized in identities:
        return True
    if normalized.startswith(("http://", "https://", "www.")):
        return True
    if re.fullmatch(r"(?:x|twitter|youtube|bilibili|web)(?: post| video| article)?(?: \w+)?", normalized):
        return True
    return False


def _sentences(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?。！？])\s*", value) if part.strip()]


def choose_title(doc: NormalizedDocument) -> str:
    canonical = _plain_text(doc.title)
    if canonical and not _generic_title(doc, canonical):
        return canonical

    content = _plain_text(doc.text or doc.markdown or doc.summary or "")
    for sentence in _sentences(content):
        if len(sentence) >= 8 and not _generic_title(doc, sentence):
            return _truncate(sentence, 80)
    if content:
        return _truncate(content, 80)
    return f"Saved {doc.source_type} bookmark {doc.external_id}".strip()


def choose_opening(doc: NormalizedDocument, title: str) -> str:
    candidates = [doc.summary or ""]
    description = doc.metadata.get("description")
    if isinstance(description, str):
        candidates.append(description)
    candidates.extend([doc.text, doc.markdown])

    title_key = re.sub(r"\W+", "", title).casefold()
    title_prefix_key = re.sub(r"\W+", "", title.rstrip("…")).casefold()
    fallback = ""
    for raw in candidates:
        text = _plain_text(raw)
        if not text:
            continue
        fallback = fallback or text
        useful = []
        for sentence in _sentences(text):
            sentence_key = re.sub(r"\W+", "", sentence).casefold()
            if sentence_key == title_key or (title.endswith("…") and sentence_key.startswith(title_prefix_key)):
                continue
            if re.match(r"^(?:this (?:article|post|page|video) (?:is about|discusses|explores)|本文(?:介绍|讨论))", sentence, re.I):
                continue
            useful.append(sentence)
            if len(" ".join(useful)) >= 60 or len(useful) == 2:
                break
        if useful:
            return _truncate(" ".join(useful), 200)
    return _truncate(fallback or title, 200)


def _safe_asset_path(bundle_dir: Path, value: object) -> Path | None:
    raw = str(value or "").strip().replace("\\", "/")
    relative = PurePosixPath(raw)
    if relative.is_absolute() or len(relative.parts) < 2 or relative.parts[0] != "assets" or ".." in relative.parts:
        return None
    candidate = bundle_dir.joinpath(*relative.parts)
    try:
        candidate.resolve().relative_to(bundle_dir.resolve())
    except ValueError:
        return None
    if not candidate.is_file() or candidate.suffix.casefold() not in _IMAGE_SUFFIXES:
        return None
    return candidate


def _image_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:65536]
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data[:3] == b"GIF" and len(data) >= 10:
        return int.from_bytes(data[6:8], "little"), int.from_bytes(data[8:10], "little")
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP" and len(data) >= 30:
        chunk = data[12:16]
        if chunk == b"VP8X":
            return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
    if data.startswith(b"\xff\xd8"):
        offset = 2
        while offset + 9 < len(data):
            if data[offset] != 0xFF:
                offset += 1
                continue
            marker = data[offset + 1]
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                return int.from_bytes(data[offset + 7 : offset + 9], "big"), int.from_bytes(data[offset + 5 : offset + 7], "big")
            if marker in {0xD8, 0xD9}:
                offset += 2
                continue
            length = int.from_bytes(data[offset + 2 : offset + 4], "big")
            if length < 2:
                break
            offset += 2 + length
    return None


def _asset_dimensions(asset: dict, path: Path) -> tuple[int, int] | None:
    try:
        width = int(asset.get("width") or 0)
        height = int(asset.get("height") or 0)
    except (TypeError, ValueError):
        width = height = 0
    return (width, height) if width and height else _image_dimensions(path)


def _source_visual_score(doc: NormalizedDocument, asset: dict, path: Path) -> int | None:
    words = " ".join(
        str(asset.get(key) or "")
        for key in ("source", "role", "kind", "alt", "name", "url")
    ).casefold()
    tokens = set(re.findall(r"[a-z]+", words))
    if tokens & _REJECTED_VISUAL_WORDS:
        return None
    captured_content_type = str(asset.get("captured_content_type") or "")
    if captured_content_type and not captured_content_type.startswith("image/"):
        return None
    if path.stat().st_size < 1024:
        return None

    dimensions = _asset_dimensions(asset, path)
    if dimensions:
        width, height = dimensions
        ratio = width / height
        if width < 400 or height < 200 or not 0.45 <= ratio <= 4.2:
            return None

    source = str(asset.get("source") or "").casefold()
    if doc.source_type in {"youtube", "bilibili"}:
        return 120
    if doc.source_type == "x" and source in {"tweet_media", "article_inline"}:
        return 115 if source == "tweet_media" else 105
    priorities = {"article_inline": 95, "article_image": 90, "open_graph": 85, "og_image": 85}
    return priorities.get(source, 50)


def select_source_visual(doc: NormalizedDocument, bundle_dir: Path) -> str | None:
    ranked: list[tuple[int, int, str]] = []
    seen_payloads: set[str] = set()
    for index, asset in enumerate(doc.assets):
        if not isinstance(asset, dict) or asset.get("type") != "image":
            continue
        path = _safe_asset_path(bundle_dir, asset.get("local_path"))
        if path is None:
            continue
        digest = sha256(path.read_bytes()).hexdigest()
        if digest in seen_payloads:
            continue
        seen_payloads.add(digest)
        score = _source_visual_score(doc, asset, path)
        if score is not None:
            ranked.append((score, -index, path.relative_to(bundle_dir).as_posix()))
    return max(ranked)[2] if ranked else None


def _diagram_worthy(doc: NormalizedDocument) -> bool:
    content = _plain_text(f"{doc.title}\n{doc.summary or ''}\n{doc.text}").casefold()
    term_hits = sum(term in content for term in _DIAGRAM_TERMS)
    enumerated = len(re.findall(r"(?:^|\s)(?:\d+[.)]|[-*])\s+", doc.markdown, re.MULTILINE)) >= 3
    return len(content) >= 80 and (term_hits >= 1 or enumerated)


def _generated_extension(media_type: str) -> str:
    return {
        "image/avif": ".avif",
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }.get(media_type.casefold(), "")


def _generate_visual(
    doc: NormalizedDocument,
    bundle_dir: Path,
    title: str,
    opening: str,
    generator: VisualGenerator,
) -> tuple[str, str] | None:
    kind: Literal["diagram", "cover"] = "diagram" if _diagram_worthy(doc) else "cover"
    width, height = (1200, 800) if kind == "diagram" else (1200, 675)
    request = VisualRequest(
        kind=kind,
        title=title,
        opening=opening,
        source_type=doc.source_type,
        content=_truncate(_plain_text(doc.text or doc.markdown), 6000),
        width=width,
        height=height,
        instructions=(
            "Create a faithful explanatory diagram using only relationships present in the captured content; "
            "labels are allowed, but do not add claims, logos, fake UI, or watermarks."
            if kind == "diagram"
            else "Create a text-free editorial cover; do not add a title, decorative text, logos, fake UI, or watermarks."
        ),
    )
    result = generator.generate(request)
    if result is None:
        return None
    extension = _generated_extension(result.media_type)
    if not extension or not result.data or len(result.data) > 2 * 1024 * 1024:
        raise ValueError("visual generator returned an unsupported or oversized image")
    filename = f"card-{kind}{extension}"
    path = bundle_dir / "assets" / filename
    path.write_bytes(result.data)
    dimensions = _image_dimensions(path)
    if dimensions and max(dimensions) > request.max_long_edge:
        path.unlink()
        raise ValueError("visual generator returned an image larger than 1600 px")
    return path.relative_to(bundle_dir).as_posix(), kind


def normalize_detail_markdown(markdown: str, title: str, opening: str) -> str:
    lines = (markdown or "").lstrip("\ufeff\n").splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and re.match(r"^#\s+", lines[0]):
        lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)

    normalized_body = []
    for line in lines:
        normalized_body.append("#" + line if line.startswith("# ") else line)
    lines = normalized_body

    output = [f"# {title}", "", opening]
    if not lines:
        return "\n".join(output).rstrip() + "\n"

    output.extend([""])
    if lines[0].lstrip().startswith(("- ", "* ")):
        output.extend(["## Source details", ""])
        list_end = 0
        while list_end < len(lines) and (not lines[list_end].strip() or lines[list_end].lstrip().startswith(("- ", "* "))):
            output.append(lines[list_end])
            list_end += 1
        remainder = lines[list_end:]
        while remainder and not remainder[0].strip():
            remainder.pop(0)
        if remainder:
            if not remainder[0].startswith("## "):
                output.extend(["", "## Captured content", ""])
            output.extend(remainder)
    else:
        if not lines[0].startswith("## "):
            output.extend(["## Captured content", ""])
        output.extend(lines)
    return "\n".join(output).rstrip() + "\n"


def enrich_card(
    doc: NormalizedDocument,
    bundle_dir: Path,
    visual_generator: VisualGenerator | None = None,
) -> None:
    title = choose_title(doc)
    opening = choose_opening(doc, title)
    card: dict[str, str] = {"title": title, "opening": opening}

    source_visual = select_source_visual(doc, bundle_dir)
    if source_visual:
        card.update(image=source_visual, visual_kind="source_image")
    elif visual_generator is not None:
        try:
            generated = _generate_visual(doc, bundle_dir, title, opening, visual_generator)
            if generated:
                path, kind = generated
                field = "diagram" if kind == "diagram" else "image"
                card.update({field: path, "visual_kind": f"generated_{kind}"})
            else:
                card["visual_kind"] = "text"
        except Exception as exc:
            card["visual_kind"] = "text"
            doc.metadata["card_enrichment"] = {
                "status": "partial",
                "visual_error": f"{type(exc).__name__}: {str(exc)[:160]}",
            }
    else:
        card["visual_kind"] = "text"

    doc.title = title
    doc.card = card
    doc.markdown = normalize_detail_markdown(doc.markdown or doc.text, title, opening)
