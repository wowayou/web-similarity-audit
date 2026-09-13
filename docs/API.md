# API Reference

This document describes the programmatic API for integrating web-similarity-audit into Python applications.

## Installation

```bash
pip install web-similarity-audit
```

## Quick Start

```python
from web_similarity_audit import Auditor

# Create auditor instance
auditor = Auditor()

# Audit specific URLs
results = auditor.audit_urls([
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
])

# Access results
print(f"Found {len(results.high_priority_pairs)} high-priority duplicates")
for pair in results.high_priority_pairs:
    print(f"{pair.url_a} <-> {pair.url_b}: {pair.tfidf:.2f}")
```

## Core Classes

### Auditor

Main interface for running audits.

```python
class Auditor:
    def __init__(
        self,
        concurrency: int = 4,
        per_host_rate: float = 2.0,
        timeout: int = 15,
        max_retries: int = 3,
        user_agent: str = None
    ):
        """
        Initialize auditor.
        
        Args:
            concurrency: Max concurrent HTTP requests
            per_host_rate: Max requests per second per host
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts for failed requests
            user_agent: Custom User-Agent string (default: web-similarity-audit/version)
        """
```

#### Methods

**audit_urls(urls: List[str]) -> AuditResults**

Audit a list of URLs.

```python
results = auditor.audit_urls([
    "https://example.com/page1",
    "https://example.com/page2"
])
```

**audit_crawl(start_url: str, max_pages: int = 200, follow_external: bool = False) -> AuditResults**

Crawl and audit a website.

```python
results = auditor.audit_crawl(
    start_url="https://example.com",
    max_pages=100,
    follow_external=False
)
```

**resume(state_file: str = ".audit-state.json") -> AuditResults**

Resume a previously interrupted audit.

```python
results = auditor.resume()
```

### AuditResults

Container for audit results.

```python
@dataclass
class AuditResults:
    pages: List[PageInfo]
    pairs: List[SimilarityPair]
    summary: AuditSummary
    execution_time: float
    
    @property
    def high_priority_pairs(self) -> List[SimilarityPair]:
        """Get P1 (high priority) pairs."""
        return [p for p in self.pairs if p.priority == "P1"]
    
    @property
    def moderate_priority_pairs(self) -> List[SimilarityPair]:
        """Get P2 (moderate priority) pairs."""
        return [p for p in self.pairs if p.priority == "P2"]
    
    @property
    def low_priority_pairs(self) -> List[SimilarityPair]:
        """Get P3 (low priority) pairs."""
        return [p for p in self.pairs if p.priority == "P3"]
    
    def get_duplicates_of(self, url: str) -> List[SimilarityPair]:
        """Get all pairs involving a specific URL."""
        return [p for p in self.pairs if url in (p.url_a, p.url_b)]
    
    def export_json(self, path: str):
        """Export results to JSON file."""
    
    def export_csv(self, path: str):
        """Export pairs to CSV file."""
    
    def export_markdown(self, path: str):
        """Export report to Markdown file."""
```

### PageInfo

Information about a single page.

```python
@dataclass
class PageInfo:
    url: str
    content_hash: str
    char_count: int
    word_count: int
    extraction_success: bool
    extraction_method: str  # "trafilatura", "fallback"
    has_template_blocks: bool
    status_code: int
    fetch_time: float
```

### SimilarityPair

A pair of similar pages.

```python
@dataclass
class SimilarityPair:
    url_a: str
    url_b: str
    priority: str  # "P1", "P2", "P3"
    sha256_match: bool
    jaccard: float
    tfidf: float
    block_overlap: float
    trigger_reason: str
```

### AuditSummary

Overall audit statistics.

```python
@dataclass
class AuditSummary:
    total_pages: int
    successful_fetches: int
    failed_fetches: int
    extraction_success_rate: float
    total_pairs: int
    p1_count: int
    p2_count: int
    p3_count: int
    exact_duplicates: int  # SHA-256 matches
    has_template_blocks: bool
```

## Advanced Usage

### Custom Configuration

```python
from web_similarity_audit import Auditor, AuditorConfig

config = AuditorConfig(
    concurrency=8,
    per_host_rate=1.0,
    timeout=30,
    max_retries=5,
    user_agent="MyBot/1.0",
    template_threshold=0.7,  # 70% frequency for template blocks
    similarity_thresholds={
        "p1_tfidf": 0.85,
        "p1_jaccard": 0.70,
        "p2_tfidf": 0.60,
        "p2_jaccard": 0.40,
        "p2_block_overlap": 0.60
    }
)

auditor = Auditor(config=config)
results = auditor.audit_urls(urls)
```

### Progress Callbacks

```python
def on_progress(current: int, total: int, stage: str):
    print(f"[{stage}] {current}/{total} ({current/total*100:.1f}%)")

auditor = Auditor()
results = auditor.audit_crawl(
    start_url="https://example.com",
    max_pages=200,
    progress_callback=on_progress
)
```

### Error Handling

```python
from web_similarity_audit import Auditor, AuditError, FetchError

try:
    auditor = Auditor()
    results = auditor.audit_urls(urls)
except FetchError as e:
    print(f"Failed to fetch: {e.url} - {e.reason}")
except AuditError as e:
    print(f"Audit failed: {e}")
```

### Filtering Results

```python
results = auditor.audit_urls(urls)

# Get only exact duplicates
exact_dupes = [p for p in results.pairs if p.sha256_match]

# Get high-similarity pairs (TF-IDF > 0.9)
high_sim = [p for p in results.pairs if p.tfidf > 0.9]

# Get pairs with specific URL
page_dupes = results.get_duplicates_of("https://example.com/page1")

# Get failed extractions
failed = [p for p in results.pages if not p.extraction_success]
```

### Batch Processing

```python
from web_similarity_audit import Auditor
import glob

auditor = Auditor()

# Process multiple CSV files
csv_files = glob.glob("urls/*.csv")
all_results = []

for csv_file in csv_files:
    with open(csv_file) as f:
        urls = [line.strip() for line in f if line.strip()]
    
    results = auditor.audit_urls(urls)
    all_results.append(results)
    
    print(f"{csv_file}: {results.summary.p1_count} P1 issues")
```

### Integration with Pandas

```python
import pandas as pd
from web_similarity_audit import Auditor

auditor = Auditor()
results = auditor.audit_urls(urls)

# Convert pairs to DataFrame
df = pd.DataFrame([
    {
        "url_a": p.url_a,
        "url_b": p.url_b,
        "priority": p.priority,
        "tfidf": p.tfidf,
        "jaccard": p.jaccard,
        "block_overlap": p.block_overlap,
        "trigger": p.trigger_reason
    }
    for p in results.pairs
])

# Analyze
high_priority = df[df["priority"] == "P1"]
print(f"High priority pairs: {len(high_priority)}")
print(f"Average TF-IDF: {df['tfidf'].mean():.3f}")

# Export
df.to_csv("analysis.csv", index=False)
```

### Async Usage

```python
import asyncio
from web_similarity_audit import AsyncAuditor

async def main():
    auditor = AsyncAuditor()
    
    # Run multiple audits concurrently
    results = await asyncio.gather(
        auditor.audit_urls(urls_set1),
        auditor.audit_urls(urls_set2),
        auditor.audit_urls(urls_set3)
    )
    
    for i, result in enumerate(results, 1):
        print(f"Set {i}: {result.summary.p1_count} P1 issues")

asyncio.run(main())
```

## Lower-Level APIs

### Fetcher

HTTP fetching with SSRF protection.

```python
from web_similarity_audit.fetcher import Fetcher

fetcher = Fetcher(
    timeout=15,
    max_retries=3,
    per_host_rate=2.0
)

# Fetch single URL
page = await fetcher.fetch("https://example.com")
print(f"Status: {page.status_code}")
print(f"Content length: {len(page.html)}")

# Fetch multiple URLs
pages = await fetcher.fetch_all([
    "https://example.com/page1",
    "https://example.com/page2"
])
```

### Extractor

Content extraction wrapper.

```python
from web_similarity_audit.extractor import Extractor

extractor = Extractor()

# Extract from HTML
extracted = extractor.extract(html, url="https://example.com")
print(f"Success: {extracted.extraction_success}")
print(f"Main content: {extracted.main_content[:100]}...")
print(f"Hash: {extracted.content_hash}")
```

### Analyzer

Similarity computation.

```python
from web_similarity_audit.analyzer import Analyzer

analyzer = Analyzer()

# Compute pairwise similarity
pairs = analyzer.compute_all_pairs(extracted_pages)

# Compute similarity for single pair
similarity = analyzer.compute_pair(page_a, page_b)
print(f"TF-IDF: {similarity.tfidf:.3f}")
print(f"Jaccard: {similarity.jaccard:.3f}")
```

### TemplateDetector

Common block detection.

```python
from web_similarity_audit.template_detector import TemplateDetector

detector = TemplateDetector(threshold=0.6)

# Detect common blocks
common_blocks = detector.detect(extracted_pages)
print(f"Found {len(common_blocks)} template blocks")

# Remove templates from page
clean_text = detector.remove_blocks(page.main_content, common_blocks)
```

### Crawler

Website crawling.

```python
from web_similarity_audit.crawler import Crawler

crawler = Crawler(
    max_pages=200,
    follow_external=False,
    respect_robots_txt=True
)

# Crawl site
discovered_urls = await crawler.crawl("https://example.com")
print(f"Discovered {len(discovered_urls)} pages")
```

## CLI Integration

Run CLI programmatically:

```python
from web_similarity_audit.cli import main
import sys

# Override sys.argv
sys.argv = [
    "web-similarity-audit",
    "--crawl", "https://example.com",
    "--max-pages", "100",
    "--output", "results"
]

exit_code = main()
print(f"Exit code: {exit_code}")
```

## Testing Support

### Mock Auditor

```python
from web_similarity_audit.testing import MockAuditor, create_mock_results

# Use in tests
mock_auditor = MockAuditor()
mock_auditor.set_results(create_mock_results(
    page_count=10,
    p1_count=2,
    p2_count=5
))

results = mock_auditor.audit_urls(urls)
assert results.summary.p1_count == 2
```

### Fixtures

```python
from web_similarity_audit.testing import fixtures

# Use predefined test pages
test_pages = fixtures.get_sample_pages()
auditor = Auditor()
results = auditor.audit_urls([p.url for p in test_pages])
```

## Configuration Files

### Load from YAML

```python
from web_similarity_audit import Auditor
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

auditor = Auditor(**config)
results = auditor.audit_urls(urls)
```

Example `config.yaml`:
```yaml
concurrency: 8
per_host_rate: 1.5
timeout: 30
max_retries: 5
template_threshold: 0.65
similarity_thresholds:
  p1_tfidf: 0.85
  p1_jaccard: 0.70
  p2_tfidf: 0.60
  p2_jaccard: 0.40
```

## Logging

```python
import logging
from web_similarity_audit import Auditor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

auditor = Auditor()
results = auditor.audit_urls(urls)

# Logs will include:
# - Fetch progress
# - Extraction successes/failures
# - Template detection results
# - Similarity computation progress
```

## Performance Tuning

```python
from web_similarity_audit import Auditor

# For large sites, reduce memory usage
auditor = Auditor(
    concurrency=2,  # Lower concurrency
    per_host_rate=1.0  # Slower rate
)

# For fast sites, increase throughput
auditor = Auditor(
    concurrency=16,  # Higher concurrency
    per_host_rate=5.0  # Faster rate
)

# For CPU-bound workloads
auditor = Auditor(
    parallel_extraction=True,  # Use multiprocessing for extraction
    parallel_similarity=True   # Use multiprocessing for similarity
)
```

## Examples

### Example 1: SEO Duplicate Content Checker

```python
from web_similarity_audit import Auditor

def check_site_duplicates(domain: str) -> dict:
    """Check a site for duplicate content."""
    auditor = Auditor()
    results = auditor.audit_crawl(f"https://{domain}", max_pages=200)
    
    return {
        "domain": domain,
        "total_pages": results.summary.total_pages,
        "exact_duplicates": results.summary.exact_duplicates,
        "near_duplicates": results.summary.p1_count,
        "pairs": [
            {
                "url_a": p.url_a,
                "url_b": p.url_b,
                "similarity": p.tfidf
            }
            for p in results.high_priority_pairs
        ]
    }

report = check_site_duplicates("example.com")
print(f"Found {report['exact_duplicates']} exact duplicates")
```

### Example 2: Batch Domain Audit

```python
from web_similarity_audit import Auditor
import csv

def audit_multiple_domains(domains: list) -> list:
    """Audit multiple domains and compare results."""
    auditor = Auditor()
    results = []
    
    for domain in domains:
        try:
            result = auditor.audit_crawl(f"https://{domain}", max_pages=50)
            results.append({
                "domain": domain,
                "status": "success",
                "pages": result.summary.total_pages,
                "duplicates": result.summary.p1_count
            })
        except Exception as e:
            results.append({
                "domain": domain,
                "status": "failed",
                "error": str(e)
            })
    
    return results

# Run audit
domains = ["site1.com", "site2.com", "site3.com"]
results = audit_multiple_domains(domains)

# Export
with open("domain-audit.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
```

### Example 3: Continuous Monitoring

```python
from web_similarity_audit import Auditor
import time
import json

def monitor_site(domain: str, interval: int = 3600):
    """Monitor site for new duplicates every hour."""
    auditor = Auditor()
    previous_hashes = set()
    
    while True:
        results = auditor.audit_crawl(f"https://{domain}", max_pages=100)
        current_hashes = {p.content_hash for p in results.pages}
        
        # Check for new duplicates
        new_dupes = [
            p for p in results.high_priority_pairs
            if p.url_a not in previous_hashes or p.url_b not in previous_hashes
        ]
        
        if new_dupes:
            # Alert
            alert_data = {
                "timestamp": time.time(),
                "domain": domain,
                "new_duplicates": len(new_dupes),
                "pairs": [{"a": p.url_a, "b": p.url_b} for p in new_dupes]
            }
            print(json.dumps(alert_data))
        
        previous_hashes = current_hashes
        time.sleep(interval)

monitor_site("example.com")
```

## API Stability

- **Stable APIs** (won't change without major version bump):
  - `Auditor` class and its methods
  - `AuditResults` structure
  - Core data classes (`PageInfo`, `SimilarityPair`, etc.)

- **Experimental APIs** (may change in minor versions):
  - `AsyncAuditor`
  - Lower-level APIs (`Fetcher`, `Extractor`, etc.)
  - Configuration file formats

- **Internal APIs** (may change at any time):
  - Anything prefixed with `_`
  - Modules not documented here

## Migration Guides

### From v0.1 to v0.2

Changes in v0.2:
- Added `block_overlap` metric
- Changed threshold logic to OR instead of AND
- Added `trigger_reason` field to pairs

Update code:
```python
# v0.1
if pair.tfidf >= 0.85 and pair.jaccard >= 0.25:
    handle_duplicate(pair)

# v0.2
if pair.priority == "P1":
    handle_duplicate(pair)
    print(f"Reason: {pair.trigger_reason}")
```

## Support

- API Documentation: https://web-similarity-audit.readthedocs.io/
- Examples: https://github.com/wowayou/web-similarity-audit/tree/main/examples
- Issues: https://github.com/wowayou/web-similarity-audit/issues
