# Operational routing

The installed host skill is the entry point for natural-language preservation requests:

- Codex `$xfetch` or Claude Code `/xfetch`
- the absolute xfetch executable recorded in the installed skill's `INSTALLATION.md`
- `ingest` for local capture, or `save` when publication was explicitly requested and configured

For local capture, choose the content root in this order:

1. a destination explicitly requested by the user
2. `XFETCH_CONTENT_ROOT`
3. the installer reference's default, normally `~/xfetch-content`

Pass the chosen root explicitly to `ingest`. This keeps local requests local even when publication variables were inherited from another shell. The direct CLI's default remains `content-out` outside the installed skill.

For publication, use `save` only after the user has requested it and `XFETCH_TARGET_REPO`, `XFETCH_REPO_OWNER`, and `XFETCH_REPO_NAME` identify an existing target checkout. Publication output is valid only when the command reports success; preserve its `capture_status`, public URL, and revisions in the response.

Each local bundle contains `document.json`, `index.md`, `publish.json`, and `assets/`; a successfully published bundle also contains `publication.json`. `complete`, `partial`, and `metadata_only` are meaningful capture states and must be reported accurately.

Historical implementation plans and migration notes live under `docs/archive/`.
