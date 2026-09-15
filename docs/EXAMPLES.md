# Examples

Use the CLI:

```bash
web-similarity-audit --crawl https://example.com --max-pages 200
web-similarity-audit urls.csv --output-dir audit-results
```

CSV input has a required `url` column and optional `selector`, `start_marker`,
and `end_marker` columns. Use `web-similarity-audit --help` as the flag source
of truth. P1 counts belong in `pairs.csv`'s `priority` column.