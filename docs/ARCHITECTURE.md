# Architecture

This document describes the internal architecture of web-similarity-audit.

## Overview

The tool follows a pipeline architecture with clear separation of concerns:

```
Input → Fetch → Extract → Analyze → Report → Output
```

## Module Structure

```
src/web_similarity_audit/
├── __init__.py           # Package entry point
├── __main__.py           # CLI entry point
├── cli.py                # Command-line interface
├── crawler.py            # Web crawling logic
├── fetcher.py            # HTTP fetching with SSRF protection
├── extractor.py          # Content extraction (trafilatura wrapper)
├── analyzer.py           # Similarity computation
├── reporter.py           # Output generation
├── template_detector.py  # Common block detection
└── utils.py              # Shared utilities
```

## Data Flow

### 1. Input Phase

**CSV Mode:**
```python
urls = parse_csv("urls.csv")  # List of URLs
```

**Crawl Mode:**
```python
urls = crawler.crawl(
    start_url="https://example.com",
    max_pages=200,
    follow_external=False
)
```

**Output:** List of URL strings

### 2. Fetch Phase

```python
pages = await fetcher.fetch_all(
    urls,
    concurrency=4,
    per_host_limit=2
)
```

**SSRF Protection:**
- DNS resolution before connection
- Block private IP ranges (RFC 1918, RFC 4193)
- Block localhost and link-local addresses

**Rate Limiting:**
- Per-host token bucket
- Configurable requests per second
- Automatic retry with exponential backoff

**Output:** List of `PageData` objects:
```python
@dataclass
class PageData:
    url: str
    html: str
    status_code: int
    headers: dict
    fetch_time: float
```

### 3. Extract Phase

```python
extracted = extractor.extract_all(pages)
```

**Process:**
1. Parse HTML with BeautifulSoup4
2. Try trafilatura extraction
3. Record extraction success/failure
4. Normalize text (NFKC, whitespace)
5. Compute SHA-256 hash

**Output:** List of `ExtractedPage` objects:
```python
@dataclass
class ExtractedPage:
    url: str
    content_hash: str
    raw_text: str           # Full page text
    main_content: str       # Extracted main content
    extraction_success: bool
    extraction_method: str  # "trafilatura", "fallback", etc.
    char_count: int
    word_count: int
```

### 4. Template Detection Phase

```python
common_blocks = template_detector.detect(
    extracted,
    threshold=0.6  # Appears in 60% of pages
)

for page in extracted:
    page.template_free_text = remove_blocks(
        page.main_content,
        common_blocks
    )
```

**Algorithm:**
1. Split each page into blocks (paragraphs)
2. Normalize blocks (whitespace, case)
3. Count block frequency across all pages
4. Mark blocks appearing in ≥60% as templates
5. Generate template-free view for each page

**Edge Case:** Skip if n < 5 pages (insufficient data)

### 5. Analysis Phase

```python
pairs = analyzer.compute_similarity(extracted)
```

**For each pair (page_a, page_b):**

1. **SHA-256 Match**
   ```python
   if page_a.content_hash == page_b.content_hash:
       return "P1", "sha256_match"
   ```

2. **N-gram Jaccard Similarity**
   ```python
   ngrams_a = set(trigrams(page_a.main_content))
   ngrams_b = set(trigrams(page_b.main_content))
   jaccard = len(ngrams_a & ngrams_b) / len(ngrams_a | ngrams_b)
   ```

3. **TF-IDF Cosine Similarity**
   ```python
   tfidf_a = compute_tfidf(page_a.main_content, all_pages)
   tfidf_b = compute_tfidf(page_b.main_content, all_pages)
   cosine = dot(tfidf_a, tfidf_b) / (norm(tfidf_a) * norm(tfidf_b))
   ```

4. **Block Overlap**
   ```python
   blocks_a = set(normalize_blocks(page_a.main_content))
   blocks_b = set(normalize_blocks(page_b.main_content))
   overlap = len(blocks_a & blocks_b) / min(len(blocks_a), len(blocks_b))
   ```

5. **Priority Assignment**
   ```python
   if tfidf >= 0.85 or jaccard >= 0.70:
       priority = "P1"
   elif tfidf >= 0.60 or jaccard >= 0.40 or block_overlap >= 0.60:
       priority = "P2"
   else:
       priority = "P3"
   ```

**Output:** List of `SimilarityPair` objects:
```python
@dataclass
class SimilarityPair:
    url_a: str
    url_b: str
    priority: str           # "P1", "P2", "P3"
    sha256_match: bool
    jaccard: float
    tfidf: float
    block_overlap: float
    trigger_reason: str     # "tfidf>=0.85 AND jaccard>=0.70"
```

### 6. Report Phase

```python
reporter.generate_all(
    pages=extracted,
    pairs=pairs,
    output_dir="audit-results"
)
```

**Generates three files:**

1. **pages.json** - Full page metadata
2. **pairs.csv** - Similarity pairs with scores
3. **report.md** - Human-readable summary

### 7. Output Phase

Write files to disk and print summary:
```
Completed in 55.28s
  P1 (high): 5
  P2 (moderate): 303
  P3 (low): 453

Reports written to: /path/to/audit-results
```

## Performance Considerations

### Time Complexity

- **Fetching**: O(n) with concurrency
- **Extraction**: O(n)
- **Template detection**: O(n × m) where m = avg blocks per page
- **Similarity**: O(n²) for all pairs
- **Overall**: O(n²) dominated by pairwise comparison

### Space Complexity

- **Page storage**: O(n × page_size)
- **TF-IDF vectors**: O(n × vocab_size)
- **Pairs**: O(n²) but only high-similarity pairs kept in memory

### Scalability Limits

Current implementation:
- **Max pages**: 200 (configurable)
- **Max pairs**: 19,900 (n=200)
- **Memory**: ~500MB for 200 pages

For larger sites (planned):
- **MinHash LSH**: Reduce comparisons to O(n log n)
- **Incremental mode**: Only compare changed pages
- **Streaming**: Don't load all pages in memory

## Error Handling

### Explicit Failures

The tool follows a "fail-fast" philosophy:

1. **Extraction failure**: Logged and reported, not silent
2. **Network errors**: Retried then recorded
3. **Invalid input**: Early validation with clear messages
4. **SSRF attempts**: Blocked with explicit error

### Exit Codes

- `0` - Success
- `1` - Input validation failure
- `2` - Fetch failure (all URLs failed)
- `3` - Processing failure (internal error)
- `4` - Output failure (disk full, permissions)

### Crash Recovery

State is saved incrementally:
```python
state = {
    "urls": discovered_urls,
    "fetched": list(fetched_pages),
    "config": {...},
    "timestamp": "2025-09-13T18:00:00Z"
}
save_state(".audit-state.json", state)
```

Resume with `--resume` flag:
```python
state = load_state(".audit-state.json")
remaining_urls = set(state["urls"]) - {p.url for p in state["fetched"]}
continue_audit(remaining_urls, state["fetched"], state["config"])
```

## Concurrency Model

Uses `asyncio` for I/O-bound operations:

```python
async def fetch_all(urls, concurrency=4):
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [fetch_one(url, semaphore) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

**Rate limiting per host:**
```python
class PerHostLimiter:
    def __init__(self, rps: float = 2.0):
        self.limiters = {}  # hostname -> TokenBucket
    
    async def acquire(self, url: str):
        host = urlparse(url).hostname
        if host not in self.limiters:
            self.limiters[host] = TokenBucket(rate=self.rps)
        await self.limiters[host].acquire()
```

## Testing Strategy

### Unit Tests
- Test each module in isolation
- Mock HTTP responses
- Test edge cases (empty pages, malformed HTML)

### Integration Tests
- End-to-end with fixtures
- Test actual HTTP fetching (local server)
- Verify output file formats

### Acceptance Tests
- Real-world site samples
- Compare against Screaming Frog results
- Verify no false positives/negatives

## Security Architecture

### SSRF Prevention

```python
def is_safe_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    return not (
        addr.is_private or
        addr.is_loopback or
        addr.is_link_local or
        addr.is_multicast
    )

# DNS resolution happens first
resolved_ip = socket.getaddrinfo(hostname, port)[0][4][0]
if not is_safe_ip(resolved_ip):
    raise SSRFError(f"Blocked private IP: {resolved_ip}")
```

### Input Validation

```python
def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme in ["http", "https"]:
        raise ValueError("Only HTTP/HTTPS allowed")
    if "@" in parsed.netloc:
        raise ValueError("Credentials in URL not allowed")
    return url
```

### Output Sanitization

```python
# CSV output uses proper escaping
csv.writer(f, quoting=csv.QUOTE_MINIMAL)

# Markdown output escapes special chars
def escape_markdown(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")
```

## Future Architecture Changes

### v0.3.0: Enhanced Paraphrase Detection
- Add sequence alignment (SequenceMatcher for top pairs)
- Paragraph-level similarity matrix

### v0.4.0: SEO-Specific Features
- Sitemap parsing (XML)
- Canonical link analysis
- Hreflang validation

### v0.5.0: Performance Optimization
- MinHash LSH for O(n log n) similarity
- Incremental audit mode (only changed pages)
- Parallel extraction with multiprocessing

### v1.0.0: API Server
- REST API with FastAPI
- Background job queue
- Database backend (SQLite/PostgreSQL)
- Web UI for results visualization

## References

- [Trafilatura Documentation](https://trafilatura.readthedocs.io/)
- [httpx Documentation](https://www.python-httpx.org/)
- [MinHash/LSH Theory](https://en.wikipedia.org/wiki/MinHash)
- [TF-IDF Explanation](https://en.wikipedia.org/wiki/Tf%E2%80%93idf)
