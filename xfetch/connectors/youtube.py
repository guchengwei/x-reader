from __future__ import annotations

from html import unescape
import re
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from xfetch.connectors.base import BaseConnector
from xfetch.models import NormalizedDocument


_YOUTUBE_HOST_RE = re.compile(r"(?:^|\.)(?:youtube\.com|youtu\.be)$", re.IGNORECASE)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "unknown"


def _extract_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "youtu.be" in host:
        value = parsed.path.strip("/")
        return value or None
    qs = parse_qs(parsed.query)
    if qs.get("v"):
        return qs["v"][0]
    match = re.search(r"/embed/([^/?#]+)", parsed.path)
    if match:
        return match.group(1)
    return None


def _fetch_html(url: str) -> tuple[str, str, str]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=15) as response:
        html = response.read().decode("utf-8", errors="replace")
        final_url = response.geturl()
        content_type = response.headers.get("Content-Type", "application/octet-stream")
    return html, final_url, content_type


def _extract_meta(html: str, attr_name: str, attr_value: str) -> str | None:
    pattern = rf'<meta\s+(?:name|property)=["\']{re.escape(attr_value)}["\']\s+content=["\']([^"\']*)["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    if not match:
        return None
    return unescape(match.group(1).strip())


class YouTubeConnector(BaseConnector):
    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        return bool(parsed.scheme in {"http", "https"} and _YOUTUBE_HOST_RE.search(parsed.netloc))

    def fetch(self, url: str) -> NormalizedDocument:
        html, canonical_url, content_type = _fetch_html(url)
        video_id = _extract_video_id(canonical_url) or _extract_video_id(url) or "youtube"
        title = _extract_meta(html, "property", "og:title") or f"YouTube video {video_id}"
        author = _extract_meta(html, "name", "author") or "unknown"
        description = _extract_meta(html, "property", "og:description") or title
        image = _extract_meta(html, "property", "og:image")
        author_handle = _slugify(author)
        assets = [{"url": image, "type": "image"}] if image else []
        markdown = f"# {title}\n\n- Source: {canonical_url}\n- Author: {author}\n\n{description}\n"

        return NormalizedDocument(
            source_type="youtube",
            source_url=url,
            canonical_url=canonical_url,
            external_id=video_id,
            title=title,
            author=author,
            author_handle=author_handle,
            created_at=None,
            language=None,
            text=description,
            markdown=markdown,
            summary=None,
            assets=assets,
            metadata={
                "platform": "youtube",
                "content_type": content_type,
                "has_transcript": False,
            },
            lineage={
                "connector": "youtube",
                "runtime_version": "0.1.0",
            },
        )
