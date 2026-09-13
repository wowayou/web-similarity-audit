# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Language-specific tokenization for better CJK support
- Sitemap.xml parsing for URL discovery
- Canonical tag conflict detection
- Optional JavaScript rendering with Playwright
- REST API mode
- Enhanced paraphrase detection algorithms

## [0.2.1] - 2025-01-15

### Added
- **robots.txt compliance** (`robots.py`): proper RFC 9309 subset parsing with
  `Allow`/`Disallow`, `*` wildcards, `$` end anchors, longest-match precedence
  (Allow wins ties), per-agent groups, `Crawl-delay`, and `Sitemap` collection
- `--ignore-robots` CLI flag for `--crawl` mode
- 6 extraction-precedence and NFKC normalization tests (`tests/test_precedence.py`)
- 16 robots.txt tests (`tests/test_robots.py`)
- Report now separates **Fetch + extract time** from **Computation time**

### Fixed
- robots.txt `Disallow` used exact-URL matching, so paths like `/admin/` never
  blocked `/admin/page`. Now uses correct prefix matching with longest-match rules
- `Crawl-delay` was previously ignored entirely and `Allow` was not parsed

### Changed
- Extractor precedence (`selector` > `markers` > `trafilatura` > body fallback)
  is now explicitly documented in the `ContentExtractor.extract` docstring

## [0.2.0] - 2025-01-15

### Added
- Progress bars with time estimation for all operations (crawl, fetch, extract, compare)
- Crash recovery with `--resume` flag to continue interrupted audits
- State persistence in `.audit-state.json`
- Rich terminal UI with color-coded status messages
- Detailed progress tracking for long-running operations

### Changed
- Improved error messages with more context
- Better handling of keyboard interrupts (Ctrl+C)
- Enhanced user feedback during crawling phase

### Fixed
- Progress bar display issues with large page counts
- State file cleanup on successful completion

## [0.1.0] - 2025-01-13

### Added
- Initial release with core functionality
- CLI tool for detecting duplicate and near-duplicate web pages
- Whole-site crawling mode with `--crawl` flag
- Multiple similarity signals:
  - SHA-256 hash for exact duplicates
  - n-gram Jaccard index for token overlap
  - TF-IDF cosine similarity for semantic similarity
  - Block overlap for shared paragraph detection
- Template detection and removal for cleaner comparison
- Main content extraction using trafilatura
- Explicit extraction failure reporting
- Three output formats:
  - `pages.json` - Full page metadata
  - `pairs.csv` - Pairwise similarity comparisons
  - `report.md` - Human-readable summary
- Priority classification (P1/P2/P3) with explicit trigger reasons
- HTTP features:
  - Automatic retry with exponential backoff
  - Per-host rate limiting
  - Concurrent fetching with connection pooling
  - SSRF protection (blocks private IPs)
  - HTTP/2 and Brotli support
  - Configurable timeout and response size limits
- Cross-platform support (Windows, macOS, Linux)
- CJK (Chinese, Japanese, Korean) text support with NFKC normalization
- CSV input mode for comparing specific URL lists
- Configurable concurrency and rate limiting
- Deterministic output for reproducible audits
- Comprehensive error codes (0-4) for CI integration
- Test suite with 10+ test cases
- GitHub Actions CI pipeline
- Documentation:
  - README with installation and usage
  - Examples for common use cases
  - API documentation in docstrings

### Dependencies
- beautifulsoup4 >= 4.12.0
- httpx[brotli,http2] >= 0.27.0
- lxml >= 5.0.0
- trafilatura >= 1.12.0
- rich >= 13.0.0

### Non-goals (documented)
- LLM-based similarity (not deterministic)
- Web UI or dashboard
- Model Context Protocol (MCP) server
- Database storage
- Automated SEO decisions

[Unreleased]: https://github.com/wowayou/web-similarity-audit/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/wowayou/web-similarity-audit/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/wowayou/web-similarity-audit/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/wowayou/web-similarity-audit/releases/tag/v0.1.0
