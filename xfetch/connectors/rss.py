from __future__ import annotations

from datetime import timezone
from email.utils import parsedate_to_datetime
from hashlib import sha1
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from xfetch.connectors.base import BaseConnector
from xfetch.models import NormalizedDocument


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1].lower()


def _first_child_text(node: ET.Element, *names: str) -> str | None:
    wanted = {name.lower() for name in names}
    for child in list(node):
        if _local_name(child.tag) in wanted:
            text = "".join(child.itertext()).strip()
            if text:
                return text
    return None


def _find_entries(root: ET.Element) -> tuple[str | None, list[ET.Element]]:
    if _local_name(root.tag) == "rss":
        channel = next((child for child in list(root) if _local_name(child.tag) == "channel"), None)
        if channel is None:
            return None, []
        feed_title = _first_child_text(channel, "title")
        items = [child for child in list(channel) if _local_name(child.tag) == "item"]
        return feed_title, items
    if _local_name(root.tag) == "feed":
        feed_title = _first_child_text(root, "title")
        items = [child for child in list(root) if _local_name(child.tag) == "entry"]
        return feed_title, items
    return None, []


def _extract_link(entry: ET.Element) -> str | None:
    for child in list(entry):
        if _local_name(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        if href:
            return href.strip()
        text = "".join(child.itertext()).strip()
        if text:
            return text
    return None


def _normalize_created_at(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        dt = parsedate_to_datetime(text)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        if text.endswith("Z") and re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", text):
            return text
    return None


def _fetch_feed(url: str) -> tuple[ET.Element, str, str]:
    request = Request(url, headers={"User-Agent": "xfetch/0.1.0"})
    with urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8", errors="replace")
        final_url = response.geturl()
        content_type = response.headers.get("Content-Type", "application/octet-stream")
    return ET.fromstring(body), final_url, content_type


class RSSConnector(BaseConnector):
    def can_handle(self, url: str) -> bool:
        lowered = url.lower()
        if not lowered.startswith(("http://", "https://")):
            return False
        return lowered.endswith(".xml") or "/feed" in lowered or "/rss" in lowered or "/atom" in lowered

    def fetch(self, url: str) -> NormalizedDocument:
        root, source_url, content_type = _fetch_feed(url)
        feed_title, entries = _find_entries(root)
        if not entries:
            raise ValueError(f"No RSS/Atom entries found for {url}")

        entry = entries[0]
        title = _first_child_text(entry, "title") or "Untitled feed entry"
        canonical_url = _extract_link(entry) or source_url
        guid = _first_child_text(entry, "guid", "id")
        external_id = guid or sha1(canonical_url.encode("utf-8")).hexdigest()[:12]
        raw_author = _first_child_text(entry, "author", "creator", "name")
        author = raw_author.split("(")[-1].rstrip(")").strip() if raw_author and "(" in raw_author else (raw_author or (feed_title or urlparse(canonical_url).netloc.lower() or "unknown"))
        author_handle = urlparse(canonical_url).netloc.lower() or "unknown"
        text = _first_child_text(entry, "description", "summary", "content") or title
        created_at = _normalize_created_at(_first_child_text(entry, "pubdate", "published", "updated"))
        markdown = f"# {title}\n\n- Source: {canonical_url}\n- Feed: {feed_title or source_url}\n- Author: {author}\n\n{text}\n"

        return NormalizedDocument(
            source_type="rss",
            source_url=source_url,
            canonical_url=canonical_url,
            external_id=external_id,
            title=title,
            author=author,
            author_handle=author_handle,
            created_at=created_at,
            language=None,
            text=text,
            markdown=markdown,
            summary=None,
            metadata={
                "platform": "rss",
                "feed_title": feed_title,
                "content_type": content_type,
            },
            lineage={
                "connector": "rss",
                "runtime_version": "0.1.0",
            },
        )
