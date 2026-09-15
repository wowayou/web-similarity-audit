# FAQ

## Is there a stable Python API?

No. Use the CLI for stable workflows; low-level classes in `docs/API.md` are
experimental.

## How is recovery stored?

The output directory contains `.audit_state.json`. Use `--resume` to continue
an interrupted run, or `--no-resume` to discard it.

## How do I tune an audit?

Use the actual CLI flags shown by `web-similarity-audit --help`. Similarity
priority counts are recorded in `pairs.csv`, not `pages.json`.