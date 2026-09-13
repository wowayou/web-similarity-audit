#!/usr/bin/env bash
# Demo script for web-similarity-audit tool

set -e

echo "======================================"
echo "Web Page Similarity Auditor - Demo"
echo "======================================"
echo

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

echo "1. Running test suite..."
echo "--------------------------------------"
pytest tests/ -v --tb=short
echo

echo "2. Testing CLI help..."
echo "--------------------------------------"
web-similarity-audit --help
echo

echo "3. Running live demo (2 pages)..."
echo "--------------------------------------"
rm -rf demo-output
web-similarity-audit \
    https://example.com \
    https://example.org \
    --output-dir demo-output
echo

echo "4. Viewing report..."
echo "--------------------------------------"
cat demo-output/report.md
echo

echo "5. Checking pairs CSV..."
echo "--------------------------------------"
cat demo-output/pairs.csv
echo

echo "6. Summary of pages.json..."
echo "--------------------------------------"
python3 -c "
import json
with open('demo-output/pages.json') as f:
    data = json.load(f)
print(f\"Total pages: {data['summary']['total']}\")
print(f\"Successful: {data['summary']['successful']}\")
print(f\"Uncertain: {data['summary']['uncertain']}\")
print(f\"Failed: {data['summary']['failed']}\")
for page in data['pages']:
    print(f\"  - {page['url']}: {page['extraction_method']} (confident={page['extraction_confident']})\")
"
echo

echo "======================================"
echo "Demo complete!"
echo "======================================"
echo
echo "Output files in: demo-output/"
echo "  - report.md"
echo "  - pairs.csv"
echo "  - pages.json"
echo
