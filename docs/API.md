# Experimental Python API

The supported interface is the CLI. These building blocks are experimental and
may change without a major-version guarantee.

- `PageFetcher(...).fetch(url)` asynchronously returns `(text, status, error)`.
  `fetch_all(urls)` preserves input order.
- `ContentExtractor(...).extract(html, page_input, status_code)` returns a
  `PageResult`.
- `SimilarityCalculator().compute_pairwise(page1, page2, common_blocks=None)`
  returns a `SimilarityScore`.
- `TemplateDetector(...).detect_common_blocks(pages)` returns common blocks or
  `None` when there are too few pages.
- `Reporter(output_dir).write_pages_json(pages)`, `write_pairs_csv(scores)`,
  and `write_markdown_report(...)` write the three report formats.

Use the CLI for stable input validation, crawling, recovery, and exit-code
handling.