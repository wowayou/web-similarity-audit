# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-01-XX

### Added
- **Site-wide crawl mode** with `--crawl` flag for automatic URL discovery
- **Progress bars** with time estimation for long-running operations
- **Crash recovery** with `--resume` flag and `.audit-state.json` persistence
- **Block overlap metric** for paragraph-level duplication detection
- **Enhanced template detection** with configurable threshold
- **Rich terminal UI** with colored output and progress tracking
- Comprehensive documentation suite:
  - ARCHITECTURE.md - System design and components
  - API.md - Python API reference
  - DEPLOYMENT.md - Docker and CI/CD setup
  - CONTRIBUTING.md - Development guidelines
  - FAQ.md - 50+ common questions
  - EXAMPLES.md - Real-world usage patterns
  - SECURITY.md - Security policy
  - README.zh-CN.md - Chinese translation
- Automated release workflow with GitHub Actions
- Cross-platform CI (Linux, macOS, Windows)

### Changed
- Improved error messages with actionable suggestions
- Better SSRF protection with explicit IP validation
- Enhanced rate limiting with per-host token bucket
- More detailed JSON output with extraction metadata

### Fixed
- Template detection now handles small page sets correctly
- Content extraction failures are properly logged
- State file cleanup on successful completion

## [0.1.0] - 2025-01-XX

### Added
- Initial release with core functionality
- URL list comparison mode
- Main content extraction with trafilatura
- Multiple similarity signals:
  - SHA-256 for exact matches
  - N-gram Jaccard for phrase overlap
  - TF-IDF cosine for topic similarity
- Template detection and removal
- Three-tier priority system (P1/P2/P3)
- JSON, CSV, and Markdown outputs
- HTTP safety features:
  - Request timeout and size limits
  - Rate limiting (per-host)
  - SSRF protection
  - Retry with exponential backoff
- CJK text support
- Comprehensive test suite
- CLI with argparse

### Security
- SSRF protection blocks private IP ranges
- User-Agent identifies tool and version
- No credential storage or authentication
- Input validation for URLs

## [Unreleased]

### Planned for 0.3.0
- Sitemap.xml parsing for faster URL discovery
- Canonical link validation
- Hreflang analysis for multilingual sites
- Enhanced paraphrase detection with sequence alignment
- robots.txt compliance
- MinHash/LSH for O(n log n) comparison on large sites
- Incremental mode (only compare changed pages)

### Planned for 0.4.0
- Optional REST API server
- Web UI for interactive exploration
- Database backend for historical tracking
- Webhook notifications
- Custom threshold configuration
- Plugin system for custom extractors

### Potential Future Features
- JavaScript rendering support (via Playwright)
- Image similarity detection
- Schema.org validation
- Structured data comparison
- Link graph analysis
- Performance metrics collection

---

## Release Notes

For detailed release notes with examples and migration guides, see:
- [v0.2.0 Release Notes](../RELEASE_NOTES_v0.2.0.md)

## Version Support

| Version | Status | Support Ends |
|---------|--------|--------------|
| 0.2.x   | Active | TBD          |
| 0.1.x   | Maintenance | 2025-06-30   |

## Upgrade Guide

### From 0.1.x to 0.2.x

**No breaking changes.** All 0.1.x commands work in 0.2.x.

**New features to try:**
```bash
# Crawl mode (new in 0.2.0)
web-similarity-audit --crawl https://example.com --max-pages 200

# Resume after interruption (new in 0.2.0)
web-similarity-audit --resume
```

**Dependencies:**
- No new required dependencies
- Optional: Rich library for progress bars (auto-installed)

**Config changes:**
- None required
- New optional flags: `--template-threshold`, `--resume`, `--crawl`, `--max-pages`

## Deprecation Notices

**None currently.**

All features from 0.1.0 remain supported in 0.2.0.

## Known Issues

### v0.2.0
- [ ] Progress bars may flicker on some terminal emulators
- [ ] Large crawls (>500 pages) can exceed 5-minute target on slow networks
- [ ] Template detection struggles with very dynamic sites (e.g., news homepages)
- [ ] No robots.txt compliance yet (planned for 0.3.0)

### v0.1.0
- [x] No progress feedback during long operations (fixed in 0.2.0)
- [x] State not preserved across runs (fixed in 0.2.0)
- [x] Manual URL listing required (fixed in 0.2.0 with crawl mode)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License - see [LICENSE](../LICENSE)

---

**Questions?** Check the [FAQ](FAQ.md) or open an [issue](https://github.com/wowayou/web-similarity-audit/issues).
