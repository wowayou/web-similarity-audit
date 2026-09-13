"""CLI entry point for web similarity audit."""

import argparse
import asyncio
import csv
import sys
import time
from pathlib import Path
from typing import Optional

from .crawler import WebsiteCrawler
from .extractor import ContentExtractor
from .fetcher import PageFetcher
from .models import PageInput, PageResult
from .reporter import Reporter
from .similarity import SimilarityCalculator
from .template import TemplateDetector


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Audit web page similarity with explicit failure reporting"
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="URLs or path to CSV file with URLs, or --crawl with single URL",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./audit-results"),
        help="Output directory for reports (default: ./audit-results)",
    )
    parser.add_argument(
        "--crawl",
        action="store_true",
        help="Crawl entire website starting from first URL (Screaming Frog mode)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=200,
        help="Maximum pages to crawl in --crawl mode (default: 200)",
    )
    parser.add_argument(
        "--follow-external",
        action="store_true",
        help="Follow external links in --crawl mode (default: internal only)",
    )
    parser.add_argument(
        "--max-response-size",
        type=int,
        default=2 * 1024 * 1024,
        help="Maximum response size in bytes (default: 2MB)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP request timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=2.0,
        help="Requests per second per host (default: 2)",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=4,
        help="Maximum concurrent requests (default: 4)",
    )
    
    return parser.parse_args()


def load_urls(inputs: list[str]) -> tuple[list[PageInput], Optional[str]]:
    """
    Load URLs from command line args or CSV file.
    
    Returns:
        (list of PageInput, error_message)
    """
    # Check if first arg is a CSV file
    if len(inputs) == 1 and Path(inputs[0]).suffix.lower() == ".csv":
        csv_path = Path(inputs[0])
        if not csv_path.exists():
            return [], f"CSV file not found: {csv_path}"
        
        pages = []
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "url" not in row:
                        return [], "CSV must have 'url' column"
                    
                    pages.append(PageInput(
                        url=row["url"],
                        selector=row.get("selector") or None,
                        start_marker=row.get("start_marker") or None,
                        end_marker=row.get("end_marker") or None,
                    ))
        except Exception as e:
            return [], f"Failed to read CSV: {e}"
        
        return pages, None
    
    # Otherwise treat as URLs
    pages = [PageInput(url=url) for url in inputs]
    return pages, None


def validate_urls(pages: list[PageInput]) -> Optional[str]:
    """Validate URL count and format."""
    if len(pages) < 2:
        return "Need at least 2 URLs"
    
    if len(pages) > 200:
        return "Maximum 200 URLs supported"
    
    # Basic URL validation
    for page in pages:
        if not page.url.startswith(("http://", "https://")):
            return f"Invalid URL: {page.url}"
    
    return None


async def run_audit(
    page_inputs: list[PageInput],
    output_dir: Path,
    fetcher_config: dict,
) -> int:
    """
    Run the full audit pipeline.
    
    Returns:
        Exit code
    """
    start_time = time.time()
    
    # Phase 1: Fetch
    print(f"Fetching {len(page_inputs)} pages...")
    fetcher = PageFetcher(**fetcher_config)
    urls = [p.url for p in page_inputs]
    fetch_results = await fetcher.fetch_all(urls)
    
    # Phase 2: Extract
    print("Extracting main content...")
    extractor = ContentExtractor()
    pages: list[PageResult] = []
    
    for page_input, (url, html, status_code, error) in zip(page_inputs, fetch_results):
        if html:
            result = extractor.extract(html, page_input, status_code)
        else:
            result = PageResult(
                url=url,
                status_code=status_code,
                error=error,
                extraction_method="fetch_failed",
                extraction_confident=False,
            )
        pages.append(result)
    
    # Check failure thresholds
    fetch_failed = sum(1 for p in pages if p.status_code is None or p.status_code >= 400)
    extraction_failed = sum(
        1 for p in pages 
        if p.extraction_method in ["failed", "selector_failed", "markers_failed"]
    )
    
    fetch_rate = fetch_failed / len(pages)
    extraction_rate = extraction_failed / len(pages)
    
    if fetch_rate > 0.2:
        print(f"ERROR: {fetch_failed}/{len(pages)} pages unreachable (>{20}%)", file=sys.stderr)
        # Still write reports
        reporter = Reporter(output_dir)
        reporter.write_pages_json(pages)
        reporter.write_pairs_csv([])
        reporter.write_markdown_report(pages, [], None, time.time() - start_time)
        return 2
    
    if extraction_rate > 0.2:
        print(f"ERROR: {extraction_failed}/{len(pages)} pages failed extraction (>{20}%)", file=sys.stderr)
        reporter = Reporter(output_dir)
        reporter.write_pages_json(pages)
        reporter.write_pairs_csv([])
        reporter.write_markdown_report(pages, [], None, time.time() - start_time)
        return 3
    
    # Phase 3: Template detection
    print("Detecting common template blocks...")
    template_detector = TemplateDetector(min_pages=5, threshold=0.6)
    common_blocks = template_detector.detect_common_blocks(pages)
    
    if common_blocks is None:
        print(f"  Template detection disabled (n={len(pages)} < 5)")
    elif len(common_blocks) == 0:
        print(f"  No common blocks detected")
    else:
        print(f"  Detected {len(common_blocks)} common blocks")
    
    # Phase 4: Similarity computation
    print(f"Computing pairwise similarity for {len(pages) * (len(pages) - 1) // 2} pairs...")
    calculator = SimilarityCalculator()
    scores: list[SimilarityScore] = []
    
    for i in range(len(pages)):
        for j in range(i + 1, len(pages)):
            score = calculator.compute_pairwise(pages[i], pages[j], common_blocks)
            scores.append(score)
    
    # Phase 5: Report generation
    print(f"Generating reports in {output_dir}...")
    reporter = Reporter(output_dir)
    reporter.write_pages_json(pages)
    reporter.write_pairs_csv(scores)
    reporter.write_markdown_report(pages, scores, common_blocks, time.time() - start_time)
    
    # Summary
    elapsed = time.time() - start_time
    p1_count = sum(1 for s in scores if s.priority == "P1")
    p2_count = sum(1 for s in scores if s.priority == "P2")
    p3_count = sum(1 for s in scores if s.priority == "P3")
    
    print(f"\nCompleted in {elapsed:.2f}s")
    print(f"  P1 (high): {p1_count}")
    print(f"  P2 (moderate): {p2_count}")
    print(f"  P3 (low): {p3_count}")
    print(f"\nReports written to: {output_dir.absolute()}")
    
    return 0


async def crawl_website(
    start_url: str,
    max_pages: int,
    follow_external: bool,
    timeout: float,
    rate_limit: float,
    max_concurrent: int,
) -> list[str]:
    """Crawl website and return discovered URLs."""
    print(f"Crawling website starting from: {start_url}")
    print(f"  Max pages: {max_pages}")
    print(f"  Follow external: {follow_external}")
    print()
    
    crawler = WebsiteCrawler(
        max_pages=max_pages,
        timeout=timeout,
        rate_limit=rate_limit,
        max_concurrent=max_concurrent,
        respect_robots=True,
        follow_external=follow_external,
    )
    
    def progress_callback(count: int, url: str):
        print(f"  [{count}/{max_pages}] {url}")
    
    urls = await crawler.crawl(start_url, progress_callback=progress_callback)
    
    print()
    print(f"Crawl complete: discovered {len(urls)} pages")
    print()
    
    return urls


def main():
    """Main entry point."""
    args = parse_args()
    
    # Crawl mode
    if hasattr(args, 'crawl') and args.crawl:
        if len(args.input) != 1:
            print("ERROR: --crawl mode requires exactly one starting URL", file=sys.stderr)
            return 1
        
        start_url = args.input[0]
        if not start_url.startswith(("http://", "https://")):
            print(f"ERROR: Invalid URL: {start_url}", file=sys.stderr)
            return 1
        
        try:
            urls = asyncio.run(crawl_website(
                start_url=start_url,
                max_pages=args.max_pages,
                follow_external=args.follow_external,
                timeout=args.timeout,
                rate_limit=args.rate_limit,
                max_concurrent=args.max_concurrent,
            ))
            
            if len(urls) < 2:
                print(f"ERROR: Only discovered {len(urls)} page(s), need at least 2", file=sys.stderr)
                return 1
            
            page_inputs = [PageInput(url=url) for url in urls]
            
        except KeyboardInterrupt:
            print("\nCrawl interrupted by user", file=sys.stderr)
            return 4
        except Exception as e:
            print(f"FATAL ERROR during crawl: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 4
    else:
        # Load URLs
        page_inputs, error = load_urls(args.input)
        if error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 1
        
        # Validate
        error = validate_urls(page_inputs)
        if error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 1
    
    # Run audit
    fetcher_config = {
        "max_response_size": args.max_response_size,
        "timeout": args.timeout,
        "rate_limit_per_host": args.rate_limit,
        "max_concurrent": args.max_concurrent,
    }
    
    try:
        exit_code = asyncio.run(run_audit(page_inputs, args.output_dir, fetcher_config))
        return exit_code
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 4
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 4


if __name__ == "__main__":
    sys.exit(main())
