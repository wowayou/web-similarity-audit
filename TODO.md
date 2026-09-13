# Roadmap and TODO

This document tracks planned features, improvements, and known issues.

## Version 0.2.0 (In Progress) ✅

**Theme**: Progress tracking and crash recovery

- [x] Add progress bars with time estimation
- [x] Implement crash recovery with `--resume` flag
- [x] State persistence in `.audit-state.json`
- [x] Rich terminal UI with color-coded output
- [x] Handle keyboard interrupts gracefully
- [ ] Add comprehensive documentation
- [ ] Create examples for common workflows
- [ ] Release v0.2.0

## Version 0.3.0 (Planned)

**Theme**: Enhanced paraphrase detection

### High Priority
- [ ] Add sequence-based similarity (e.g., longest common subsequence)
- [ ] Implement sentence reordering detection
- [ ] Add language-specific tokenization (separate CJK from English)
- [ ] Improve "paraphrase" signal in priority classification
- [ ] Add `--paraphrase-threshold` flag for custom sensitivity

### Medium Priority
- [ ] Add fuzzy matching for product codes and model numbers
- [ ] Detect translated content (same meaning, different language)
- [ ] Add n<5 template detection warning (avoid false removal)
- [ ] Configurable P1/P2/P3 thresholds via CLI

### Documentation
- [ ] Add paraphrase detection examples
- [ ] Document algorithm trade-offs
- [ ] Add benchmarks against commercial tools

## Version 0.4.0 (Planned)

**Theme**: SEO-specific features

### Features
- [ ] **Sitemap.xml parsing** - Discover URLs from sitemap instead of crawling
  - [ ] Support nested sitemaps
  - [ ] Handle sitemap index files
  - [ ] Parse lastmod dates for freshness
- [ ] **Canonical tag analysis**
  - [ ] Detect canonical conflicts (A→B, B→A)
  - [ ] Find self-canonicals with duplicates
  - [ ] Report missing canonical tags
- [ ] **Meta robots detection**
  - [ ] Flag noindex pages in duplicate sets
  - [ ] Detect indexation conflicts
- [ ] **hreflang validation**
  - [ ] Check for duplicate content across languages
  - [ ] Validate hreflang reciprocity
- [ ] **JavaScript rendering** (optional, via Playwright)
  - [ ] `--render-js` flag for SPA/dynamic sites
  - [ ] Configurable wait time for JS execution
  - [ ] Screenshot capture for visual comparison

### Improvements
- [ ] Add `--exclude` patterns (regex) to skip certain URLs
- [ ] Support robots.txt parsing
- [ ] Add user-agent rotation
- [ ] Respect crawl-delay directives

## Version 0.5.0 (Future)

**Theme**: Scale and performance

### Performance
- [ ] Implement MinHash LSH for O(n) instead of O(n²) comparison
- [ ] Add incremental audit mode (only new/changed pages)
- [ ] Parallel processing with multiprocessing
- [ ] Database backend option (SQLite) for large audits
- [ ] Streaming output for very large page sets

### Scale
- [ ] Support 500+ page audits efficiently
- [ ] Add distributed crawling with worker nodes
- [ ] Implement crawl budget management
- [ ] Add memory-mapped file support for huge corpuses

## Version 1.0.0 (Future)

**Theme**: API and integrations

### API
- [ ] REST API mode with `--serve` flag
- [ ] WebSocket support for real-time progress
- [ ] Swagger/OpenAPI documentation
- [ ] Python SDK for programmatic access
- [ ] Authentication and rate limiting

### Integrations
- [ ] Webhook support for audit completion
- [ ] Slack/Discord notifications
- [ ] Google Search Console integration
- [ ] Screaming Frog import/export
- [ ] CSV diff mode (compare two audit runs)

### UI (Optional)
- [ ] Web dashboard for visualization
- [ ] Interactive similarity explorer
- [ ] Heatmap of duplicate clusters
- [ ] Export to Gephi/network analysis tools

## Known Issues

### High Priority
- [ ] Fix test import error in `tests/test_integration.py`
- [ ] Add Windows-specific path handling tests
- [ ] Validate rate limiting accuracy under load

### Medium Priority
- [ ] Improve extraction for table-heavy pages (specs sheets)
- [ ] Handle very long URLs (>2000 chars) in CSV output
- [ ] Add warning for pages with no extractable text
- [ ] Better detection of navigation vs content

### Low Priority
- [ ] Add colorblind-friendly terminal output option
- [ ] Improve error messages for network timeouts
- [ ] Add debug mode with verbose logging

## Non-Goals

These features are explicitly **not planned**:

- ❌ LLM-based similarity (not deterministic, expensive)
- ❌ Image similarity comparison (out of scope)
- ❌ Video content analysis
- ❌ Automated content rewriting
- ❌ SEO score calculation (too subjective)
- ❌ Keyword density analysis (deprecated SEO practice)
- ❌ Link spam detection (different problem domain)
- ❌ GUI desktop application (CLI-first philosophy)

## Ideas / Maybe

Features under consideration:

- 🤔 Diff mode showing exact differences between near-duplicates
- 🤔 Export to XLSX with conditional formatting
- 🤔 Support for authenticated pages (login flow)
- 🤔 Lighthouse integration for performance metrics
- 🤔 A/B test variant detection
- 🤔 Machine learning for custom similarity models (opt-in)
- 🤔 Browser extension for one-click audits
- 🤔 Cloud service for scheduled audits

## Contributing

Want to work on any of these? See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Open an issue to discuss implementation before starting work on major features.

## Priorities

Current focus areas in order:
1. **Stability**: Fix known bugs, improve error handling
2. **Documentation**: Examples, tutorials, API docs
3. **Paraphrase detection**: Core algorithm improvements
4. **SEO features**: Canonical, sitemap, hreflang
5. **Performance**: Scale to 500+ pages efficiently
6. **API**: Enable programmatic usage

---

Last updated: 2025-01-13
