# Web Similarity Audit

[![CI](https://github.com/wowayou/web-similarity-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/wowayou/web-similarity-audit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/web-similarity-audit.svg)](https://pypi.org/project/web-similarity-audit/)
[![Python Version](https://img.shields.io/pypi/pyversions/web-similarity-audit.svg)](https://pypi.org/project/web-similarity-audit/)
[![License](https://img.shields.io/github/license/wowayou/web-similarity-audit.svg)](LICENSE)

A command-line tool for detecting duplicate and near-duplicate web pages. Built for SEO professionals who need explainable, reproducible audits.

## Why This Tool?

Commercial tools like Screaming Frog detect duplicates but lack:
- **Explainability**: Multiple similarity signals with clear thresholds
- **Reproducibility**: Save state and re-run audits with fixtures
- **Explicit failure handling**: Never silently fall back to full-page comparison
- **CI/CD integration**: Run audits in pipelines, not just GUIs

## Features

- 🔍 **Site-wide crawling** with automatic link discovery
- 📊 **Multiple similarity signals**: SHA-256, Jaccard, TF-IDF, block overlap
- 🎯 **Three-tier priority system**: P1 (high), P2 (moderate), P3 (low)
- 🌐 **CJK language support**: Chinese, Japanese, Korean text handling
- 📝 **Template detection**: Compare content with and without common blocks
- 💾 **Crash recovery**: Resume interrupted audits with `--resume`
- 🚦 **Progress tracking**: Real-time progress bars with time estimation
- 🔒 **Security built-in**: SSRF protection, rate limiting, request size limits
- 📤 **Multiple output formats**: JSON, CSV, Markdown reports

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

**Crawl entire site:**
```bash
web-similarity-audit --crawl https://example.com --max-pages 200
```

**Compare specific URLs:**
```bash
# From CSV file
web-similarity-audit urls.csv

# Direct URLs
web-similarity-audit https://example.com/page1 https://example.com/page2
```

**Resume after interruption:**
```bash
web-similarity-audit --resume
```

### Example Output

```
Crawling website starting from: https://example.com
  Max pages: 200

  [1/200] https://example.com
  [2/200] https://example.com/about
  [3/200] https://example.com/products
  ...

Crawl complete: discovered 121 pages

Fetching 121 pages...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:45

Computing pairwise similarity for 7260 pairs...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:05

Completed in 55.28s
  P1 (high): 5
  P2 (moderate): 303
  P3 (low): 453

Reports written to: audit-results/
```

## How It Works

### Content Extraction

1. Fetch HTML via HTTP/2 with retry logic
2. Extract main content using [trafilatura](https://github.com/adbar/trafilatura)
3. Fall back to heuristics (`<main>`, `<article>`, `[role=main]`)
4. **Fail explicitly** if extraction uncertain (never silently use full HTML)

### Similarity Detection

Four independent signals detect different types of duplication:

| Signal | Detects | Threshold |
|--------|---------|-----------|
| **SHA-256** | Exact matches | 100% |
| **Jaccard (3-gram)** | Copied phrases | ≥0.70 (P1) |
| **TF-IDF** | Topic similarity | ≥0.85 (P1) |
| **Block overlap** | Copied paragraphs | ≥0.60 (P2) |

### Priority Levels

- **P1 (High)**: Very similar content requiring immediate action
  - TF-IDF ≥ 0.85 OR Jaccard ≥ 0.70 OR exact match
- **P2 (Moderate)**: Potentially duplicate, worth reviewing
  - TF-IDF ≥ 0.60 OR Jaccard ≥ 0.40 OR block overlap ≥ 0.60
- **P3 (Low)**: Some similarity, likely template-related

## Use Cases

### SEO Auditing

Find duplicate product descriptions, thin content, and template issues:

```bash
web-similarity-audit --crawl https://mystore.com --max-pages 500

# Check high-priority duplicates
cat audit-results/report.md
```

### CI/CD Integration

Block deployments with duplicate content:

```yaml
- name: Run content audit
  run: web-similarity-audit urls.csv

- name: Check for duplicates
  run: |
    P1_COUNT=$(jq '.summary.p1_count' audit-results/pages.json)
    if [ "$P1_COUNT" -gt 0 ]; then
      echo "❌ Found $P1_COUNT high-priority duplicates"
      exit 1
    fi
```

### Consulting Deliverables

Generate reproducible audits with evidence:

```bash
web-similarity-audit --crawl https://client-site.com --output client-audit
tar -czf client-audit-2025-01-15.tar.gz client-audit/
```

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[API Reference](docs/API.md)** - Python API usage
- **[Examples](docs/EXAMPLES.md)** - Real-world usage patterns
- **[FAQ](docs/FAQ.md)** - Common questions (50+ Q&A)
- **[Deployment](docs/DEPLOYMENT.md)** - Docker and CI/CD setup
- **[Contributing](docs/CONTRIBUTING.md)** - Development guidelines
- **[Changelog](docs/CHANGELOG.md)** - Version history
- **[中文文档](README.zh-CN.md)** - Chinese translation

## Comparison with Alternatives

| Feature | Screaming Frog | Sitebulb | This Tool |
|---------|----------------|----------|-----------|
| **Price** | £149/year | £35-275/mo | Free |
| **Interface** | GUI | GUI + reports | CLI |
| **Explainability** | Single score | Good | Multiple signals |
| **CI/CD** | Manual export | Manual | Native |
| **Offline** | Yes | Yes | Yes |
| **Open Source** | No | No | Yes |
| **Reproducibility** | Manual | Manual | Automatic |
| **Max pages (free)** | 500 | - | Unlimited |

**Use Screaming Frog/Sitebulb if:** You want a comprehensive GUI tool with visualization.  
**Use this tool if:** You need explainable audits in CI/CD or consulting deliverables.

## Advanced Usage

### Custom Settings

```bash
web-similarity-audit --crawl https://example.com \
  --max-pages 500 \
  --concurrency 8 \
  --per-host-rate 3.0 \
  --timeout 60 \
  --template-threshold 0.7 \
  --output my-audit
```

### Python API

```python
from web_similarity_audit import Auditor

auditor = Auditor(concurrency=8, per_host_rate=2.0)
results = auditor.audit_crawl("https://example.com", max_pages=200)

for pair in results.high_priority_pairs:
    print(f"{pair.url_a} <-> {pair.url_b}")
    print(f"  Reason: {pair.trigger_reason}")
    print(f"  TF-IDF: {pair.tfidf:.3f}")
```

See [API.md](docs/API.md) for full documentation.

## Requirements

- Python 3.10 or later
- 4 dependencies:
  - `httpx[http2,brotli]` - Modern HTTP client
  - `beautifulsoup4` - HTML parsing
  - `lxml` - XML/HTML processing
  - `trafilatura` - Content extraction

## Security

- SSRF protection blocks private IP ranges
- Rate limiting prevents accidental DoS
- Request size limits (10MB default)
- No credential storage or authentication
- See [SECURITY.md](SECURITY.md) for full policy

## Performance

- **Small sites** (<50 pages): ~30-60 seconds
- **Medium sites** (200 pages): ~2-4 minutes
- **Large sites** (500 pages): ~5-10 minutes

Bottleneck is network I/O (fetching), not computation. Use `--concurrency` and `--per-host-rate` to tune.

## Limitations

- **JavaScript rendering**: Not supported (static HTML only)
- **Authentication**: Not supported (public pages only)
- **Max pages**: O(n²) comparison limits practical max to ~1000 pages
- **Paraphrase detection**: Limited (planned improvement with sequence alignment)
- **robots.txt**: Not yet respected (planned for v0.3.0)

## Roadmap

**v0.3.0** (Q2 2025):
- Sitemap.xml parsing
- Canonical link validation
- Hreflang analysis
- robots.txt compliance
- Enhanced paraphrase detection

**v0.4.0** (Q3 2025):
- Optional REST API
- Web UI for exploration
- MinHash/LSH for O(n log n) on large sites
- Incremental mode (only compare changed pages)

See [TODO.md](TODO.md) for full roadmap.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for:
- Development setup
- Code style guidelines
- Testing requirements
- Pull request process

## License

MIT License - see [LICENSE](LICENSE)

Free for commercial and personal use.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/wowayou/web-similarity-audit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/wowayou/web-similarity-audit/discussions)
- **Author**: [@wowayou](https://github.com/wowayou)
- **Website**: [eigentime.org](https://eigentime.org)

## Acknowledgments

- [trafilatura](https://github.com/adbar/trafilatura) - Robust content extraction
- [httpx](https://github.com/encode/httpx) - Modern HTTP client
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal UI

---

**Star this repo** if you find it useful! ⭐

**Share with colleagues** who need duplicate content detection. 📢
