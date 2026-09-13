# Web Similarity Audit

[![CI](https://github.com/wowayou/web-similarity-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/wowayou/web-similarity-audit/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command-line tool for detecting duplicate and near-duplicate web pages with detailed similarity analysis. Built for SEO professionals who need **explicit**, **deterministic**, and **explainable** content auditing.

[English](README.md) | [简体中文](README.zh-CN.md)

## Features

✨ **Whole-site crawling** mode like Screaming Frog  
📊 **Multiple similarity signals**: SHA-256, n-gram Jaccard, TF-IDF, block overlap  
🎯 **Template detection** for cleaner comparison  
📈 **Progress bars** with time estimates  
💾 **Crash recovery** with `--resume` flag  
🌐 **CJK support** (Chinese, Japanese, Korean)  
🔒 **SSRF protection** and rate limiting  
📋 **Three output formats**: JSON, CSV, Markdown  
🚫 **Explicit failures** - no silent fallbacks  

## Quick Start

### Installation

```bash
pipx install web-similarity-audit
```

Or with pip:
```bash
pip install web-similarity-audit
```

### Basic Usage

Compare specific URLs:
```bash
web-similarity-audit https://example.com/page1 https://example.com/page2
```

Crawl entire site:
```bash
web-similarity-audit --crawl https://example.com --max-pages 200
```

Resume interrupted audit:
```bash
web-similarity-audit --resume
```

## Why This Tool?

### The Problem

Commercial tools like Screaming Frog detect duplicates, but:
- **Silent fallbacks**: When main content extraction fails, they compare entire pages (including navigation, footers) leading to false positives
- **Black box scoring**: You get a similarity percentage but no explanation
- **No reproducibility**: Can't include in CI or hand to clients with "run this again"

### This Tool's Approach

1. **Explicit failures**: If content extraction fails, it's logged—never silently falls back to comparing full HTML
2. **Multiple signals**: SHA-256 hash, n-gram Jaccard, TF-IDF cosine, block overlap—each tells you something different
3. **Template-aware**: Detects common blocks (navigation, footer) and provides both raw and template-free comparisons
4. **Explainable**: Every high-priority pair shows which metric triggered it: `tfidf>=0.85 OR jaccard>=0.70`
5. **Reproducible**: CLI tool with CSV input/output, perfect for CI pipelines or consultant deliverables

## Documentation

- **[Installation & Usage](README.md#usage)** - Commands and examples
- **[Architecture](docs/ARCHITECTURE.md)** - How it works internally
- **[API Reference](docs/API.md)** - Python integration
- **[Deployment](docs/DEPLOYMENT.md)** - Docker, CI/CD, production setup
- **[Contributing](docs/CONTRIBUTING.md)** - Development guide
- **[Changelog](CHANGELOG.md)** - Version history

## Usage

### Compare Specific URLs

Create `urls.csv`:
```csv
https://example.com/page1
https://example.com/page2
https://example.com/page3
```

Run audit:
```bash
web-similarity-audit urls.csv
```

### Crawl a Website

```bash
web-similarity-audit --crawl https://example.com --max-pages 200
```

Options:
- `--max-pages N`: Limit crawl to N pages (default: 200)
- `--follow-external`: Follow links to other domains (default: same-domain only)
- `--per-host-rate R`: Max requests per second per host (default: 2.0)
- `--concurrency N`: Max concurrent HTTP requests (default: 4)

### Advanced Options

```bash
web-similarity-audit urls.csv \
  --output custom-dir \
  --concurrency 8 \
  --per-host-rate 1.0 \
  --timeout 30 \
  --template-threshold 0.7
```

### Resume Interrupted Audit

If an audit crashes or is interrupted:
```bash
web-similarity-audit --resume
```

State is saved in `.audit-state.json` and cleaned up on successful completion.

## Output

Three files are generated in `audit-results/`:

### 1. pages.json

Full page metadata:
```json
{
  "summary": {
    "total_pages": 121,
    "successful_fetches": 121,
    "extraction_success_rate": 0.95,
    "p1_count": 5,
    "p2_count": 303,
    "p3_count": 453
  },
  "pages": [
    {
      "url": "https://example.com/page1",
      "content_hash": "a3d2e1f...",
      "char_count": 5234,
      "extraction_success": true,
      "extraction_method": "trafilatura"
    }
  ]
}
```

### 2. pairs.csv

Similarity pairs with all metrics:
```csv
url_a,url_b,priority,sha256_match,jaccard,tfidf,block_overlap,trigger_reason
https://example.com/page1,https://example.com/page2,P1,false,0.72,0.88,0.65,tfidf>=0.85 OR jaccard>=0.70
```

### 3. report.md

Human-readable summary with:
- Configuration details
- Summary statistics
- Top similar pairs by priority
- Pages with extraction failures

## Understanding the Metrics

### SHA-256 Hash
Exact content match. If hashes match, pages are identical after normalization.

### N-gram Jaccard Similarity
Measures word sequence overlap using trigrams (3-word chunks).
- High (>0.7): Many identical phrases
- Moderate (0.4-0.7): Some shared phrases
- Low (<0.4): Different wording

### TF-IDF Cosine Similarity
Measures topic similarity while downweighting common words.
- High (>0.85): Very similar topics
- Moderate (0.6-0.85): Related topics
- Low (<0.6): Different topics

### Block Overlap
Measures paragraph-level copying.
- High (>0.6): Many identical paragraphs
- Moderate (0.3-0.6): Some shared blocks
- Low (<0.3): Mostly unique blocks

## Priority Levels

**P1 (High Priority)** - Likely duplicates requiring action:
- TF-IDF ≥ 0.85 OR
- Jaccard ≥ 0.70 OR
- SHA-256 match

**P2 (Moderate Priority)** - Review recommended:
- TF-IDF ≥ 0.60 OR
- Jaccard ≥ 0.40 OR
- Block overlap ≥ 0.60

**P3 (Low Priority)** - Informational only

## Use Cases

### SEO Duplicate Content Audit
```bash
# Crawl production site
web-similarity-audit --crawl https://mysite.com --max-pages 500

# Check for P1 issues
jq '.summary.p1_count' audit-results/pages.json
```

### Pre-Deployment Check
```bash
# In CI pipeline
web-similarity-audit urls.csv
if [ $? -ne 0 ]; then
  echo "Audit failed"
  exit 1
fi

P1_COUNT=$(jq '.summary.p1_count' audit-results/pages.json)
if [ "$P1_COUNT" -gt 0 ]; then
  echo "Found $P1_COUNT high-priority duplicates"
  exit 1
fi
```

### Consultant Deliverable
```bash
# Create reproducible audit
web-similarity-audit --crawl https://client-site.com --max-pages 200

# Share with client:
# - audit-results/ directory
# - "Run: web-similarity-audit --resume" to replicate
```

### Multi-Site Comparison
```bash
# Create combined URL list from multiple sites
cat site1-urls.csv site2-urls.csv > all-urls.csv
web-similarity-audit all-urls.csv
```

## Python API

```python
from web_similarity_audit import Auditor

# Create auditor
auditor = Auditor(concurrency=8, per_host_rate=2.0)

# Crawl and audit
results = auditor.audit_crawl("https://example.com", max_pages=200)

# Access results
print(f"Found {results.summary.p1_count} high-priority duplicates")

for pair in results.high_priority_pairs:
    print(f"{pair.url_a} <-> {pair.url_b}")
    print(f"  TF-IDF: {pair.tfidf:.3f}, Jaccard: {pair.jaccard:.3f}")
```

See [API documentation](docs/API.md) for more details.

## Security

- **SSRF Protection**: Blocks private IP ranges (RFC 1918, RFC 4193, localhost)
- **Rate Limiting**: Per-host token bucket prevents accidental DoS
- **Input Validation**: URL scheme and format validation
- **No Credentials**: Tool never handles authentication
- **Read-Only**: Only reads public web pages

See [SECURITY.md](SECURITY.md) for security policy.

## Limitations

- **Max pages**: 200 by default (configurable, but O(n²) comparison gets slow)
- **Text-only**: Images, videos, and client-side JavaScript content not analyzed
- **Public pages**: No support for authenticated content
- **English-optimized**: Works with CJK languages but TF-IDF tuned for English

## Roadmap

### v0.2.0 (Current)
- [x] Whole-site crawling mode
- [x] Progress bars with ETA
- [x] Crash recovery with --resume
- [x] Block overlap metric
- [x] Comprehensive documentation

### v0.3.0 (Planned)
- [ ] Enhanced paraphrase detection (sequence alignment)
- [ ] Sitemap.xml parsing
- [ ] Canonical link validation
- [ ] Hreflang analysis

### v0.4.0 (Planned)
- [ ] MinHash/LSH for O(n log n) comparison
- [ ] Incremental mode (only compare changed pages)
- [ ] HTML structural similarity

### v1.0.0 (Future)
- [ ] REST API with FastAPI
- [ ] Web UI for results visualization
- [ ] Database backend (SQLite/PostgreSQL)
- [ ] Scheduled audits with job queue

See [TODO.md](TODO.md) for detailed task list.

## Alternatives

**When to use this tool:**
- Need explainable, reproducible audits
- CI/CD integration required
- Working with consultants or clients who need to replicate results
- Want to understand *why* pages are similar

**When to use commercial tools:**
- Need GUI for non-technical users
- Require comprehensive SEO features beyond duplicate detection
- Have budget for paid tools
- Need enterprise support

**Alternatives:**
- [Screaming Frog](https://www.screamingfrogseoseo.com/) - Commercial, GUI, comprehensive SEO
- [Sitebulb](https://sitebulb.com/) - Commercial, visual reports
- [Siteliner](https://www.siteliner.com/) - Free tier, online only

## Contributing

Contributions welcome! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for:
- Development setup
- Code style guide
- Testing requirements
- Pull request process

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Built with:
- [trafilatura](https://github.com/adbar/trafilatura) - Content extraction
- [httpx](https://github.com/encode/httpx) - HTTP client with HTTP/2 support
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing

## Support

- **Documentation**: https://github.com/wowayou/web-similarity-audit/tree/main/docs
- **Issues**: https://github.com/wowayou/web-similarity-audit/issues
- **Discussions**: https://github.com/wowayou/web-similarity-audit/discussions
- **Security**: See [SECURITY.md](SECURITY.md)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

**Made for SEO professionals who need explainable, reproducible duplicate content audits.**
