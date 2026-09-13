#!/usr/bin/env python3
"""
Example: Programmatic usage of web-similarity-audit in an SEO workflow
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


def run_audit(url: str, max_pages: int = 200, output_dir: str = "audit-results") -> int:
    """Run the audit and return exit code."""
    cmd = [
        "web-similarity-audit",
        "--crawl", url,
        "--max-pages", str(max_pages),
        "--output", output_dir
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Audit failed with code {result.returncode}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return result.returncode
    
    print("✅ Audit completed successfully")
    return 0


def load_results(output_dir: str = "audit-results") -> Dict:
    """Load audit results from JSON files."""
    results_path = Path(output_dir)
    
    with open(results_path / "pages.json") as f:
        pages = json.load(f)
    
    # Parse CSV pairs
    pairs = []
    with open(results_path / "pairs.csv") as f:
        header = f.readline().strip().split(',')
        for line in f:
            values = line.strip().split(',')
            pairs.append(dict(zip(header, values)))
    
    return {
        "pages": pages,
        "pairs": pairs
    }


def analyze_duplicates(results: Dict) -> Dict:
    """Analyze duplicate patterns."""
    pairs = results["pairs"]
    pages = results["pages"]
    
    stats = {
        "total_pages": len(pages),
        "total_pairs": len(pairs),
        "p1_count": sum(1 for p in pairs if p["priority"] == "P1"),
        "p2_count": sum(1 for p in pairs if p["priority"] == "P2"),
        "p3_count": sum(1 for p in pairs if p["priority"] == "P3"),
        "exact_duplicates": sum(1 for p in pairs if p["sha256_match"] == "True"),
        "extraction_failures": sum(1 for p in pages if not p["extraction_success"])
    }
    
    # Find pages involved in most P1 duplicates
    p1_urls = {}
    for pair in pairs:
        if pair["priority"] == "P1":
            for url_key in ["url_a", "url_b"]:
                url = pair[url_key]
                p1_urls[url] = p1_urls.get(url, 0) + 1
    
    stats["most_duplicated"] = sorted(
        p1_urls.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:5]
    
    return stats


def generate_summary_report(stats: Dict) -> str:
    """Generate a summary report."""
    report = f"""
# Content Audit Summary

## Overview
- Total pages audited: {stats['total_pages']}
- Total comparisons: {stats['total_pairs']}
- Extraction failures: {stats['extraction_failures']}

## Duplicate Detection
- P1 (High priority): {stats['p1_count']}
- P2 (Moderate): {stats['p2_count']}
- P3 (Low): {stats['p3_count']}
- Exact duplicates (SHA-256): {stats['exact_duplicates']}

## Pages with Most P1 Duplicates
"""
    for url, count in stats["most_duplicated"]:
        report += f"- {url} ({count} duplicates)\n"
    
    report += "\n## Recommendations\n"
    if stats["p1_count"] > 10:
        report += "⚠️ HIGH: More than 10 high-priority duplicates found. Immediate action required.\n"
    elif stats["p1_count"] > 0:
        report += "⚠️ MEDIUM: Some high-priority duplicates found. Review recommended.\n"
    else:
        report += "✅ GOOD: No high-priority duplicates detected.\n"
    
    if stats["extraction_failures"] > stats["total_pages"] * 0.1:
        report += f"⚠️ WARNING: {stats['extraction_failures']} pages failed extraction. Check page structure.\n"
    
    return report


def main():
    """Main workflow."""
    # Example site to audit
    site_url = "https://example.com"
    
    print(f"Starting audit for {site_url}...")
    
    # Run audit
    exit_code = run_audit(site_url, max_pages=100)
    if exit_code != 0:
        sys.exit(exit_code)
    
    # Load results
    print("\nLoading results...")
    results = load_results()
    
    # Analyze
    print("Analyzing patterns...")
    stats = analyze_duplicates(results)
    
    # Generate report
    report = generate_summary_report(stats)
    print(report)
    
    # Save custom report
    with open("custom-summary.md", "w") as f:
        f.write(report)
    print("\n✅ Custom summary saved to custom-summary.md")
    
    # Exit with appropriate code
    if stats["p1_count"] > 10:
        print("\n❌ Too many P1 duplicates, failing build")
        sys.exit(1)
    
    print("\n✅ Audit passed quality threshold")
    sys.exit(0)


if __name__ == "__main__":
    main()
