# Quick Start Guide

## Installation

```bash
cd web-similarity-audit
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

## Run Tests

```bash
pytest tests/ -v
```

Expected output:
```
============================== 12 passed in 0.54s ===============================
```

## Basic Usage

### Compare 2 URLs directly

```bash
web-similarity-audit https://example.com https://example.org
```

### Compare from CSV file

Create `urls.csv`:
```csv
url,selector,start_marker,end_marker
https://example.com/page1,,,
https://example.com/page2,#main,,
https://example.com/page3,,<!-- START -->,<!-- END -->
```

Run:
```bash
web-similarity-audit urls.csv --output-dir results
```

## Output Files

Three files are generated in the output directory:

1. **pages.json** - Extraction metadata for each page
2. **pairs.csv** - Similarity scores for all page pairs
3. **report.md** - Human-readable summary

## Example Output

```
Fetching 2 pages...
Extracting main content...
Detecting common template blocks...
  Template detection disabled (n=2 < 5)
Computing pairwise similarity for 1 pairs...
Generating reports in audit-results...

Completed in 0.96s
  P1 (high): 1
  P2 (moderate): 0
  P3 (low): 0
```

## Understanding Results

### Priority Levels

- **P1 (High)**: Strong similarity - likely duplicates
  - SHA-256 exact match, OR
  - TF-IDF ≥ 0.85, OR
  - Jaccard ≥ 0.7, OR
  - Block overlap ≥ 0.8

- **P2 (Moderate)**: Moderate similarity - review recommended
  - TF-IDF ≥ 0.6, OR
  - Jaccard ≥ 0.4, OR
  - Block overlap ≥ 0.5

- **P3 (Low)**: Some similarity - may be coincidental
  - TF-IDF ≥ 0.3, OR
  - Jaccard ≥ 0.2, OR
  - Block overlap ≥ 0.3

### Extraction Methods

- **selector**: CSS selector found and used
- **markers**: Start/end markers found and used
- **trafilatura**: ML-based extraction successful
- **body_fallback**: Uncertain extraction (flagged)
- **selector_failed**: Selector not found (error)
- **markers_failed**: Markers not found (error)

## Command Options

```bash
web-similarity-audit [OPTIONS] <input>

Options:
  --output-dir DIR           Output directory (default: ./audit-results)
  --max-response-size N      Max bytes per response (default: 2MB)
  --timeout N                Request timeout in seconds (default: 10)
  --rate-limit N             Requests/sec per host (default: 2)
  --max-concurrent N         Max concurrent requests (default: 4)
```

## Exit Codes

- `0`: Success
- `1`: Invalid input
- `2`: Network failure (>20% pages unreachable)
- `3`: Extraction failure (>20% pages failed)
- `4`: Fatal error

## Common Issues

### SSRF Protection Error

```
SSRF protection: example.local resolves to blocked IP 192.168.1.1
```

This is expected - the tool blocks private IPs for security.

### Extraction Uncertain

```
Main content extraction uncertain: using body fallback
```

The page will still be processed, but check the output. Consider providing a CSS selector in the CSV.

### Template Detection Disabled

```
Template detection disabled (n=2 < 5)
```

Normal behavior for <5 pages. Template removal requires at least 5 pages to avoid false positives.

## Next Steps

1. Read [README.md](README.md) for detailed documentation
2. Check [IMPLEMENTATION.md](IMPLEMENTATION.md) for technical details
3. Run `./demo.sh` for a complete demonstration
