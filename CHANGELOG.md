# Changelog

All notable changes to web-similarity-audit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-XX

### Added
- Initial release with core similarity audit functionality
- **Crawl mode**: Whole-site crawling similar to Screaming Frog (`--crawl` flag)
- URL list mode: Direct URL input or CSV file
- Multiple similarity signals: SHA-256, n-gram Jaccard, TF-IDF, block overlap
- Explicit failure reporting for content extraction
- Template detection and dual-view comparison (raw + de-templated)
- Three-tier priority system (P1/P2/P3)
- Multi-format output: JSON, CSV, Markdown
- Cross-platform support: Windows, macOS, Linux
- Comprehensive test suite (16 tests)
- Rate limiting and concurrent request control
- SSRF protection and security measures
- robots.txt respect (basic implementation)
- Smart resource filtering (images, PDFs, CSS, JS)

### Dependencies
- beautifulsoup4 ≥ 4.12.0
- httpx[brotli,http2] ≥ 0.27.0
- lxml ≥ 5.0.0
- trafilatura ≥ 1.12.0

### Documentation
- Comprehensive README with usage examples
- Example scripts in `examples/` directory
- Detailed PRD document

[0.1.0]: https://github.com/yourusername/web-similarity-audit/releases/tag/v0.1.0
