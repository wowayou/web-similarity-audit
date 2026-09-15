# Web Similarity Audit

A deterministic CLI for finding duplicate and near-duplicate public web pages.

## Usage

```bash
web-similarity-audit --crawl https://example.com --max-pages 200
web-similarity-audit https://example.com/a https://example.com/b
web-similarity-audit urls.csv --output-dir audit-results
web-similarity-audit --resume --output audit-results
```

CSV input requires a `url` column and may also contain `selector`, `start_marker`, and `end_marker`.

## Options

`--output-dir`/`--output`, `--crawl`, `--max-pages`, `--follow-external`,
`--ignore-robots`, `--max-response-size`, `--timeout`,
`--rate-limit`/`--per-host-rate`, `--max-concurrent`/`--concurrency`,
`--allow-private`, `--resume`, and `--no-resume` are supported. Run
`web-similarity-audit --help` for defaults and details.

## How it works

The crawler discovers HTML pages and, unless `--ignore-robots` is set, applies
robots rules. Each page is fetched with retries, a per-host minimum interval,
and a streamed response-size limit. Extraction tries a CSV selector, then CSV
markers, then trafilatura, then a body fallback marked as uncertain.

Pairs are classified with SHA-256, character-trigram Jaccard, pair-local
TF-IDF cosine, and block overlap. The current thresholds are:

| Priority | Trigger |
| --- | --- |
| P1 | exact hash; TF-IDF ≥ 0.85; Jaccard ≥ 0.70; block overlap ≥ 0.80 |
| P2 | TF-IDF ≥ 0.60; Jaccard ≥ 0.40; block overlap ≥ 0.50 |
| P3 | TF-IDF ≥ 0.30; Jaccard ≥ 0.20; block overlap ≥ 0.30 |

Reports are `pages.json` (page/extraction summary), `pairs.csv` (including the
`priority` column), and `report.md`. To count P1 results in CI, filter
`pairs.csv` by its `priority` column rather than reading `pages.json`.

## Python use

There is no stable high-level Python API. Experimental building blocks are
`PageFetcher`, `ContentExtractor`, `SimilarityCalculator`, `TemplateDetector`,
and `Reporter`; their current signatures are described in [docs/API.md](docs/API.md).

## Security and limits

SSRF checks reject non-public DNS answers by default; `--allow-private` is only
for trusted intranet or local targets. Responses are limited to 2 MiB by
default. See [SECURITY.md](SECURITY.md).

The current all-pairs comparison is O(n²); choose `--max-pages` accordingly.

## Dependencies and documentation

Python 3.10+ and six direct dependencies are required: beautifulsoup4, certifi,
httpx, lxml, trafilatura, and rich.

See [architecture review](docs/ARCHITECTURE_REVIEW.md), [architecture](docs/ARCHITECTURE.md),
[examples](docs/EXAMPLES.md), [FAQ](docs/FAQ.md), [contributing](docs/CONTRIBUTING.md),
and the root [CHANGELOG.md](CHANGELOG.md).