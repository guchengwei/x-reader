from __future__ import annotations

import json
import re
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from xfetch.connectors.base import BaseConnector
from xfetch.models import NormalizedDocument


_BILIBILI_URL_RE = re.compile(r"^https?://(?:www\.)?(?:bilibili\.com|b23\.tv)/", re.IGNORECASE)
_BV_RE = re.compile(r"(BV[0-9A-Za-z]+)")
_API_URL = "https://api.bilibili.com/x/web-interface/view"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "unknown"


def _extract_bvid(url: str) -> str | None:
    match = _BV_RE.search(url)
    if match:
        return match.group(1)
    return None


def _fetch_api_payload(bvid: str) -> tuple[dict, str]:
    query_url = f"{_API_URL}?{urlencode({'bvid': bvid})}"
    request = Request(query_url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
        content_type = response.headers.get("Content-Type", "application/json")
    return payload, content_type


class BilibiliConnector(BaseConnector):
    def can_handle(self, url: str) -> bool:
        return bool(_BILIBILI_URL_RE.match(url))

    def fetch(self, url: str) -> NormalizedDocument:
        bvid = _extract_bvid(url)
        if not bvid:
            parsed = urlparse(url)
            bvid = parsed.path.strip("/") or None
        if not bvid:
            raise ValueError(f"Cannot extract Bilibili BV ID from {url}")

        payload, content_type = _fetch_api_payload(bvid)
        if payload.get("code") != 0:
            raise ValueError(f"Bilibili API error: {payload.get('message')}")
        data = payload.get("data", {})
        title = data.get("title") or f"Bilibili video {bvid}"
        description = data.get("desc") or title
        author = data.get("owner", {}).get("name") or "unknown"
        cover = data.get("pic")
        canonical_url = f"https://www.bilibili.com/video/{bvid}"
        assets = [{"url": cover, "type": "image"}] if cover else []
        markdown = f"# {title}\n\n- Source: {canonical_url}\n- Author: {author}\n\n{description}\n"

        return NormalizedDocument(
            source_type="bilibili",
            source_url=url,
            canonical_url=canonical_url,
            external_id=bvid,
            title=title,
            author=author,
            author_handle=_slugify(author),
            created_at=None,
            language="zh",
            text=description,
            markdown=markdown,
            summary=None,
            assets=assets,
            metadata={
                "platform": "bilibili",
                "content_type": content_type,
                "duration": data.get("duration", 0),
                "view_count": data.get("stat", {}).get("view", 0),
            },
            lineage={
                "connector": "bilibili",
                "runtime_version": "0.1.0",
            },
        )
