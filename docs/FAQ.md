# Frequently Asked Questions

## General Questions

### What is this tool for?

This tool detects duplicate and near-duplicate web pages. It's designed for SEO professionals who need to:
- Audit websites for duplicate content
- Find thin pages with similar content
- Identify paraphrased or template-based duplicates
- Get explainable, reproducible results

### How is this different from Screaming Frog?

| Feature | Screaming Frog | Web Similarity Audit |
|---------|----------------|---------------------|
| Interface | GUI | CLI |
| Price | Paid (free up to 500 URLs) | Free & Open Source |
| CI/CD | No | Yes |
| Explainability | Single score | Multiple signals |
| Failure handling | Silent fallback | Explicit failure |
| Reproducibility | Manual export | CSV/JSON fixtures |

**Use Screaming Frog if:** You want a comprehensive SEO tool with GUI.  
**Use this tool if:** You need explainable, reproducible audits in CI/CD or consulting deliverables.

### What does "explicit failure" mean?

When main content extraction fails, commercial tools often silently fall back to comparing the entire HTML (including navigation, footer). This causes false positives.

This tool **never** does that. If extraction fails, it:
1. Marks the page as `extraction_success: false`
2. Includes it in `extraction_failures` in the report
3. Still compares the page, but you know the results are less reliable

You can then decide to fix the extraction (add custom selectors) or exclude those pages.

### Does this use AI or LLMs?

**No.** This tool uses deterministic algorithms:
- SHA-256 hashing for exact matches
- Jaccard similarity with n-grams for phrase overlap
- TF-IDF cosine similarity for topic similarity
- Block-level overlap for paragraph duplication

This means:
- Results are reproducible
- No API costs
- Works offline
- Fast (O(n²) but deterministic)

### Can I use this for non-English sites?

**Yes.** The tool supports:
- CJK languages (Chinese, Japanese, Korean)
- Any language that uses spaces for word boundaries
- Custom n-gram sizes for different languages

However, TF-IDF is tuned for English. For CJK, consider:
- Relying more on block overlap and Jaccard
- Using a preprocessing step for word segmentation

## Installation & Setup

### How do I install this?

**Recommended (pipx):**
```bash
pipx install web-similarity-audit
```

**Alternative (pip):**
```bash
pip install web-similarity-audit
```

**From source:**
```bash
git clone https://github.com/wowayou/web-similarity-audit.git
cd web-similarity-audit
pip install -e .
```

### What Python version do I need?

Python 3.10 or later.

Check your version:
```bash
python3 --version
```

### Why does installation fail with "externally managed environment"?

This is a Python 3.11+ protection mechanism. Use `pipx` instead:

```bash
# Install pipx
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install the tool
pipx install web-similarity-audit
```

### Can I use this in Docker?

**Yes.** See [DEPLOYMENT.md](DEPLOYMENT.md) for Docker setup. Quick start:

```bash
docker build -t web-similarity-audit .
docker run --rm -v $(pwd)/audit-results:/results \
  web-similarity-audit --crawl https://example.com --output /results
```

## Usage Questions

### How do I audit a single website?

Use crawl mode:
```bash
web-similarity-audit --crawl https://example.com --max-pages 200
```

This will:
1. Crawl up to 200 pages
2. Extract main content from each
3. Compare all pairs
4. Generate reports in `audit-results/`

### How do I compare specific URLs?

Create a `urls.csv`:
```csv
https://example.com/page1
https://example.com/page2
https://example.com/page3
```

Run:
```bash
web-similarity-audit urls.csv
```

### What if the audit crashes?

Use resume mode:
```bash
web-similarity-audit --resume
```

This will:
1. Load state from `.audit-state.json`
2. Skip already-fetched pages
3. Continue from where it left off

The state file is automatically cleaned up on successful completion.

### How do I interpret the priority levels?

**P1 (High Priority)** - Likely duplicates requiring action:
- Very similar topic (TF-IDF ≥ 0.85) OR
- Many identical phrases (Jaccard ≥ 0.70) OR
- Exact content match (SHA-256)

**P2 (Moderate Priority)** - Worth reviewing:
- Somewhat similar topic (TF-IDF ≥ 0.60) OR
- Some shared phrases (Jaccard ≥ 0.40) OR
- Many duplicate blocks (Block overlap ≥ 0.60)

**P3 (Low Priority)** - FYI only

### How do I adjust the thresholds?

Currently, thresholds are hardcoded. Future versions will support:
```bash
web-similarity-audit --p1-tfidf 0.90 --p1-jaccard 0.75 urls.csv
```

For now, you can filter the results:
```bash
# Show only pairs with TF-IDF > 0.90
jq '.[] | select(.tfidf > 0.90)' audit-results/pairs.json
```

### What's the maximum number of pages?

**Default: 200 pages**

This is because similarity checking is O(n²):
- 200 pages = 19,900 comparisons (~5-10 seconds)
- 500 pages = 124,750 comparisons (~30-60 seconds)
- 1000 pages = 499,500 comparisons (~2-5 minutes)

You can increase this:
```bash
web-similarity-audit --crawl https://example.com --max-pages 1000
```

For very large sites (>1000 pages), consider:
- Crawling in batches (by subdirectory)
- Using `--follow-external=false` to skip external links
- Future versions will use MinHash/LSH for O(n log n)

## Technical Questions

### How does content extraction work?

1. **Fetch HTML** via httpx
2. **Try trafilatura** for main content extraction
3. **Fall back to heuristics** if trafilatura fails:
   - Look for `<main>` tag
   - Look for `<article>` tag
   - Look for `[role="main"]` attribute
4. **Mark as failed** if all heuristics fail
5. **Never** silently use full HTML

The extraction method is recorded in `pages.json`:
```json
{
  "url": "https://example.com/page1",
  "extraction_success": true,
  "extraction_method": "trafilatura"
}
```

### What is template detection?

Many pages share common elements (navigation, footer, sidebar). Comparing these creates false positives.

The tool:
1. Splits each page into normalized blocks (paragraphs)
2. Finds blocks that appear in ≥60% of pages
3. Marks these as "template blocks"
4. Generates two views:
   - **Original**: All content included
   - **Template-removed**: Common blocks excluded

You can adjust the threshold:
```bash
web-similarity-audit --template-threshold 0.8 urls.csv
```

### How does SSRF protection work?

The tool blocks private IP addresses to prevent Server-Side Request Forgery:

**Blocked ranges:**
- RFC 1918: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- RFC 4193: `fc00::/7`
- Localhost: `127.0.0.0/8`, `::1`
- Link-local: `169.254.0.0/16`, `fe80::/10`
- Multicast and others

**How it works:**
1. DNS resolution happens first
2. Resolved IP is checked against blocked ranges
3. Connection is rejected if IP is private

This prevents attacks like:
```bash
# Attacker tries to scan internal network
web-similarity-audit http://169.254.169.254/latest/meta-data/
# ❌ Blocked: 169.254.169.254 is link-local
```

### What about rate limiting?

The tool uses a **token bucket** algorithm:

**Per-host rate limiting:**
- Default: 2 requests/second per host
- Configurable: `--per-host-rate N`
- Prevents accidental DoS

**Concurrency limiting:**
- Default: 4 concurrent requests total
- Configurable: `--concurrency N`
- Prevents overwhelming your network

Example:
```bash
# More aggressive (8 concurrent, 1 req/s per host)
web-similarity-audit --crawl https://example.com --concurrency 8 --per-host-rate 1.0
```

### Why no authentication support?

**By design.** This tool audits public web pages only.

**Reasons:**
1. **Security**: Storing credentials in CLI tools is risky
2. **Scope**: SEO audits target public pages
3. **Complexity**: Auth adds cookie/session/token management

**Workarounds:**
1. Use a proxy with auth built-in
2. Run the tool behind a VPN with access
3. Export authenticated URLs to CSV and fetch manually

### Can I use this programmatically?

**Yes.** The tool provides a Python API:

```python
from web_similarity_audit import Auditor, AuditConfig

config = AuditConfig(
    concurrency=8,
    per_host_rate=2.0,
    timeout=30
)

auditor = Auditor(config)
results = auditor.audit_crawl("https://example.com", max_pages=200)

# Access results
for pair in results.high_priority_pairs:
    print(f"{pair.url_a} <-> {pair.url_b}: {pair.tfidf:.2f}")
```

See [API.md](API.md) for full documentation.

## Troubleshooting

### Error: "Need at least 2 URLs"

You need at least 2 URLs to compare. Either:
- Provide a CSV with ≥2 URLs
- Use `--crawl` mode to discover URLs automatically

### Error: "Connection timeout"

Increase the timeout:
```bash
web-similarity-audit --timeout 60 urls.csv
```

Or check your network connection.

### Error: "Too many requests"

You're hitting rate limits. Reduce the rate:
```bash
web-similarity-audit --per-host-rate 0.5 urls.csv
```

### Error: "SSRF protection: blocked private IP"

You're trying to fetch from a private IP. This is blocked by design.

If you need to audit internal sites:
- Run the tool from inside your network
- Disable SSRF protection (requires code modification, not recommended)

### Output is empty or has few comparisons

**Check extraction success:**
```bash
jq '.summary.extraction_success_rate' audit-results/pages.json
```

If extraction success is low (<50%), the tool found little main content to compare.

**Solutions:**
1. Check if the site is JavaScript-heavy (tool can't execute JS)
2. Add custom CSS selectors for main content
3. Review `extraction_failures` in report.md

### TF-IDF and Jaccard are both low, but pages look similar

This often happens when:
1. **Images/videos**: Tool only compares text
2. **Client-side JS**: Content loaded after page load
3. **Different languages**: Same content, different language
4. **Paraphrasing**: Heavy rewording changes both signals

**Solutions:**
- Check block overlap (catches paraphrasing better)
- Use SequenceMatcher for detailed diffing on suspected pairs
- Future versions will have better paraphrase detection

### How do I debug why two pages matched as P1?

Check the `trigger_reason` column in `pairs.csv`:

```csv
url_a,url_b,priority,trigger_reason
https://a.com,https://b.com,P1,tfidf>=0.85 OR jaccard>=0.70
```

This tells you which threshold was crossed.

For detailed analysis:
```python
from web_similarity_audit import SimilarityChecker

checker = SimilarityChecker()
metrics = checker.compute_similarity(text1, text2)
print(f"TF-IDF: {metrics['tfidf']:.3f}")
print(f"Jaccard: {metrics['jaccard']:.3f}")
print(f"Block overlap: {metrics['block_overlap']:.3f}")
```

## Performance

### How long does an audit take?

**Rules of thumb:**
- Crawling: ~0.5-1 second per page (network-bound)
- Extraction: ~0.1 second per page (CPU-bound)
- Comparison: ~0.0001 second per pair (CPU-bound)

**Examples:**
- 50 pages: ~30-60 seconds (mostly crawling)
- 200 pages: ~2-4 minutes (mostly crawling)
- 500 pages: ~5-10 minutes (crawling + comparison)

### How do I speed it up?

**For crawling:**
```bash
# Increase concurrency and rate
web-similarity-audit --crawl https://example.com \
  --concurrency 10 --per-host-rate 5.0
```

**For comparison:**
- Use CSV input (skip crawling)
- Reduce `--max-pages`
- Future: MinHash will make this O(n log n)

### Can I run this on a Raspberry Pi?

**Yes**, but it will be slower. The tool is CPU-bound for comparisons.

**Recommendations:**
- Use `--max-pages 100` or less
- Reduce `--concurrency` to 2
- Expect 2-3x longer runtime

## Integration

### How do I use this in CI/CD?

**Example GitHub Actions:**
```yaml
- name: Install auditor
  run: pipx install web-similarity-audit

- name: Run audit
  run: web-similarity-audit urls.csv

- name: Check for duplicates
  run: |
    P1_COUNT=$(jq '.summary.p1_count' audit-results/pages.json)
    if [ "$P1_COUNT" -gt 0 ]; then
      echo "Found $P1_COUNT high-priority duplicates"
      exit 1
    fi

- name: Upload results
  uses: actions/upload-artifact@v3
  with:
    name: audit-results
    path: audit-results/
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full examples.

### Can I compare output across runs?

**Yes.** The output is deterministic (same inputs → same outputs).

**Compare runs:**
```bash
# Run 1
web-similarity-audit urls.csv
mv audit-results audit-results-run1

# Run 2 (after site changes)
web-similarity-audit urls.csv
mv audit-results audit-results-run2

# Compare
diff <(jq '.summary' audit-results-run1/pages.json) \
     <(jq '.summary' audit-results-run2/pages.json)
```

### How do I integrate with Screaming Frog?

Export URLs from Screaming Frog:
1. Export → Response Codes → HTML
2. Save as `screaming-frog-urls.csv`
3. Run: `web-similarity-audit screaming-frog-urls.csv`

### Can I use this with Google Sheets?

**Yes.**

1. Export URLs from Sheets as CSV
2. Run audit: `web-similarity-audit urls.csv`
3. Import `audit-results/pairs.csv` back into Sheets

**Tip:** Use `=IMPORTDATA()` to auto-refresh (requires hosted CSV).

## Contributing

### How can I contribute?

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Setting up development environment
- Code style guidelines
- Testing requirements
- Pull request process

### What's the roadmap?

See [TODO.md](../TODO.md) for planned features:
- MinHash/LSH for O(n log n) comparison
- Canonical and hreflang validation
- REST API and Web UI
- Incremental mode (only compare changed pages)

### How do I report a bug?

Open an issue on GitHub:
- Use the bug report template
- Include OS, Python version, package version
- Provide reproduction steps
- Attach error logs

### How do I request a feature?

Open an issue on GitHub:
- Use the feature request template
- Describe your use case
- Explain why existing features don't work

### Can I sponsor development?

Yes! See [FUNDING.yml](.github/FUNDING.yml) for sponsorship options.

## Comparison with Alternatives

### vs. Screaming Frog

| Feature | Screaming Frog | This Tool |
|---------|----------------|-----------|
| Price | £149/year | Free |
| Interface | GUI | CLI |
| Explainability | Single score | Multiple signals |
| CI/CD | Manual | Native |
| Max pages (free) | 500 | Unlimited |
| Content extraction | Heuristics | trafilatura |
| Failure handling | Silent fallback | Explicit |

### vs. Sitebulb

| Feature | Sitebulb | This Tool |
|---------|----------|-----------|
| Price | £35-£275/month | Free |
| Interface | GUI + reports | CLI + reports |
| Visualizations | Excellent | Minimal |
| Reproducibility | Manual | Automatic |

### vs. Siteliner

| Feature | Siteliner | This Tool |
|---------|-----------|-----------|
| Price | Free (250 pages) | Free (unlimited) |
| Interface | Web UI | CLI |
| Offline | No | Yes |
| CI/CD | No | Yes |

### vs. Custom Scripts

| Feature | Custom Script | This Tool |
|---------|--------------|-----------|
| Time to build | Days-weeks | Minutes (install) |
| Maintenance | You | Community |
| Testing | You | CI + fixtures |
| Documentation | You | Comprehensive |

## License & Legal

### What's the license?

**MIT License** - free for commercial and personal use.

See [LICENSE](../LICENSE) for full text.

### Can I use this commercially?

**Yes.** The MIT license allows:
- Commercial use
- Modification
- Distribution
- Private use

### Do I need to credit you?

Not required, but appreciated! Mention in your reports:
```
Duplicate content audit performed with web-similarity-audit
https://github.com/wowayou/web-similarity-audit
```

### Is there a warranty?

**No.** Per MIT license, the software is provided "as-is" without warranty.

### What about the dependencies?

All dependencies are also open source:
- httpx: BSD License
- beautifulsoup4: MIT License
- lxml: BSD License
- trafilatura: Apache 2.0 License

---

**Still have questions?** Open a [discussion](https://github.com/wowayou/web-similarity-audit/discussions) or [issue](https://github.com/wowayou/web-similarity-audit/issues).
