# Web Similarity Audit

[![CI](https://github.com/wowayou/web-similarity-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/wowayou/web-similarity-audit/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command-line tool for detecting duplicate and near-duplicate web pages with detailed similarity analysis. Built for SEO professionals who need **explicit**, **deterministic**, and **explainable** content auditing.

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

## Usage Examples

### Compare URLs from CSV

Create a file `urls.csv`:
```csv
url
https://example.com/page1
https://example.com/page2
https://example.com/page3
```

Run:
```bash
web-similarity-audit --csv urls.csv
```

### Full-site Audit with Custom Settings

```bash
web-similarity-audit \
  --crawl https://example.com \
  --max-pages 500 \
  --concurrency 8 \
  --per-host-limit 3.0 \
  --output my-audit
```

### Check Specific Priority Level

```bash
web-similarity-audit --crawl https://example.com
cat audit-results/pairs.csv | grep ",P1,"
```

## Output

All results are saved to `audit-results/` (or custom directory with `--output`):

- **`report.md`** - Human-readable summary with statistics
- **`pages.json`** - Full page metadata (extraction status, word counts, hashes)
- **`pairs.csv`** - All similarity comparisons with trigger reasons
- **`blocks.json`** - Detected template blocks (if any)

Example `pairs.csv`:
```csv
url_a,url_b,priority,sha256_match,jaccard,tfidf,block_overlap,trigger
https://example.com/a,https://example.com/b,P1,False,0.82,0.91,0.76,"tfidf>=0.85"
https://example.com/c,https://example.com/d,P2,False,0.45,0.68,0.52,"jaccard>=0.40"
```

## Priority Levels

| Priority | Criteria | Meaning |
|----------|----------|---------|
| **P1** (High) | TF-IDF ≥ 0.85 **or** Jaccard ≥ 0.60 **or** SHA-256 match | Near-identical content, likely duplicates |
| **P2** (Moderate) | Jaccard ≥ 0.40 **or** TF-IDF ≥ 0.70 **or** Block overlap ≥ 0.60 | Similar content, review recommended |
| **P3** (Low) | Jaccard ≥ 0.25 **or** TF-IDF ≥ 0.50 | Distant similarity, informational |

The `trigger` column shows exactly which signal crossed the threshold.

## How It Works

1. **Fetch** pages with retry logic and rate limiting
2. **Extract** main content using trafilatura (with explicit failure reporting)
3. **Detect** common template blocks across all pages
4. **Compare** both raw and template-removed content
5. **Classify** pairs into P1/P2/P3 based on multiple signals
6. **Report** with full transparency on what triggered each match

## Similarity Signals

| Signal | Purpose | Range |
|--------|---------|-------|
| **SHA-256** | Exact duplicates | Boolean |
| **n-gram Jaccard** | Token overlap (character 3-grams) | 0.0 - 1.0 |
| **TF-IDF Cosine** | Semantic similarity | 0.0 - 1.0 |
| **Block Overlap** | Shared paragraph-level content | 0.0 - 1.0 |

All text is NFKC-normalized and lowercased before comparison.

## Command-Line Options

```
web-similarity-audit [OPTIONS] [URL...]

Positional:
  URL                   One or more URLs to compare (min 2, max 200)

Mode Selection:
  --csv PATH            Read URLs from CSV file (header: "url")
  --crawl URL           Crawl website starting from URL
  --max-pages N         Maximum pages to crawl (default: 200)
  --follow-external     Follow links to external domains

HTTP Settings:
  --concurrency N       Concurrent requests (default: 4)
  --per-host-limit N    Requests per second per host (default: 2.0)
  --timeout N           Request timeout in seconds (default: 30)
  --max-response-mb N   Max response size in MB (default: 10)

Recovery:
  --resume              Resume from saved state (.audit-state.json)
  --no-resume           Force fresh start, ignore saved state

Output:
  --output DIR          Output directory (default: audit-results)

Other:
  --version             Show version and exit
  --help                Show this help message
```

## Error Codes

- **0**: Success
- **1**: Invalid arguments (missing URLs, file not found)
- **2**: HTTP error (connection failed, timeout, SSRF blocked)
- **3**: Extraction error (all pages failed to extract content)
- **4**: Processing error (similarity computation failed)

## Design Principles

1. **Explicit over implicit** - Report failures, don't hide them
2. **Deterministic** - Same input always produces same output
3. **Explainable** - Every decision has a reason you can inspect
4. **Fail fast** - Validate early, exit with clear error codes
5. **No silent fallbacks** - If extraction fails, we say so

## Comparison with Commercial Tools

| Feature | Web Similarity Audit | Screaming Frog | Sitebulb |
|---------|---------------------|----------------|----------|
| CLI automation | ✅ | ❌ | ❌ |
| Reproducible runs | ✅ | ❌ | ❌ |
| Explicit failures | ✅ | ❌ | ❌ |
| Trigger reasons | ✅ | ❌ | ❌ |
| Free & open source | ✅ | 🟡 (limited) | ❌ |
| Whole-site crawl | ✅ | ✅ | ✅ |
| Crash recovery | ✅ | ❌ | ❌ |
| Progress indicators | ✅ | ✅ | ✅ |

## Requirements

- Python 3.10 or higher
- 4 direct dependencies:
  - `beautifulsoup4` - HTML parsing
  - `httpx` - HTTP client with HTTP/2 and brotli
  - `lxml` - Fast XML/HTML processing
  - `trafilatura` - Content extraction
  - `rich` - Terminal UI

All dependencies are automatically installed.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and contribution guidelines.

```bash
git clone https://github.com/wowayou/web-similarity-audit.git
cd web-similarity-audit
python -m venv venv
source venv/bin/activate
pip install -e '.[dev]'
pytest tests/ -v
```

## Roadmap

See [TODO.md](TODO.md) for planned features:
- v0.3.0: Enhanced paraphrase detection, language-specific tokenization
- v0.4.0: Sitemap parsing, canonical conflict detection, JavaScript rendering
- Future: REST API, webhooks, distributed crawling

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Citation

If you use this tool in research or reporting, please cite:

```bibtex
@software{web_similarity_audit,
  title = {Web Similarity Audit: CLI Tool for Duplicate Content Detection},
  author = {Web Similarity Audit Contributors},
  year = {2025},
  url = {https://github.com/wowayou/web-similarity-audit}
}
```

## Acknowledgments

Built with:
- [trafilatura](https://github.com/adbar/trafilatura) for robust content extraction
- [httpx](https://github.com/encode/httpx) for modern async HTTP
- [rich](https://github.com/Textualize/rich) for beautiful terminal UI

Inspired by Screaming Frog's Near Duplicates feature and the need for transparent, reproducible SEO auditing.
