# Examples

This directory contains practical examples for using web-similarity-audit in different scenarios.

## Files

### `basic_usage.sh`
Bash script demonstrating common CLI usage patterns:
- Compare specific URLs
- Read from CSV
- Crawl websites
- Resume interrupted audits
- Filter results by priority

Run:
```bash
./examples/basic_usage.sh
```

### `ci_integration.yml`
GitHub Actions workflow example showing:
- Scheduled weekly audits
- Upload results as artifacts
- Comment on PRs with audit results
- Fail CI if too many duplicates found

Use this as a template for your `.github/workflows/` directory.

### `seo_workflow.py`
Python script demonstrating programmatic usage:
- Call the tool from Python code
- Parse JSON output
- Generate custom reports
- Integrate with other tools

Run:
```bash
python examples/seo_workflow.py
```

## Use Cases

### 1. Pre-deployment Check
Run before deploying to production:
```bash
web-similarity-audit --crawl https://staging.example.com --max-pages 100
if [ $(grep -c ",P1," audit-results/pairs.csv) -gt 0 ]; then
  echo "❌ Found duplicate content, blocking deploy"
  exit 1
fi
```

### 2. Competitor Analysis
Compare your site with competitors:
```bash
# Create CSV with your and competitor URLs
cat > comparison.csv << 'CSV'
url
https://yoursite.com/product-a
https://competitor.com/product-a
https://yoursite.com/product-b
https://competitor.com/product-b
CSV
web-similarity-audit --csv comparison.csv
```

### 3. Multi-site Governance
Audit multiple brand sites for content leakage:
```bash
for site in site1.com site2.com site3.com; do
  web-similarity-audit --crawl https://$site --output audit-$site
done
```

### 4. Migration Validation
Verify content integrity after migration:
```bash
# Before migration
web-similarity-audit --crawl https://old-site.com --output before

# After migration
web-similarity-audit --crawl https://new-site.com --output after

# Compare page counts and duplicate patterns
diff before/report.md after/report.md
```

### 5. Content Audit Report for Client
Generate evidence-based report:
```bash
web-similarity-audit --crawl https://client-site.com --max-pages 500
# Results in audit-results/ can be zipped and delivered
tar -czf client-audit-$(date +%Y%m%d).tar.gz audit-results/
```

## Integration Examples

### Python
```python
import subprocess
import json

result = subprocess.run([
    'web-similarity-audit',
    '--crawl', 'https://example.com',
    '--max-pages', '100'
], check=True)

with open('audit-results/pages.json') as f:
    pages = json.load(f)
    
print(f"Audited {len(pages)} pages")
```

### Shell Script with Error Handling
```bash
#!/bin/bash
set -e

if ! command -v web-similarity-audit &> /dev/null; then
    echo "Installing web-similarity-audit..."
    pipx install web-similarity-audit
fi

web-similarity-audit --crawl "$1" --max-pages 200 || {
    echo "Audit failed with code $?"
    exit 1
}

echo "✅ Audit complete. Results in audit-results/"
```

### Cron Job
```bash
# Add to crontab: run every Sunday at 2 AM
0 2 * * 0 cd /path/to/project && /usr/local/bin/web-similarity-audit --crawl https://example.com --output /var/audits/$(date +\%Y\%m\%d)
```

## Tips

1. **Start small**: Test with `--max-pages 50` first, then scale up
2. **Use resume**: For large sites, use `--resume` to recover from interruptions
3. **Filter P1 only**: Focus on high-priority pairs with `grep ",P1," pairs.csv`
4. **Automate**: Set up weekly CI audits to catch new duplicates early
5. **Compare before/after**: Save results before making bulk changes

## Questions?

See the main [README](../README.md) or open an [issue](https://github.com/wowayou/web-similarity-audit/issues).
