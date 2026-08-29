# Changelog

## 0.2.0 - 2026-08-29

- add public-network validation for source fetches, redirects, and asset downloads
- add bounded response reads for fetch operations
- add `capture_status` and `content_kinds` to the normalized document contract
- downgrade captures when durable asset materialization fails instead of silently claiming completeness
- reject WeChat verification pages and Xiaohongshu login walls as source content
- add a validated X oEmbed fallback when FxTwitter is unavailable
- classify YouTube and Bilibili honestly as `metadata_only` until transcript capture exists
- scope git publication to generated paths and reject unrelated pre-staged changes
- split content revision from publication receipt metadata and push both commits together
- render common Markdown structures including lists, links, blockquotes, code, and images
- replace the legacy agent skill description with the active xfetch interface
- remove the runtime repo's obsolete Pages deployment workflow and add pytest CI

## 0.1.0 - 2026-04

- establish xfetch as the canonical save/publish runtime
- introduce normalized portable bundles and the connector registry
- add X, web, RSS, Telegram, WeChat, Xiaohongshu, YouTube, and Bilibili connectors
- add separate target-repository sync/publish support and static page rendering

Earlier x-reader / x-tweet-fetcher history remains available in git history and archived planning documents; it is not the active xfetch product contract.
