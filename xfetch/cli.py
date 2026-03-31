from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .connectors.x import XConnector
from .pipeline.bundle import write_bundle
from .publishing.github_repo_sync import sync_bundle_to_repo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xfetch")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("url")
    ingest.add_argument("--content-root")
    ingest.add_argument("--json", action="store_true")

    sync = subparsers.add_parser("sync")
    sync.add_argument("bundle_dir")
    sync.add_argument("--target-repo", required=True)
    sync.add_argument("--target-subdir", default="content")
    sync.add_argument("--json", action="store_true")
    return parser


def pick_connector(url: str):
    connector = XConnector()
    if connector.can_handle(url):
        return connector
    return None


def run_ingest(args) -> int:
    config = load_config(content_root=args.content_root)
    connector = pick_connector(args.url)
    if connector is None:
        return 2

    doc = connector.fetch(args.url)
    bundle_dir = write_bundle(doc, config)
    if args.json:
        print(
            json.dumps(
                {
                    "ok": True,
                    "source_type": doc.source_type,
                    "external_id": doc.external_id,
                    "bundle_dir": str(bundle_dir),
                },
                ensure_ascii=False,
            )
        )
    else:
        print(bundle_dir)
    return 0


def run_sync(args) -> int:
    result = sync_bundle_to_repo(
        bundle_dir=Path(args.bundle_dir),
        target_repo=Path(args.target_repo),
        target_subdir=args.target_subdir,
    )
    if args.json:
        print(
            json.dumps(
                {
                    "ok": True,
                    "destination_dir": str(result.destination_dir),
                    "target_path": result.target_path,
                    "published": result.published,
                    "public_url": result.public_url,
                    "revision": result.revision,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(result.destination_dir)
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "ingest":
        return run_ingest(args)
    if args.command == "sync":
        return run_sync(args)
    return 0
