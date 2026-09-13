# Roadmap & TODO

This document tracks planned features, improvements, and known issues.

## Version 0.3.0 (Q2 2025)

### High Priority

- [ ] **Sitemap.xml parsing**
  - Auto-discover sitemap from robots.txt
  - Parse sitemap index files
  - Handle gzip-compressed sitemaps
  - Respect priority and lastmod
  - See: #TBD

- [ ] **Canonical link validation**
  - Detect missing canonical tags
  - Find self-referential canonicals
  - Check for canonical chains (A→B→C)
  - Identify canonical conflicts
  - Output: canonical-issues.csv
  - See: #TBD

- [x] **robots.txt compliance**
  - [x] Parse robots.txt before crawling
  - [x] Respect Disallow/Allow directives (prefix + longest-match)
  - [x] Wildcard (`*`) and end-anchor (`$`) support
  - [x] Parse Crawl-delay (exposed on `RobotsRules.crawl_delay`)
  - [x] Case-insensitive agent matching, per-host rule caching
  - [x] `--ignore-robots` CLI escape hatch
  - [ ] Automatically enforce crawl-delay as the request interval
  - See: `src/web_similarity_audit/robots.py`

### Medium Priority

- [ ] **Hreflang analysis**
  - Detect missing return links
  - Find language/region mismatches
  - Validate alternate URLs exist
  - Check for hreflang loops
  - Output: hreflang-issues.csv
  - See: #TBD

- [ ] **Enhanced paraphrase detection**
  - Use difflib.SequenceMatcher for top candidates
  - Detect sentence reordering
  - Identify synonym substitution patterns
  - Add paraphrase-specific priority level
  - See: #TBD

- [ ] **Content quality metrics**
  - Reading level (Flesch-Kincaid)
  - Keyword density
  - Internal/external link counts
  - Image count and alt text coverage
  - Output: quality-metrics.csv
  - See: #TBD

### Low Priority

- [ ] **Crawl politeness improvements**
  - Exponential backoff on 429/503
  - Respect Retry-After header
  - Better User-Agent rotation
  - See: #TBD

- [ ] **Output format enhancements**
  - XLSX export with formulas
  - HTML report with interactive charts
  - SQLite database option
  - See: #TBD

## Version 0.4.0 (Q3 2025)

### High Priority

- [ ] **MinHash/LSH for O(n log n) comparison**
  - Use datasketch library
  - Configurable similarity threshold
  - LSH index for fast candidate retrieval
  - Fallback to exact comparison for high candidates
  - Target: 5000+ pages in <10 minutes
  - See: #TBD

- [ ] **Incremental mode**
  - Store page hashes in persistent DB
  - Only fetch/compare changed pages
  - Track page additions/deletions
  - Output: changes-since-last-run.csv
  - See: #TBD

- [ ] **REST API server**
  - FastAPI-based HTTP server
  - POST /audit with URL list
  - GET /results/{audit_id}
  - WebSocket for progress updates
  - Optional feature, not required
  - See: #TBD

### Medium Priority

- [ ] **Web UI**
  - React/Vue frontend
  - Upload URL list or enter crawl seed
  - Real-time progress updates
  - Interactive duplicate explorer
  - Filter/sort pairs by metric
  - Export subsets to CSV
  - See: #TBD

- [ ] **Database backend**
  - PostgreSQL support for large audits
  - Store historical audit results
  - Track changes over time
  - Query API for trend analysis
  - Optional feature, not required
  - See: #TBD

- [ ] **Webhook notifications**
  - POST results to webhook URL
  - Slack/Discord integration
  - Email notifications (SMTP)
  - Configurable trigger conditions
  - See: #TBD

### Low Priority

- [ ] **Custom threshold configuration**
  - YAML/TOML config file
  - Per-metric threshold tuning
  - Priority level customization
  - Domain-specific presets
  - See: #TBD

- [ ] **Plugin system**
  - Custom content extractors
  - Custom similarity metrics
  - Output format plugins
  - Hook points for extensions
  - See: #TBD

## Version 0.5.0+ (Q4 2025+)

### Future Considerations

- [ ] **JavaScript rendering**
  - Playwright integration
  - Configurable render timeout
  - Screenshot diffing
  - Performance impact acceptable?
  - See: #TBD

- [ ] **Image similarity**
  - perceptual hashing (pHash)
  - Detect duplicate hero images
  - Alt text comparison
  - See: #TBD

- [ ] **Schema.org validation**
  - Extract JSON-LD structured data
  - Validate against schema.org specs
  - Compare structured data across pages
  - Find missing required properties
  - See: #TBD

- [ ] **Link graph analysis**
  - Build internal link graph
  - Find orphaned pages
  - Identify link hubs
  - Calculate PageRank-like scores
  - See: #TBD

- [ ] **Performance metrics**
  - Core Web Vitals collection
  - Page load time tracking
  - Resource size analysis
  - See: #TBD

## Known Issues

### High Priority

- [ ] Progress bars flicker on Windows Terminal
  - Workaround: Use Windows Terminal Preview
  - Root cause: Rich library terminal detection
  - See: #TBD

- [ ] Template detection fails on very small page sets (<5)
  - Current: Disabled for n<5
  - Better: Use adaptive threshold
  - See: #TBD

### Medium Priority

- [ ] Large crawls (>500 pages) exceed 5-minute target
  - Root cause: O(n²) comparison
  - Solution: Implement MinHash in v0.4.0
  - Workaround: Use --max-pages 200
  - See: #TBD

- [ ] Memory usage grows with page count
  - Current: ~500MB for 200 pages
  - Target: <200MB for 200 pages
  - Consider: Streaming comparison
  - See: #TBD

### Low Priority

- [ ] No color output in CI logs
  - Workaround: Rich auto-detects terminal
  - Enhancement: Force color with --color flag
  - See: #TBD

- [ ] CSV output uses Unix line endings on Windows
  - Standard: Python csv module uses system default
  - Enhancement: Add --crlf flag
  - See: #TBD

## Non-Goals

These are explicitly **not** planned:

- ❌ **LLM-based content analysis** - Too slow, non-deterministic
- ❌ **Automatic SEO recommendations** - Out of scope
- ❌ **Keyword research tools** - Use dedicated tools
- ❌ **Backlink analysis** - Use Ahrefs, Majestic, etc.
- ❌ **Rank tracking** - Use SERPWatcher, etc.
- ❌ **On-page SEO scoring** - Too subjective
- ❌ **Content generation** - Not an audit tool
- ❌ **Link building outreach** - Out of scope

## Community Requests

Track most-requested features from GitHub Issues and Discussions:

| Feature | Votes | Status | Target |
|---------|-------|--------|--------|
| JavaScript rendering | 15 | Considering | v0.5.0 |
| MinHash for large sites | 12 | Planned | v0.4.0 |
| Web UI | 10 | Planned | v0.4.0 |
| Canonical validation | 8 | Planned | v0.3.0 |
| Custom thresholds | 6 | Planned | v0.4.0 |
| robots.txt support | 5 | ✅ Done | v0.2.1 |
| Hreflang validation | 4 | Planned | v0.3.0 |
| Sitemap parsing | 4 | Planned | v0.3.0 |

**Want to influence the roadmap?**
- Vote on existing issues with 👍
- Open a feature request
- Contribute a PR

## Recent Completions

### v0.2.0 (Released 2025-01-XX)

- ✅ Site-wide crawl mode
- ✅ Progress bars with time estimation
- ✅ Crash recovery with --resume
- ✅ Block overlap metric
- ✅ Enhanced template detection
- ✅ Rich terminal UI
- ✅ Comprehensive documentation suite
- ✅ Cross-platform CI

### v0.1.0 (Released 2025-01-XX)

- ✅ Core URL comparison
- ✅ Main content extraction
- ✅ Multiple similarity signals
- ✅ Template detection
- ✅ Three-tier priority system
- ✅ JSON/CSV/Markdown output
- ✅ HTTP safety features
- ✅ CJK text support

## Contributing to Roadmap

We welcome community input on priorities!

**How to help:**

1. **Vote on issues** - Use 👍 to show interest
2. **Discuss trade-offs** - Comment on design decisions
3. **Propose alternatives** - Suggest better approaches
4. **Implement features** - Submit PRs for planned items

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for development guidelines.

## Version Support Policy

| Version | Type | Support Duration |
|---------|------|------------------|
| 0.x.0 (major minor) | Feature releases | 6 months |
| 0.x.y (patches) | Bug fixes only | Until next minor |

**Example:**
- v0.3.0 released April 2025 → supported until October 2025
- v0.3.1 released May 2025 → supported until v0.4.0 release

## Release Cadence

- **Major minor releases** (0.x.0): Quarterly
- **Patch releases** (0.x.y): As needed for critical bugs
- **Release candidates**: 2 weeks before major releases

## Compatibility Promise

**Until v1.0.0:**
- CLI flags may change (with deprecation warnings)
- JSON/CSV output schemas may evolve
- Python API is experimental

**After v1.0.0:**
- Semantic versioning strictly followed
- Breaking changes only in major versions
- Deprecation cycle: 2 major versions

---

**Questions about the roadmap?**
Open a [discussion](https://github.com/wowayou/web-similarity-audit/discussions).

**Want to help prioritize?**
Vote on [issues](https://github.com/wowayou/web-similarity-audit/issues) with 👍.
