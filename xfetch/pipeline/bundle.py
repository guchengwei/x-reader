from __future__ import annotations

from datetime import datetime, timezone
import json
import mimetypes
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlparse
from urllib.request import Request

from xfetch.config import RuntimeConfig
from xfetch.models import NormalizedDocument, document_to_dict
from xfetch.net import safe_urlopen
from xfetch.pipeline.card import VisualGenerator, enrich_card


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
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with safe_urlopen(req, timeout=timeout, max_bytes=20 * 1024 * 1024) as resp:
        return resp.read(), resp.headers.get("Content-Type")


def _materialize_assets(doc: NormalizedDocument, assets_dir: Path) -> None:
    updated_assets: list[dict] = []
    failures = 0
    for index, asset in enumerate(doc.assets, start=1):
        if not isinstance(asset, dict):
            continue
        url = str(asset.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            updated_assets.append(asset)
            continue
        try:
            payload, content_type = _download_asset(url)
        except Exception as exc:
            failed_asset = dict(asset)
            failed_asset["capture_error"] = str(exc)
            updated_assets.append(failed_asset)
            failures += 1
            continue

        prefix = "image" if asset.get("type") == "image" else "asset"
        extension = _infer_extension(url, content_type)
        filename = f"{prefix}-{index:02d}{extension}"
        local_path = f"assets/{filename}"
        (assets_dir / filename).write_bytes(payload)

        updated_asset = dict(asset)
        updated_asset["local_path"] = local_path
        if content_type:
            updated_asset["captured_content_type"] = content_type.split(";", 1)[0].strip().lower()
        updated_assets.append(updated_asset)
        if doc.markdown:
            doc.markdown = doc.markdown.replace(url, local_path)

    doc.assets = updated_assets
    if failures:
        doc.metadata["asset_capture_failures"] = failures
        if doc.capture_status == "complete":
            doc.capture_status = "partial"


def _replace_bundle(temp_dir: Path, bundle_dir: Path) -> None:
    backup_dir = bundle_dir.with_name(f".{bundle_dir.name}.old")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    if bundle_dir.exists():
        bundle_dir.replace(backup_dir)
    try:
        temp_dir.replace(bundle_dir)
    except Exception:
        if backup_dir.exists() and not bundle_dir.exists():
            backup_dir.replace(bundle_dir)
        raise
    finally:
        if backup_dir.exists():
            shutil.rmtree(backup_dir)


def _fallback_card(doc: NormalizedDocument, error: Exception) -> None:
    title = " ".join(str(doc.title or "").split()) or f"Saved {doc.source_type} bookmark {doc.external_id}"
    opening_source = doc.summary or doc.text or title
    opening = " ".join(str(opening_source).split())[:200].rstrip() or title
    original = str(doc.markdown or doc.text or "").lstrip()
    original = re.sub(r"^#\s+[^\n]+\n*", "", original, count=1)
    doc.card = {"title": title, "opening": opening, "visual_kind": "text"}
    doc.markdown = f"# {title}\n\n{opening}\n"
    if original:
        doc.markdown += f"\n## Captured content\n\n{original.rstrip()}\n"
    doc.metadata["card_enrichment"] = {
        "status": "partial",
        "error": f"{type(error).__name__}: {str(error)[:160]}",
    }


def write_bundle(
    doc: NormalizedDocument,
    config: RuntimeConfig,
    visual_generator: VisualGenerator | None = None,
) -> Path:
    month = bundle_month(doc.created_at, doc.lineage.get("fetched_at"))
    slug = build_slug(doc.source_type, doc.external_id, doc.author_handle)
    month_dir = config.content_root / month
    month_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir = month_dir / slug
    temp_dir = Path(tempfile.mkdtemp(prefix=f".{slug}.", dir=month_dir))
    assets_dir = temp_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    try:
        _materialize_assets(doc, assets_dir)
        try:
            enrich_card(doc, temp_dir, visual_generator=visual_generator)
        except Exception as exc:
            _fallback_card(doc, exc)

        (temp_dir / "document.json").write_text(
            json.dumps(document_to_dict(doc), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (temp_dir / "index.md").write_text(doc.markdown, encoding="utf-8")
        (temp_dir / "publish.json").write_text(
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
        _replace_bundle(temp_dir, bundle_dir)
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise

    return bundle_dir
