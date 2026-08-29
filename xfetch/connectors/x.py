from __future__ import annotations

from datetime import datetime, timezone
import re

from xfetch.backends.fxtwitter import fetch_fxtwitter_json, fetch_oembed_json, parse_fxtwitter_payload, parse_oembed_payload
from xfetch.connectors.base import BaseConnector
from xfetch.models import NormalizedDocument, derive_title, render_markdown


_X_URL_RE = re.compile(r"^https?://(?:www\.)?(?:x\.com|twitter\.com)/[^/]+/status/\d+", re.IGNORECASE)


def is_x_url(url: str) -> bool:
    return bool(_X_URL_RE.match(url))


class XConnector(BaseConnector):
    def can_handle(self, url: str) -> bool:
        return is_x_url(url)

    def fetch(self, url: str) -> NormalizedDocument:
        try:
            raw = parse_fxtwitter_payload(fetch_fxtwitter_json(url))
            return self._normalize_raw(url, raw, backend="fxtwitter", capture_status="complete")
        except Exception as primary_error:
            raw = parse_oembed_payload(fetch_oembed_json(url), source_url=url)
            doc = self._normalize_raw(url, raw, backend="oembed", capture_status="partial")
            doc.metadata["fallback_from"] = "fxtwitter"
            doc.metadata["fallback_error"] = type(primary_error).__name__
            return doc

    def normalize_payload(self, source_url: str, payload: dict) -> NormalizedDocument:
        return self._normalize_raw(source_url, parse_fxtwitter_payload(payload), backend="fxtwitter", capture_status="complete")

    def _normalize_raw(self, source_url: str, raw: dict, backend: str, capture_status: str) -> NormalizedDocument:
        text = raw["text"]
        doc = NormalizedDocument(
            source_type="x",
            source_url=source_url,
            canonical_url=raw["canonical_url"] or source_url,
            external_id=raw["tweet_id"],
            title=derive_title(text, raw["tweet_id"]),
            author=raw["display_name"] or raw["screen_name"] or "unknown",
            author_handle=raw["screen_name"] or "unknown",
            created_at=raw["created_at"],
            language=raw["language"],
            text=text,
            markdown="",
            summary=None,
            assets=raw.get("assets", []),
            metadata={"platform": "x", "tweet_id": raw["tweet_id"], "screen_name": raw["screen_name"], "display_name": raw["display_name"], "stats": raw["stats"], "raw_source": backend},
            lineage={"fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "connector": "x", "backend": backend, "runtime_version": "0.2.0"},
            capture_status=capture_status,
            content_kinds=["text", "images"] if raw.get("assets") else ["text"],
        )
        doc.markdown = render_markdown(doc, body=raw.get("markdown") or text)
        return doc
