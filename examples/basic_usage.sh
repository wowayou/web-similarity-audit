#!/bin/bash
# Basic usage examples for web-similarity-audit

# Example 1: Compare two specific URLs
echo "Example 1: Compare two URLs"
web-similarity-audit \
  https://example.com/page1 \
  https://example.com/page2

# Example 2: Compare multiple URLs
echo -e "\nExample 2: Compare multiple URLs"
web-similarity-audit \
  https://example.com/page1 \
  https://example.com/page2 \
  https://example.com/page3 \
  https://example.com/page4

# Example 3: Read URLs from CSV
echo -e "\nExample 3: Read from CSV"
cat > urls.csv << 'CSV'
url
https://example.com/page1
https://example.com/page2
https://example.com/page3
CSV
web-similarity-audit --csv urls.csv
rm urls.csv

# Example 4: Crawl entire website (limited to 50 pages)
echo -e "\nExample 4: Crawl website"
web-similarity-audit --crawl https://example.com --max-pages 50

# Example 5: Crawl with custom settings
echo -e "\nExample 5: Crawl with custom settings"
web-similarity-audit \
  --crawl https://example.com \
  --max-pages 100 \
  --concurrency 8 \
  --per-host-limit 3.0 \
  --output my-audit-results

# Example 6: Resume interrupted audit
echo -e "\nExample 6: Resume interrupted audit"
# First run (simulate interruption with Ctrl+C)
web-similarity-audit --crawl https://example.com --max-pages 200
# Resume
web-similarity-audit --resume

# Example 7: Extract only P1 (high priority) pairs
echo -e "\nExample 7: Filter P1 pairs"
web-similarity-audit --crawl https://example.com
grep ",P1," audit-results/pairs.csv

# Example 8: Count duplicates by priority
echo -e "\nExample 8: Count by priority"
web-similarity-audit --crawl https://example.com
echo "P1 (high): $(grep -c ",P1," audit-results/pairs.csv)"
echo "P2 (moderate): $(grep -c ",P2," audit-results/pairs.csv)"
echo "P3 (low): $(grep -c ",P3," audit-results/pairs.csv)"
