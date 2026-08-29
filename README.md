# xfetch

Chat-first link preservation runtime.

xfetch turns supported public URLs into portable content bundles and can publish those bundles into a separate content repository for durable static hosting. It is intentionally narrower than its upstream lineage: xfetch is a capture/preservation engine, not a universal reader, inbox, MCP product, search tool, or analysis suite.

## Goal

```text
caller / Hermes
      ↓
    xfetch
fetch → normalize → bundle
                    ↓
               publisher
                    ↓
           content repository
                    ↓
              static hosting
```

The runtime repository owns fetching, normalization, bundle creation, and publication mechanics. The target repository owns rendering, durable published artifacts, and any higher-level index/search experience.

## Capture contract

Every item is normalized into `NormalizedDocument` and written as:

```text
content-out/YYYY-MM/<slug>/
  document.json
  index.md
  publish.json
  assets/
  publication.json   # added after a successful publish
```

`document.json` includes explicit capture quality:

- `complete` — meaningful source content captured to the connector's supported contract.
- `partial` — useful content captured, but completeness is not guaranteed.
- `metadata_only` — only metadata/description/thumbnail captured.
- `failed` — reserved for explicit failed-capture records; normal CLI failures exit non-zero.

`content_kinds` describes captured material such as `text`, `images`, `metadata`, and `thumbnail`.

Asset download failures are not silently ignored: the affected asset records a `capture_error`, `asset_capture_failures` is added to metadata, and a `complete` document is downgraded to `partial`.

## Supported source families

| Source | Current capture level |
|---|---|
| X status | `complete` for preserved text/photos through FxTwitter; posts with unpreserved video and oEmbed fallback are `partial` |
| Generic web | `partial` main/article-oriented text extraction |
| RSS / Atom | `complete` when a full content element is present, otherwise `partial` |
| Public Telegram | `partial` OpenGraph post representation |
| WeChat | article text/images when public HTML is available; verification pages fail explicitly |
| Xiaohongshu | image notes can be `complete`; video notes are `partial` until video preservation exists; login walls fail explicitly |
| YouTube | `metadata_only` |
| Bilibili | `metadata_only` |

YouTube and Bilibili are deliberately not described as full content preservation until transcript/subtitle capture exists.

## Network safety

xfetch accepts public HTTP(S) sources only. Before a request, after a redirect, and before downloading an asset, it resolves the destination and rejects non-public addresses (loopback, private, link-local, reserved, metadata endpoints, and similar ranges). Responses are size-limited to reduce accidental unbounded downloads.

This is a security boundary because xfetch is intended to sit behind an agent/chat front door.

## CLI

Install locally:

```bash
pip install -e .[dev]
python -m xfetch --help
```

### Save

`save` is the canonical one-shot command:

```bash
python -m xfetch save "https://x.com/jack/status/20" --json
```

With publication defaults:

```bash
export XFETCH_TARGET_REPO='/Users/zion/link-vault-publish'
export XFETCH_REPO_OWNER='guchengwei'
export XFETCH_REPO_NAME='link-vault'

python -m xfetch save "https://example.com/article" \
  --content-root ./content-out \
  --json
```

Optional environment overrides:

- `XFETCH_BRANCH`
- `XFETCH_CONTENT_SUBDIR`
- `XFETCH_CONTENT_ROOT`

JSON output includes capture quality plus publication state:

```json
{
  "ok": true,
  "source_type": "web",
  "capture_status": "partial",
  "content_kinds": ["text", "metadata"],
  "bundle_dir": "...",
  "published": true,
  "public_url": "...",
  "revision": "<content commit>",
  "receipt_revision": "<receipt commit>"
}
```

### Ingest

```bash
python -m xfetch ingest "https://example.com/article" --json
```

Writes a local bundle without publishing it.

### Sync

```bash
python -m xfetch sync ./content-out/2026-08/web-example \
  --target-repo /path/to/target \
  --repo-owner owner \
  --repo-name repo
```

Copies the bundle into a target working tree without committing.

### Publish

```bash
python -m xfetch publish ./content-out/2026-08/web-example \
  --target-repo /path/to/target \
  --repo-owner owner \
  --repo-name repo
```

Publication stages only the generated bundle path. Unrelated dirty files are left untouched, and unrelated pre-staged changes cause publication to fail instead of being swept into a content commit.

The publisher creates a content commit, records that immutable content revision in `publish.json`/`publication.json`, creates a receipt commit locally, then pushes both commits in one push. This avoids the self-referential problem of trying to place a commit's own SHA inside itself.

For an existing remote branch, the target checkout must start exactly at `origin/<branch>` before publication. This prevents unrelated local commits from being swept into the publish push.

## Rendering

xfetch keeps a small dependency-free renderer for local preview/export. It handles headings, paragraphs, fenced code, images, ordered/unordered lists, blockquotes, links, inline code, and bold text. Publication does not copy rendered pages into the target repository; the normalized bundle remains the durable source of truth and the target owns presentation.

## Upstream relationship

This repository is a fork of `runesleo/x-reader`, but upstream product direction is not xfetch's specification. Upstream is useful as a source of hard-earned fetcher fixes and fallback behavior. Changes should be ported selectively when they improve xfetch's preservation contract; upstream inbox, MCP, skills, search, and general reader surfaces are intentionally out of scope.

## Development

```bash
pytest -q
```

Pull requests run the test suite on Python 3.10, 3.11, and 3.12.
