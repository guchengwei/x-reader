from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1
from html import unescape
from html.parser import HTMLParser
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from xfetch.connectors.base import BaseConnector
from xfetch.models import NormalizedDocument
from xfetch.connectors.x import is_x_url


def _is_feed_url(url: str) -> bool:
    lowered = url.lower()
    return lowered.endswith(".xml") or "/feed" in lowered or "/rss" in lowered or "/atom" in lowered


class _HTMLDocumentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.author = None
        self._in_title = False
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = {key.lower(): value for key, value in attrs}
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag.lower() == "meta":
            name = (attrs_dict.get("name") or attrs_dict.get("property") or "").lower()
            if name in {"author", "article:author"} and attrs_dict.get("content"):
                self.author = attrs_dict["content"].strip()

    def handle_endtag(self, tag):
        lowered = tag.lower()
        if lowered == "title":
            self._in_title = False
        if lowered in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if lowered in {"p", "div", "section", "article", "main", "br", "li", "h1", "h2", "h3", "h4"}:
            self._chunks.append("\n")

    def handle_data(self, data):
        text = unescape(data)
        if self._in_title:
            self.title += text
        if self._skip_depth:
            return
        collapsed = " ".join(text.split())
        if collapsed:
            self._chunks.append(collapsed)

    def text_content(self) -> str:
        text = " ".join(self._chunks)
        text = re.sub(r"\s*\n\s*", "\n", text)
        text = re.sub(r"\n{2,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()


def _fetch_url(url: str) -> tuple[str, str, str]:
    request = Request(url, headers={"User-Agent": "xfetch/0.1.0"})
    with urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8", errors="replace")
        final_url = response.geturl()
        content_type = response.headers.get("Content-Type", "application/octet-stream")
    return body, final_url, content_type


def _domain_handle(url: str) -> str:
    return urlparse(url).netloc.lower() or "unknown"


class WebConnector(BaseConnector):
    def can_handle(self, url: str) -> bool:
        if not url.lower().startswith(("http://", "https://")):
            return False
        if is_x_url(url) or _is_feed_url(url):
            return False
        return True

    def fetch(self, url: str) -> NormalizedDocument:
        html, canonical_url, content_type = _fetch_url(url)
        parser = _HTMLDocumentParser()
        parser.feed(html)
        parser.close()

        title = " ".join(parser.title.split()) or urlparse(canonical_url).path.strip("/") or canonical_url
        author_handle = _domain_handle(canonical_url)
        author = parser.author or author_handle
        text = parser.text_content() or title
        external_id = sha1(canonical_url.encode("utf-8")).hexdigest()[:12]
        fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        markdown = f"# {title}\n\n- Source: {canonical_url}\n- Author: {author}\n\n{text}\n"

        return NormalizedDocument(
            source_type="web",
            source_url=url,
            canonical_url=canonical_url,
            external_id=external_id,
            title=title,
            author=author,
            author_handle=author_handle,
            created_at=None,
            language=None,
            text=text,
            markdown=markdown,
            summary=None,
            metadata={
                "platform": "web",
                "content_type": content_type,
            },
            lineage={
                "fetched_at": fetched_at,
                "connector": "web",
                "runtime_version": "0.1.0",
            },
        )
