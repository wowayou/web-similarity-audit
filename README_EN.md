# Web Similarity Audit

A command-line tool for detecting duplicate and near-duplicate content across web pages, inspired by Screaming Frog's Near Duplicates feature.

## Features

### Dual Operating Modes

- **Site Crawl Mode**: Automatically discover and crawl all pages within a domain
- **URL List Mode**: Audit specific pages via command-line arguments or CSV file

### Four-Signal Similarity Detection

- **SHA-256**: Exact duplicate detection
- **n-gram Jaccard**: Character-level overlap
- **TF-IDF Cosine**: Topic similarity
- **Block Overlap**: Paragraph-level copying (catches paraphrased duplicates)

### Engineering Excellence

- ✅ Explicit failure reporting when content extraction fails
- ✅ Raw and template-removed dual-view comparison
- ✅ Intelligent content extraction powered by trafilatura
- ✅ SSRF protection, rate limiting, and concurrency control
- ✅ Cross-platform support (Linux/Windows/macOS)

## Quick Start

### Installation

```bash
cd ~/Dev/my-projects/web-similarity-audit
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

### Usage

```bash
# Audit entire website
web-similarity-audit --crawl https://example.com --max-pages 50

# Audit specific URLs
web-similarity-audit url1 url2 url3

# Use CSV input
web-similarity-audit urls.csv

# View results
cat audit-results/report.md
```

## Output Files

```
audit-results/
├── report.md          # Human-readable report
├── pairs.csv          # All page pairs with similarity scores
├── full_data.json     # Complete audit data
└── pages.json         # Per-page extraction status
```

## Example Output

### report.md

```markdown
## P1 - High Similarity Pairs

### Pair 1: Duplicate Detection

**URL 1**: https://example.com/product-a
**URL 2**: https://example.com/product-a-copy

**Trigger**: sha256_match
**Confidence**: Very High

Raw similarity:
- SHA-256: MATCH (identical)
- TF-IDF: 1.000
- Jaccard: 1.000
- Block overlap: 1.000
```

### pairs.csv

```csv
url1,url2,priority,trigger_reason,sha256_match,tfidf_raw,jaccard_raw,block_overlap_raw
https://example.com/p1,https://example.com/p2,P1,sha256_match,True,1.000,1.000,1.000
https://example.com/p3,https://example.com/p4,P1,block_overlap_raw≥0.70,False,0.782,0.312,0.750
```

## Comparison with Commercial Tools

| Feature | Screaming Frog | Sitebulb | web-similarity-audit |
|---------|----------------|----------|---------------------|
| Price | $259/year | $35/month | Free (MIT) |
| Site Crawling | ✓ | ✓ | ✓ |
| Near Duplicates | ✓ | ✓ | ✓ (4 signals) |
| CI Integration | ✗ | ✗ | ✓ |
| Explainability | Medium | Medium | High |
| Explicit Failures | ✗ | ✗ | ✓ |

## Use Cases

### SEO Consulting

```bash
web-similarity-audit --crawl https://client-site.com --max-pages 100
# Deliverables: report.md, pairs.csv, full_data.json
```

### CI Integration

```yaml
- name: Check for duplicate content
  run: |
    web-similarity-audit --crawl https://staging.example.com --max-pages 50
    if [ $(jq '[.pairs[] | select(.priority == "P1")] | length' audit-results/full_data.json) -gt 0 ]; then
      echo "Duplicate content detected!"
      exit 1
    fi
```

### Site Migration Validation

```bash
# Before migration
web-similarity-audit --crawl https://old-site.com --max-pages 200
mv audit-results audit-before

# After migration
web-similarity-audit --crawl https://new-site.com --max-pages 200
mv audit-results audit-after

# Compare
diff <(jq -S . audit-before/full_data.json) <(jq -S . audit-after/full_data.json)
```

## Performance

| Pages | Pairs | Calculation* | Total** |
|-------|-------|--------------|---------|
| 10    | 45    | ~0.5s        | ~6s     |
| 50    | 1,225 | ~2s          | ~27s    |
| 100   | 4,950 | ~8s          | ~58s    |
| 200   | 19,900| ~30s         | ~130s   |

\* Similarity calculation phase (local only)  
\*\* Including fetch (2 rps/host, 4 concurrent)

## Architecture

```
src/web_similarity_audit/
├── cli.py          # Command-line interface
├── crawler.py      # Website crawler
├── fetcher.py      # HTTP client + SSRF protection
├── extractor.py    # Content extraction
├── similarity.py   # Four-signal similarity
├── template.py     # Template detection
├── reporter.py     # Output generation
└── models.py       # Data models
```

## Testing

```bash
pytest tests/ -v

# 16 tests, all passing
tests/test_basic.py           # Core functionality
tests/test_crawler.py         # Crawler logic
tests/test_edge_cases.py      # Edge cases
tests/test_integration.py     # End-to-end
```

## Known Limitations

- **Page limit**: 200 (O(n²) complexity)
- **No JS rendering**: Won't find links in SPAs
- **Basic robots.txt**: Simplified implementation
- **Basic SSRF protection**: Doesn't cover DNS rebinding

## Roadmap

### M1 (Current)
- ✅ Site crawling mode
- ✅ Four-signal detection
- ✅ Cross-platform CLI

### M2 (Future)
- [ ] Publish to PyPI
- [ ] sitemap.xml support
- [ ] MinHash/LSH for >200 pages
- [ ] Playwright JS rendering
- [ ] Web UI

## License

MIT License - See [LICENSE](LICENSE) for details.

## Documentation

- [README.md](README.md) - Main documentation (Chinese)
- [DEMO.md](DEMO.md) - Quick demo
- [DELIVERY_SUMMARY.md](DELIVERY_SUMMARY.md) - Complete delivery summary
- [examples/](examples/) - Code examples

## Credits

Built with:
- [httpx](https://www.python-httpx.org/) - HTTP client
- [trafilatura](https://trafilatura.readthedocs.io/) - Content extraction
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [lxml](https://lxml.de/) - XML/HTML processing

## Support

For questions or issues, check the documentation or create an issue in the repository.
