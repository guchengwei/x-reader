from __future__ import annotations

import argparse
import json

from .config import load_config
from .connectors.x import XConnector
from .pipeline.bundle import write_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xfetch")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("url")
    ingest.add_argument("--content-root")
    ingest.add_argument("--json", action="store_true")
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


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "ingest":
        return run_ingest(args)
    return 0
