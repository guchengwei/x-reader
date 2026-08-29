---
name: xfetch
description: >
  Preserve a supported public URL as a portable local bundle and optionally publish it
  into a separate content repository. Use for save/archive/preserve-link requests.
---

# xfetch

Use xfetch when the user wants to save or preserve the content behind a URL. xfetch is not a search tool, timeline reader, bookmark manager, or general-purpose browser.

## Canonical command

```bash
python -m xfetch save "<url>" --json
```

When publish defaults are configured, `save` performs ingest + bundle creation + publication and returns the public URL. Without publish configuration it returns the local bundle path.

Publish defaults:

```bash
export XFETCH_TARGET_REPO='/path/to/content-repo'
export XFETCH_REPO_OWNER='owner'
export XFETCH_REPO_NAME='repo'
```

Optional overrides: `XFETCH_BRANCH`, `XFETCH_CONTENT_SUBDIR`, `XFETCH_CONTENT_ROOT`.

## Other commands

```bash
python -m xfetch ingest "<url>" --json
python -m xfetch sync <bundle-dir> --target-repo <repo> --repo-owner <owner> --repo-name <name> --json
python -m xfetch publish <bundle-dir> --target-repo <repo> --repo-owner <owner> --repo-name <name> --json
```

Use `ingest` only when a local bundle is desired without publication. `sync` prepares a target working tree without committing. `publish` publishes an existing bundle. Publication copies durable bundle content only; the target repository owns rendering/presentation.

## Result semantics

A normalized document includes `capture_status`:

- `complete`: connector captured the meaningful source content it knows how to preserve.
- `partial`: usable content was captured, but completeness is not guaranteed.
- `metadata_only`: only metadata/description/thumbnail was captured; do not describe this as full preservation.
- `failed`: reserved for explicit failed-capture records; normal CLI failures return non-zero instead.

`content_kinds` describes what was captured, such as `text`, `images`, `transcript`, `metadata`, or `thumbnail`.

When `save --json` reports `published: true`, return its `public_url` as the saved link. Also preserve the reported `capture_status`; do not describe a `partial` or `metadata_only` result as a complete archive.

After publication, `publication.json` records the content commit revision and public URL. The target repository is a content/output surface; xfetch remains the ingestion runtime.

## Supported source families

- X status URLs
- generic public web pages
- RSS/Atom feeds
- public Telegram URLs
- WeChat articles
- Xiaohongshu notes when public HTML contains the note state
- YouTube video URLs: `partial` when public captions are captured, otherwise `metadata_only`
- Bilibili video URLs: `partial` when public subtitles are captured, otherwise `metadata_only`

YouTube caption tracks can be advertised but inaccessible without additional playback tokens; keep those results `metadata_only` and report the recorded capture limitation. Bilibili subtitles that require login likewise remain `metadata_only`.

If WeChat returns a verification page or Xiaohongshu returns a login wall, report the fetch failure rather than saving the interstitial as content.

## Safety

Only public HTTP(S) destinations are fetchable. xfetch rejects loopback, private, link-local, reserved, and metadata-network destinations, including redirects and downloaded assets.
