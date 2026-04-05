from __future__ import annotations

from datetime import datetime, timezone
import json
import mimetypes
from pathlib import Path
import re
from urllib.parse import urlparse
import urllib.request

from xfetch.config import RuntimeConfig
from xfetch.models import NormalizedDocument, document_to_dict


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9-]", "-", text.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def build_slug(source_type: str, external_id: str, author_handle: str | None) -> str:
    handle = slugify(author_handle or "") or "unknown"
    return slugify(f"{source_type}-{external_id}-{handle}")


def _parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def bundle_month(created_at: str | None, fetched_at: str | None = None) -> str:
    dt = _parse_iso8601(created_at) or _parse_iso8601(fetched_at)
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m")


def _infer_extension(url: str, content_type: str | None) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix:
        return suffix
    guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip()) or ""
    return guessed or ".bin"


def _download_asset(url: str, timeout: int = 20) -> tuple[bytes, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get("Content-Type")


def _materialize_assets(doc: NormalizedDocument, assets_dir: Path) -> None:
    updated_assets: list[dict] = []
    for index, asset in enumerate(doc.assets, start=1):
        if not isinstance(asset, dict):
            continue
        url = str(asset.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            updated_assets.append(asset)
            continue
        try:
            payload, content_type = _download_asset(url)
        except Exception:
            updated_assets.append(asset)
            continue

        prefix = "image" if asset.get("type") == "image" else "asset"
        extension = _infer_extension(url, content_type)
        filename = f"{prefix}-{index:02d}{extension}"
        local_path = f"assets/{filename}"
        (assets_dir / filename).write_bytes(payload)

        updated_asset = dict(asset)
        updated_asset["local_path"] = local_path
        updated_assets.append(updated_asset)
        if doc.markdown:
            doc.markdown = doc.markdown.replace(url, local_path)

    doc.assets = updated_assets


def write_bundle(doc: NormalizedDocument, config: RuntimeConfig) -> Path:
    month = bundle_month(doc.created_at)
    slug = build_slug(doc.source_type, doc.external_id, doc.author_handle)
    bundle_dir = config.content_root / month / slug
    assets_dir = bundle_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    _materialize_assets(doc, assets_dir)

    (bundle_dir / "document.json").write_text(
        json.dumps(document_to_dict(doc), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "index.md").write_text(doc.markdown, encoding="utf-8")
    (bundle_dir / "publish.json").write_text(
        json.dumps(
            {
                "published": False,
                "public_url": None,
                "target": None,
                "revision": None,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    return bundle_dir
