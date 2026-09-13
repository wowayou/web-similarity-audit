# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Progress bars with time estimates for all phases (crawling, fetching, extraction, similarity)
- Crash recovery system with `--resume` and `--no-resume` flags
- State persistence in `.audit-state.json` for interrupted runs
- Elapsed time and ETA display during long operations
- Automatic state cleanup on successful completion

### Changed
- Enhanced CLI output with rich formatting and spinners
- Improved error messages with color coding

## [0.1.0] - 2025-01-XX

### Added
- Initial release
- CLI tool for auditing web page similarity
- Support for 2-200 URLs via direct input or CSV file
- Website crawling mode (`--crawl`) similar to Screaming Frog
- Main content extraction with trafilatura
- Multiple similarity signals: SHA-256, n-gram Jaccard, TF-IDF, block overlap
- Template detection and removal for cleaner comparison
- Priority classification (P1/P2/P3) with explicit trigger reasons
- JSON, CSV, and Markdown report outputs
- SSRF protection and rate limiting
- Support for English and CJK (Chinese/Japanese/Korean) text
- Comprehensive test suite with 16 tests
