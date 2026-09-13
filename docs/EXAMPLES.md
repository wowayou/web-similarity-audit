# Usage Examples

This document provides real-world examples of using Web Similarity Audit in various scenarios.

## Table of Contents

- [Basic Usage](#basic-usage)
- [SEO Auditing](#seo-auditing)
- [CI/CD Integration](#cicd-integration)
- [Consulting Deliverables](#consulting-deliverables)
- [Multi-Site Management](#multi-site-management)
- [Advanced Filtering](#advanced-filtering)
- [Python API Usage](#python-api-usage)

## Basic Usage

### Compare Two Pages

```bash
web-similarity-audit https://example.com/page1 https://example.com/page2
```

### Compare Multiple Specific URLs

Create `urls.csv`:
```csv
https://example.com/product-a
https://example.com/product-b
https://example.com/product-c
https://example.com/product-d
```

Run:
```bash
web-similarity-audit urls.csv
```

### Crawl Entire Website

```bash
web-similarity-audit --crawl https://example.com --max-pages 200
```

### Crawl with Custom Settings

```bash
web-similarity-audit --crawl https://example.com \
  --max-pages 500 \
  --concurrency 8 \
  --per-host-rate 3.0 \
  --timeout 60 \
  --template-threshold 0.7 \
  --output my-audit-results
```

## SEO Auditing

### Audit Product Pages for Duplicates

```bash
# Export product URLs from your CMS or sitemap
cat > product-urls.csv << EOF
https://mysite.com/products/widget-blue
https://mysite.com/products/widget-red
https://mysite.com/products/widget-green
https://mysite.com/products/widget-premium
EOF

# Run audit
web-similarity-audit product-urls.csv

# Check for high-priority duplicates
jq '.summary.p1_count' audit-results/pages.json
```

### Find Thin Content

```bash
web-similarity-audit --crawl https://mysite.com --max-pages 200

# Filter pages with low character count
jq '.pages[] | select(.char_count < 500) | {url, char_count}' \
  audit-results/pages.json
```

### Identify Template Pages

```bash
web-similarity-audit --crawl https://mysite.com --max-pages 200

# Check template detection results
jq '.template_detection' audit-results/pages.json

# View pairs with high similarity after template removal
csvcut -c url_a,url_b,tfidf,jaccard,block_overlap audit-results/pairs.csv | \
  csvgrep -c tfidf -m 0.8 | \
  csvlook
```

### Compare Before/After Site Migration

```bash
# Before migration
web-similarity-audit --crawl https://old-site.com --max-pages 200
mv audit-results audit-before

# After migration
web-similarity-audit --crawl https://new-site.com --max-pages 200
mv audit-results audit-after

# Compare summaries
diff <(jq '.summary' audit-before/pages.json) \
     <(jq '.summary' audit-after/pages.json)

# Find new duplicates
comm -13 \
  <(jq -r '.pages[].content_hash' audit-before/pages.json | sort) \
  <(jq -r '.pages[].content_hash' audit-after/pages.json | sort)
```

### Audit Multilingual Site

```bash
# Crawl each language separately
web-similarity-audit --crawl https://example.com/en --max-pages 200
mv audit-results audit-en

web-similarity-audit --crawl https://example.com/zh --max-pages 200
mv audit-results audit-zh

# Compare duplicate rates
echo "English P1 duplicates: $(jq '.summary.p1_count' audit-en/pages.json)"
echo "Chinese P1 duplicates: $(jq '.summary.p1_count' audit-zh/pages.json)"
```

## CI/CD Integration

### GitHub Actions - Block on Duplicates

`.github/workflows/audit.yml`:
```yaml
name: Content Audit

on:
  push:
    branches: [main]
  pull_request:

jobs:
  audit:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
    
    - name: Install auditor
      run: pipx install web-similarity-audit
    
    - name: Run audit
      run: web-similarity-audit urls.csv
    
    - name: Check for duplicates
      run: |
        P1_COUNT=$(jq '.summary.p1_count' audit-results/pages.json)
        if [ "$P1_COUNT" -gt 5 ]; then
          echo "❌ Found $P1_COUNT high-priority duplicates (threshold: 5)"
          jq -r '.pages[] | select(.priority == "P1") | 
            "\(.url_a) <-> \(.url_b): \(.trigger_reason)"' \
            audit-results/pairs.csv
          exit 1
        fi
        echo "✅ Duplicate check passed ($P1_COUNT P1 duplicates)"
    
    - name: Upload audit results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: audit-results
        path: audit-results/
```

### GitLab CI - Weekly Scheduled Audit

`.gitlab-ci.yml`:
```yaml
audit:
  image: python:3.10
  script:
    - pip install web-similarity-audit
    - web-similarity-audit --crawl https://example.com --max-pages 200
    - |
      P1_COUNT=$(jq '.summary.p1_count' audit-results/pages.json)
      echo "High-priority duplicates: $P1_COUNT"
  artifacts:
    paths:
      - audit-results/
    expire_in: 30 days
  rules:
    - if: '$CI_PIPELINE_SOURCE == "schedule"'
```

### Jenkins - Compare Production vs Staging

```groovy
pipeline {
    agent any
    
    stages {
        stage('Install') {
            steps {
                sh 'pip install web-similarity-audit'
            }
        }
        
        stage('Audit Production') {
            steps {
                sh 'web-similarity-audit --crawl https://prod.example.com --output prod-audit'
            }
        }
        
        stage('Audit Staging') {
            steps {
                sh 'web-similarity-audit --crawl https://staging.example.com --output staging-audit'
            }
        }
        
        stage('Compare') {
            steps {
                script {
                    def prodP1 = sh(
                        script: "jq '.summary.p1_count' prod-audit/pages.json",
                        returnStdout: true
                    ).trim().toInteger()
                    
                    def stagingP1 = sh(
                        script: "jq '.summary.p1_count' staging-audit/pages.json",
                        returnStdout: true
                    ).trim().toInteger()
                    
                    if (stagingP1 > prodP1) {
                        error("Staging has more duplicates than production ($stagingP1 vs $prodP1)")
                    }
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: '*/audit-results/**'
        }
    }
}
```

## Consulting Deliverables

### Create Reproducible Audit Package

```bash
#!/bin/bash
# audit-client-site.sh

CLIENT="acme-corp"
DATE=$(date +%Y%m%d)
OUTPUT_DIR="${CLIENT}-audit-${DATE}"

# Run audit
web-similarity-audit --crawl https://client-site.com \
  --max-pages 200 \
  --output "$OUTPUT_DIR"

# Create README
cat > "$OUTPUT_DIR/README.txt" << EOF
Content Similarity Audit for ${CLIENT}
Date: $(date +"%Y-%m-%d %H:%M:%S")

This audit was performed using web-similarity-audit v$(web-similarity-audit --version)

To reproduce this audit:
1. Install: pipx install web-similarity-audit
2. Run: web-similarity-audit --resume

Files included:
- pages.json: Full page metadata and extraction results
- pairs.csv: All similarity comparisons with metrics
- report.md: Human-readable summary
- .audit-state.json: Reproducibility data

High-priority findings: $(jq '.summary.p1_count' "$OUTPUT_DIR/pages.json")
Total pages analyzed: $(jq '.summary.total_pages' "$OUTPUT_DIR/pages.json")

For questions, see: https://github.com/wowayou/web-similarity-audit
EOF

# Create tarball
tar -czf "${OUTPUT_DIR}.tar.gz" "$OUTPUT_DIR"

echo "✅ Audit package created: ${OUTPUT_DIR}.tar.gz"
echo "   Size: $(du -h "${OUTPUT_DIR}.tar.gz" | cut -f1)"
echo "   P1 issues: $(jq '.summary.p1_count' "$OUTPUT_DIR/pages.json")"
```

### Generate Executive Summary

```bash
# audit-summary.sh

OUTPUT_DIR="audit-results"

cat > executive-summary.md << EOF
# Content Audit Executive Summary

**Date**: $(date +"%B %d, %Y")
**Site**: $(jq -r '.pages[0].url' $OUTPUT_DIR/pages.json | sed 's|/.*||')
**Pages Analyzed**: $(jq '.summary.total_pages' $OUTPUT_DIR/pages.json)

## Key Findings

### Duplicate Content Risk

- **High Priority (P1)**: $(jq '.summary.p1_count' $OUTPUT_DIR/pages.json) page pairs
- **Moderate Priority (P2)**: $(jq '.summary.p2_count' $OUTPUT_DIR/pages.json) page pairs
- **Low Priority (P3)**: $(jq '.summary.p3_count' $OUTPUT_DIR/pages.json) page pairs

### Content Extraction

- **Success Rate**: $(jq '.summary.extraction_success_rate * 100' $OUTPUT_DIR/pages.json | xargs printf "%.1f%%")
- **Failed Extractions**: $(jq '.summary.total_pages - (.summary.extraction_success_rate * .summary.total_pages | floor)' $OUTPUT_DIR/pages.json)

### Top Duplicate Pairs

$(jq -r '.[] | select(.priority == "P1") | 
  "- **\(.url_a)** vs **\(.url_b)**\n  - TF-IDF: \(.tfidf | . * 100 | round / 100)\n  - Jaccard: \(.jaccard | . * 100 | round / 100)\n  - Reason: \(.trigger_reason)\n"' \
  $OUTPUT_DIR/pairs.csv | head -n 20)

## Recommendations

1. Review all P1 duplicates for consolidation or canonical tags
2. Investigate failed content extractions
3. Monitor P2 duplicates for future action

## Technical Details

Full audit results available in:
- \`pages.json\` - Complete page metadata
- \`pairs.csv\` - All similarity comparisons
- \`report.md\` - Detailed findings

Generated with: https://github.com/wowayou/web-similarity-audit
EOF

cat executive-summary.md
```

## Multi-Site Management

### Audit Multiple Client Sites

```bash
#!/bin/bash
# audit-all-clients.sh

CLIENTS=(
  "https://client1.com"
  "https://client2.com"
  "https://client3.com"
)

for site in "${CLIENTS[@]}"; do
  domain=$(echo "$site" | sed 's|https://||' | sed 's|/.*||')
  echo "🔍 Auditing $domain..."
  
  web-similarity-audit --crawl "$site" \
    --max-pages 100 \
    --output "audit-$domain"
  
  p1_count=$(jq '.summary.p1_count' "audit-$domain/pages.json")
  echo "   P1 duplicates: $p1_count"
done

# Generate comparison report
cat > multi-site-summary.csv << EOF
Site,Total Pages,P1 Duplicates,P2 Duplicates,Extraction Success Rate
EOF

for site in "${CLIENTS[@]}"; do
  domain=$(echo "$site" | sed 's|https://||' | sed 's|/.*||')
  jq -r --arg domain "$domain" \
    '"\($domain),\(.summary.total_pages),\(.summary.p1_count),\(.summary.p2_count),\(.summary.extraction_success_rate)"' \
    "audit-$domain/pages.json" >> multi-site-summary.csv
done

column -t -s, multi-site-summary.csv
```

### Monitor Site Changes Over Time

```bash
#!/bin/bash
# monitor-changes.sh

SITE="https://example.com"
HISTORY_DIR="audit-history"
DATE=$(date +%Y%m%d)

mkdir -p "$HISTORY_DIR"

# Run audit
web-similarity-audit --crawl "$SITE" \
  --max-pages 200 \
  --output "$HISTORY_DIR/$DATE"

# Compare with previous audit
PREV_AUDIT=$(ls -1d "$HISTORY_DIR"/*/ | tail -n 2 | head -n 1)

if [ -n "$PREV_AUDIT" ]; then
  echo "Comparing with previous audit: $PREV_AUDIT"
  
  PREV_P1=$(jq '.summary.p1_count' "$PREV_AUDIT/pages.json")
  CURR_P1=$(jq '.summary.p1_count' "$HISTORY_DIR/$DATE/pages.json")
  
  DIFF=$((CURR_P1 - PREV_P1))
  
  if [ $DIFF -gt 0 ]; then
    echo "⚠️  P1 duplicates increased by $DIFF"
  elif [ $DIFF -lt 0 ]; then
    echo "✅ P1 duplicates decreased by ${DIFF#-}"
  else
    echo "➡️  No change in P1 duplicates"
  fi
fi
```

## Advanced Filtering

### Find Exact Duplicates Only

```bash
web-similarity-audit urls.csv

# Extract exact matches (SHA-256)
jq -r '.[] | select(.sha256_match == true) | 
  "\(.url_a)\n\(.url_b)\n---"' audit-results/pairs.csv
```

### Find Paraphrased Content

```bash
# High TF-IDF but low Jaccard = paraphrasing
csvgrep -c tfidf -r "0\.[8-9].*" audit-results/pairs.csv | \
  csvgrep -c jaccard -r "0\.[0-4].*" | \
  csvcut -c url_a,url_b,tfidf,jaccard | \
  csvlook
```

### Find Template-Heavy Pages

```bash
# Pages where template removal greatly reduces similarity
awk -F, 'NR>1 && $4-$5>0.3 {print $1","$2","$4","$5}' audit-results/pairs.csv | \
  column -t -s,
```

### Export for Excel Analysis

```bash
web-similarity-audit urls.csv

# Convert to Excel-friendly format
csvcut -c url_a,url_b,priority,tfidf,jaccard,block_overlap,trigger_reason \
  audit-results/pairs.csv > duplicates-for-excel.csv

# Import into Excel/Google Sheets for pivot tables and filtering
```

## Python API Usage

### Basic Programmatic Audit

```python
from web_similarity_audit import Auditor

# Create auditor
auditor = Auditor(concurrency=8, per_host_rate=2.0)

# Audit from URL list
urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
]

results = auditor.audit_urls(urls)

# Access results
print(f"Total pages: {results.summary.total_pages}")
print(f"P1 duplicates: {results.summary.p1_count}")

for pair in results.high_priority_pairs:
    print(f"{pair.url_a} <-> {pair.url_b}")
    print(f"  TF-IDF: {pair.tfidf:.3f}")
    print(f"  Reason: {pair.trigger_reason}")
```

### Custom Threshold Analysis

```python
from web_similarity_audit import SimilarityChecker

checker = SimilarityChecker()

# Fetch and extract content (custom logic)
text1 = fetch_and_extract("https://example.com/page1")
text2 = fetch_and_extract("https://example.com/page2")

# Compute all metrics
metrics = checker.compute_similarity(text1, text2)

# Apply custom thresholds
if metrics['tfidf'] > 0.90 or metrics['block_overlap'] > 0.80:
    print("⚠️  Very high similarity detected")
    print(f"  TF-IDF: {metrics['tfidf']:.3f}")
    print(f"  Block overlap: {metrics['block_overlap']:.3f}")
```

### Batch Processing with Progress Tracking

```python
from web_similarity_audit import Auditor
from rich.progress import Progress

auditor = Auditor()

sites = [
    "https://client1.com",
    "https://client2.com",
    "https://client3.com"
]

results_map = {}

with Progress() as progress:
    task = progress.add_task("Auditing sites...", total=len(sites))
    
    for site in sites:
        progress.console.print(f"🔍 Auditing {site}")
        results = auditor.audit_crawl(site, max_pages=100)
        results_map[site] = results
        progress.advance(task)

# Generate summary
for site, results in results_map.items():
    print(f"{site}: {results.summary.p1_count} P1 duplicates")
```

### Integration with Pandas

```python
import pandas as pd
from web_similarity_audit import Auditor

auditor = Auditor()
results = auditor.audit_crawl("https://example.com", max_pages=200)

# Convert to DataFrame
pairs_df = pd.DataFrame([
    {
        'url_a': p.url_a,
        'url_b': p.url_b,
        'priority': p.priority,
        'tfidf': p.tfidf,
        'jaccard': p.jaccard,
        'block_overlap': p.block_overlap
    }
    for p in results.pairs
])

# Analyze with pandas
print(pairs_df.describe())
print(pairs_df.groupby('priority').size())

# Filter high-risk paraphrasing
paraphrased = pairs_df[
    (pairs_df['tfidf'] > 0.85) & 
    (pairs_df['jaccard'] < 0.40)
]
print(f"Paraphrased pairs: {len(paraphrased)}")
```

---

**More examples?** Check the [FAQ](FAQ.md) or open a [discussion](https://github.com/wowayou/web-similarity-audit/discussions).
