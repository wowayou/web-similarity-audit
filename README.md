# Web Similarity Audit

A command-line tool for detecting duplicate and near-duplicate web pages with explicit failure reporting and detailed similarity analysis.

## Features

- **Multiple Input Modes**: Direct URLs, CSV files, or whole-site crawling (Screaming Frog style)
- **Smart Content Extraction**: Uses trafilatura for reliable main content extraction
- **Multi-Signal Analysis**: SHA-256, n-gram Jaccard, TF-IDF cosine similarity, and block overlap
- **Template Detection**: Automatically identifies and removes common template blocks
- **Priority Classification**: P1/P2/P3 with explicit trigger reasons for each pair
- **Rich Progress Display**: Real-time progress bars with ETA for all phases
- **Crash Recovery**: Resume interrupted runs with `--resume` flag
- **Comprehensive Reports**: JSON, CSV, and Markdown outputs with detailed diagnostics
- **CJK Support**: Handles English, Chinese, Japanese, and Korean text
- **Safety Features**: SSRF protection, rate limiting, and explicit failure thresholds

## Installation

```bash
pip install web-similarity-audit
```

Or install from source:

```bash
git clone https://github.com/wowayou/web-similarity-audit.git
cd web-similarity-audit
pip install -e .
```

## Quick Start

### Compare specific URLs

```bash
# Direct URLs
web-similarity-audit https://example.com/page1 https://example.com/page2

# From CSV file
web-similarity-audit urls.csv
```

### Crawl entire website

```bash
# Crawl up to 200 pages (default)
web-similarity-audit --crawl https://example.com

# Crawl up to 500 pages
web-similarity-audit --crawl https://example.com --max-pages 500

# Include external links
web-similarity-audit --crawl https://example.com --follow-external
```

### Resume interrupted run

```bash
# Resume from saved state
web-similarity-audit --resume --crawl https://example.com

# Force fresh start
web-similarity-audit --no-resume --crawl https://example.com
```

## CSV Input Format

Create a CSV file with optional custom selectors and markers:

```csv
url,selector,start_marker,end_marker
https://example.com/page1,article.content,<!-- content start -->,<!-- content end -->
https://example.com/page2,main,BEGIN_MAIN,END_MAIN
https://example.com/page3,,,
```

Fields:
- `url` (required): The page URL
- `selector` (optional): CSS selector for main content
- `start_marker` (optional): HTML comment marking content start
- `end_marker` (optional): HTML comment marking content end

## Output Reports

All reports are written to `./audit-results/` (customizable with `--output-dir`):

### 1. pages.json
Detailed page-level data:
```json
{
  "url": "https://example.com/page",
  "status_code": 200,
  "content_hash": "abc123...",
  "extraction_method": "trafilatura",
  "extraction_confident": true,
  "text_length": 1523,
  "text_length_no_template": 1205,
  "has_cjk": false
}
```

### 2. pairs.csv
Pairwise similarity scores:
```csv
url_a,url_b,priority,sha256_match,jaccard,tfidf_cosine,block_overlap,jaccard_no_tpl,tfidf_no_tpl,trigger_reasons
https://a.com,https://b.com,P1,false,0.78,0.91,0.65,0.72,0.89,"tfidf_cosine>=0.85; block_overlap>=0.50"
```

### 3. report.md
Human-readable summary with:
- Execution metadata
- Failure warnings (fetch/extraction issues)
- Priority breakdown
- Top P1 pairs with trigger explanations
- Template blocks detected

## Priority Levels

- **P1 (High)**: Likely duplicates
  - TF-IDF ≥ 0.85, OR
  - Jaccard ≥ 0.25, OR
  - Block overlap ≥ 0.50, OR
  - SHA-256 match
  
- **P2 (Moderate)**: Possibly similar
  - TF-IDF ≥ 0.70, OR
  - Jaccard ≥ 0.15

- **P3 (Low)**: Low similarity
  - Everything else

## Command-Line Options

```
usage: web-similarity-audit [-h] [--output-dir OUTPUT_DIR] [--crawl]
                            [--max-pages MAX_PAGES] [--follow-external]
                            [--max-response-size MAX_RESPONSE_SIZE]
                            [--timeout TIMEOUT] [--rate-limit RATE_LIMIT]
                            [--max-concurrent MAX_CONCURRENT]
                            [--resume] [--no-resume]
                            input [input ...]

Options:
  --output-dir DIR          Output directory (default: ./audit-results)
  --crawl                   Crawl entire website from starting URL
  --max-pages N             Max pages to crawl (default: 200)
  --follow-external         Follow external links in crawl mode
  --max-response-size N     Max response size in bytes (default: 2MB)
  --timeout SECONDS         HTTP timeout (default: 10)
  --rate-limit RPS          Requests per second per host (default: 2)
  --max-concurrent N        Max concurrent requests (default: 4)
  --resume                  Resume from previous interrupted run
  --no-resume               Force fresh start, ignore saved state
```

## Failure Modes

The tool exits with explicit codes:

- `0`: Success
- `1`: Invalid input (bad URLs, missing file, etc.)
- `2`: Too many fetch failures (>20%)
- `3`: Too many extraction failures (>20%)
- `4`: Fatal error or user interrupt

## Development

### Setup

```bash
git clone https://github.com/wowayou/web-similarity-audit.git
cd web-similarity-audit
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e .
```

### Run Tests

```bash
pytest tests/ -v
```

### Project Structure

```
src/web_similarity_audit/
├── cli.py              # Main entry point and CLI logic
├── crawler.py          # Website crawling (Screaming Frog mode)
├── fetcher.py          # HTTP fetching with SSRF protection
├── extractor.py        # Main content extraction
├── template.py         # Template block detection
├── similarity.py       # Similarity scoring engine
├── reporter.py         # Report generation
├── state.py            # Crash recovery state management
├── models.py           # Data models
└── utils.py            # Text normalization utilities
```

## Use Cases

1. **SEO Audits**: Find duplicate content issues across your website
2. **Content Migration**: Verify pages were copied correctly
3. **Quality Assurance**: Detect unintended page duplication
4. **Competitive Analysis**: Compare similar pages across sites
5. **Consulting Deliverables**: Provide evidence-backed reports to clients

## Design Philosophy

- **Explicit over implicit**: All failures are reported, not silently handled
- **Explainable signals**: Every P1/P2 classification shows which thresholds triggered
- **Deterministic**: No LLMs, same input always produces same output
- **Reproducible**: CSV inputs and state files can be shared and re-run
- **No silent fallbacks**: If main content extraction fails, it's flagged explicitly

## License

MIT License - see LICENSE file for details

## Contributing

Issues and pull requests welcome at https://github.com/wowayou/web-similarity-audit

## Acknowledgments

Built with:
- [trafilatura](https://github.com/adbar/trafilatura) for content extraction
- [httpx](https://www.python-httpx.org/) for HTTP operations
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- [rich](https://rich.readthedocs.io/) for terminal UI
