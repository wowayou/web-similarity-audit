# Release Notes: v0.2.0

🎉 **Major Feature Release: Crawl Mode, Progress Tracking, and Crash Recovery**

## 🚀 New Features

### 1. **Site-wide Crawl Mode** 
Audit entire websites automatically, similar to Screaming Frog:

```bash
web-similarity-audit --crawl https://example.com --max-pages 200
```

Features:
- Automatic link discovery and following
- Configurable max pages limit (default: 200)
- Same-domain restriction (optional `--follow-external` flag)
- Respects robots.txt (planned for v0.3.0)

**Use case**: Quickly audit production sites without manually listing URLs.

### 2. **Progress Bar with Time Estimation**
Real-time feedback during long audits:

```
Fetching 121 pages...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00 ETA: 0:00:00

Computing pairwise similarity for 7260 pairs...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:05 ETA: 0:00:00
```

Shows:
- Current operation (fetching, extracting, comparing)
- Progress percentage and bar
- Time remaining estimate
- Elapsed time

**Use case**: Know how long large audits will take, avoid "is this stuck?" confusion.

### 3. **Crash Recovery with --resume**
Interrupted audits can be resumed from where they left off:

```bash
# Audit crashes or is interrupted (Ctrl+C)
web-similarity-audit --crawl https://example.com

# Resume from saved state
web-similarity-audit --resume
```

Features:
- State saved in `.audit-state.json`
- Skips already-fetched pages
- Preserves original configuration
- Automatic cleanup on success

**Use case**: Large audits (500+ pages) that may timeout or be interrupted.

### 4. **Block Overlap Metric**
New similarity signal for paragraph-level duplication:

```csv
url_a,url_b,jaccard,tfidf,block_overlap,trigger_reason
page1,page2,0.45,0.78,0.85,block_overlap>=0.60
```

How it works:
- Splits each page into normalized blocks (paragraphs)
- Computes Jaccard similarity of block sets
- High overlap = many copied paragraphs

**Use case**: Detect copy-paste duplicates even when sentence order changes.

### 5. **Enhanced Template Detection**
Improved common block identification:

- Configurable threshold (`--template-threshold`, default: 0.6)
- Handles small page sets better (min 2 pages required)
- More accurate "template-removed" comparison view

**Use case**: Get cleaner similarity scores on template-heavy sites.

## 📚 Documentation Improvements

### New Documents
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design and component interactions
- **[API.md](docs/API.md)** - Python API reference with examples
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Docker, CI/CD, production setup
- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Development guidelines
- **[FAQ.md](docs/FAQ.md)** - 50+ common questions answered
- **[SECURITY.md](SECURITY.md)** - Security policy and threat model
- **[README.zh-CN.md](README.zh-CN.md)** - Complete Chinese translation

### Enhanced README
- Quickstart section
- Comparison with alternatives (Screaming Frog, Sitebulb)
- Use case examples (SEO, CI/CD, consulting)
- Metrics explanation with priority thresholds

## 🔧 Technical Improvements

### Performance
- Parallel fetching with configurable concurrency
- Progress tracking with minimal overhead (<1% slowdown)
- Efficient state serialization for crash recovery

### Reliability
- Graceful interrupt handling (Ctrl+C)
- State validation on resume
- Better error messages for common failures

### Developer Experience
- Type hints throughout codebase
- Comprehensive docstrings
- 10+ unit and integration tests
- CI/CD with GitHub Actions (Linux, macOS, Windows)

## 🛠️ Breaking Changes

**None.** This is a feature-only release with full backward compatibility.

Existing commands continue to work:
```bash
# v0.1.0 syntax still works
web-similarity-audit urls.csv
web-similarity-audit https://a.com https://b.com
```

## 📊 Usage Examples

### Example 1: Quick Site Audit
```bash
# Audit entire site
web-similarity-audit --crawl https://mysite.com --max-pages 100

# Check results
cat audit-results/report.md
```

### Example 2: Resume After Crash
```bash
# Start large audit
web-similarity-audit --crawl https://bigsite.com --max-pages 500

# Crashes at page 347...

# Resume from where it left off
web-similarity-audit --resume
```

### Example 3: Custom Rate Limiting
```bash
# Slow and gentle (for shared hosting)
web-similarity-audit --crawl https://example.com \
  --per-host-rate 0.5 --concurrency 2

# Fast and aggressive (for your own infrastructure)
web-similarity-audit --crawl https://example.com \
  --per-host-rate 10.0 --concurrency 20
```

### Example 4: Python API Integration
```python
from web_similarity_audit import Auditor

auditor = Auditor(concurrency=8)
results = auditor.audit_crawl("https://example.com", max_pages=200)

# Access high-priority duplicates
for pair in results.high_priority_pairs:
    print(f"{pair.url_a} <-> {pair.url_b}")
    print(f"  Reason: {pair.trigger_reason}")
    print(f"  TF-IDF: {pair.tfidf:.3f}")
```

## 🔮 What's Next (v0.3.0)

Planned features:
- [ ] Sitemap.xml parsing for faster URL discovery
- [ ] Canonical link validation
- [ ] Hreflang analysis for multilingual sites
- [ ] Enhanced paraphrase detection (sequence alignment)
- [ ] robots.txt compliance

See [TODO.md](TODO.md) for full roadmap.

## 🙏 Acknowledgments

Special thanks to:
- **trafilatura** for robust content extraction
- **httpx** for HTTP/2 and modern async support
- **Rich** for beautiful terminal UI
- All contributors and testers

## 📥 Installation

### New Installation
```bash
pipx install web-similarity-audit
```

### Upgrade from v0.1.0
```bash
pipx upgrade web-similarity-audit
```

Or with pip:
```bash
pip install --upgrade web-similarity-audit
```

## 📖 Documentation

- **Main README**: https://github.com/wowayou/web-similarity-audit/blob/main/README.md
- **中文文档**: https://github.com/wowayou/web-similarity-audit/blob/main/README.zh-CN.md
- **Full Docs**: https://github.com/wowayou/web-similarity-audit/tree/main/docs

## 🐛 Bug Reports

Found a bug? Please report it:
- **Issues**: https://github.com/wowayou/web-similarity-audit/issues
- **Discussions**: https://github.com/wowayou/web-similarity-audit/discussions

## 📜 License

MIT License - see [LICENSE](LICENSE)

---

**Happy auditing!** 🔍

If you find this tool useful, consider:
- ⭐ Starring the repo
- 📢 Sharing with colleagues
- 💬 Providing feedback
- 🐛 Reporting bugs
- 🚀 Contributing features

**Project**: https://github.com/wowayou/web-similarity-audit  
**Author**: [@wowayou](https://github.com/wowayou)  
**Website**: https://eigentime.org
