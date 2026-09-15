# Deployment

Install from a tagged release or source distribution, then run the CLI in an
account whose outbound network access is restricted to the intended HTTP(S)
targets. This is defense in depth for URL-auditing workloads.

```bash
python -m pip install web-similarity-audit
web-similarity-audit --crawl https://example.com --max-pages 200
```

Persist the output directory if you need recovery: the state filename is
`.audit_state.json`, and `--resume` continues an interrupted run.
For CI, inspect the `priority` column in `pairs.csv`; `pages.json` contains only
page-extraction summary counts.