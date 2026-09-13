# TODO

## v0.2.0 - In Progress ✓
- [x] Progress bars with ETA for all phases
- [x] Crash recovery with state persistence
- [x] Rich terminal formatting
- [ ] Web UI (optional, future consideration)

## v0.3.0 - Planned
### Enhanced Analysis
- [ ] Add SequenceMatcher for top 20 pairs (detect paragraph reordering)
- [ ] Improve paraphrase detection with block-level signals
- [ ] Add language-specific tokenization (jieba for Chinese, MeCab for Japanese)
- [ ] Support for multiple similarity thresholds via config file

### Performance
- [ ] Parallel content extraction
- [ ] Incremental crawl mode (only check new/modified pages)
- [ ] Optional MinHash/LSH for >200 pages
- [ ] Memory optimization for large sites

### Reporting
- [ ] HTML report with interactive filtering
- [ ] Export to Excel with charts
- [ ] Diff view showing actual text differences
- [ ] Screenshot comparison (optional)

## v0.4.0 - Advanced Features
### Crawl Enhancements
- [ ] Sitemap.xml parsing
- [ ] robots.txt respect
- [ ] JavaScript rendering (playwright integration)
- [ ] Custom crawl rules (include/exclude patterns)
- [ ] Pagination detection and handling

### Content Intelligence
- [ ] Product schema detection (JSON-LD)
- [ ] Canonical URL conflict detection
- [ ] Thin content detection (<300 words)
- [ ] Auto-detect navigation/footer/sidebar
- [ ] Meta tag comparison (title, description)

### Integration
- [ ] REST API mode
- [ ] Webhook notifications
- [ ] Slack/Discord integration
- [ ] CI/CD pipeline examples
- [ ] Docker image

## Backlog
- [ ] Machine translation detection
- [ ] Historical comparison (track changes over time)
- [ ] Batch mode for multiple sites
- [ ] Plugin system for custom extractors
- [ ] Cloud storage integration (S3, GCS)
- [ ] Distributed crawling support

## Known Issues
- [ ] Fix test import error in tests/test_integration.py
- [ ] Validate trafilatura quality on pure table-based pages
- [ ] Test full-width character normalization edge cases
- [ ] Verify SSRF protection on all platforms

## Documentation
- [ ] Add video tutorial
- [ ] Write troubleshooting guide
- [ ] Create example workflows for common SEO scenarios
- [ ] Document comparison with Screaming Frog
- [ ] Add architecture decision records (ADRs)

## Research
- [ ] Benchmark MinHash vs TF-IDF on 500+ pages
- [ ] Evaluate commercial tools (Sitebulb, Siteliner) on same fixtures
- [ ] Survey real-world usage patterns after 2 weeks
- [ ] A/B test different extraction confidence thresholds
