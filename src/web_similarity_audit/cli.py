"""CLI entry point for web similarity audit."""

import argparse
import asyncio
import csv
import sys
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)

from .crawler import WebsiteCrawler
from .extractor import ContentExtractor
from .fetcher import PageFetcher
from .models import PageInput, PageResult
from .reporter import Reporter
from .similarity import SimilarityCalculator
from .template import TemplateDetector
from .state import StateManager

console = Console()


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
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous interrupted run if state exists",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Force fresh start, ignore any saved state",
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
    start_time: Optional[float] = None,
    resume_pages: Optional[list[PageResult]] = None,
) -> int:
    """
    Run the full audit pipeline.
    
    Args:
        page_inputs: List of pages to audit
        output_dir: Output directory for reports
        fetcher_config: Configuration for PageFetcher
        start_time: Start time (for resume)
        resume_pages: Already fetched pages (for resume)
    
    Returns:
        Exit code
    """
    if start_time is None:
        start_time = time.time()
    
    state_manager = StateManager(output_dir)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        
        # Phase 1: Fetch (skip if resuming)
        if resume_pages is None:
            fetch_task = progress.add_task(
                f"[cyan]Fetching {len(page_inputs)} pages...",
                total=len(page_inputs)
            )
            
            fetcher = PageFetcher(**fetcher_config)
            urls = [p.url for p in page_inputs]
            
            # Fetch with progress updates and periodic state saves
            fetch_results = []
            pages: list[PageResult] = []
            extractor = ContentExtractor()
            
            for i, (page_input, url) in enumerate(zip(page_inputs, urls)):
                result = await fetcher.fetch_all([url])
                fetch_results.append(result[0])
                
                # Extract immediately for state saving
                url_result, html, status_code, error = result[0]
                if html:
                    page = extractor.extract(html, page_input, status_code)
                else:
                    page = PageResult(
                        url=url_result,
                        status_code=status_code,
                        error=error,
                        extraction_method="fetch_failed",
                        extraction_confident=False,
                    )
                pages.append(page)
                
                progress.update(fetch_task, advance=1)
                
                # Save state every 10 pages
                if (i + 1) % 10 == 0:
                    state_manager.save_state(
                        start_url=page_inputs[0].url if page_inputs else None,
                        fetched_urls=urls[:i+1],
                        pages=pages,
                        start_time=start_time,
                    )
            
            progress.update(fetch_task, description="[green]✓ Fetching complete")
        else:
            # Resume from saved pages
            pages = resume_pages
            console.print(f"[yellow]↻ Resumed with {len(pages)} previously fetched pages[/yellow]")
        
        fetch_phase_time = time.time() - start_time
        
        # Check failure thresholds
        fetch_failed = sum(1 for p in pages if p.status_code is None or p.status_code >= 400)
        extraction_failed = sum(
            1 for p in pages 
            if p.extraction_method in ["failed", "selector_failed", "markers_failed"]
        )
        
        fetch_rate = fetch_failed / len(pages)
        extraction_rate = extraction_failed / len(pages)
        
        if fetch_rate > 0.2:
            console.print(f"[red]ERROR: {fetch_failed}/{len(pages)} pages unreachable (>20%)")
            reporter = Reporter(output_dir)
            reporter.write_pages_json(pages)
            reporter.write_pairs_csv([])
            reporter.write_markdown_report(
                pages, [], None, time.time() - start_time,
                fetch_time=fetch_phase_time,
            )
            state_manager.clear_state()
            return 2
        
        if extraction_rate > 0.2:
            console.print(f"[red]ERROR: {extraction_failed}/{len(pages)} pages failed extraction (>20%)")
            reporter = Reporter(output_dir)
            reporter.write_pages_json(pages)
            reporter.write_pairs_csv([])
            reporter.write_markdown_report(
                pages, [], None, time.time() - start_time,
                fetch_time=fetch_phase_time,
            )
            state_manager.clear_state()
            return 3
        
        # Phase 3: Template detection
        template_task = progress.add_task(
            "[cyan]Detecting common template blocks...",
            total=1
        )
        
        template_detector = TemplateDetector(min_pages=5, threshold=0.6)
        common_blocks = template_detector.detect_common_blocks(pages)
        
        if common_blocks is None:
            progress.update(template_task, description=f"[yellow]⚠ Template detection disabled (n={len(pages)} < 5)")
        elif len(common_blocks) == 0:
            progress.update(template_task, description="[green]✓ No common blocks detected")
        else:
            progress.update(template_task, description=f"[green]✓ Detected {len(common_blocks)} common blocks")
        
        progress.update(template_task, advance=1)
        
        # Phase 4: Similarity computation
        total_pairs = len(pages) * (len(pages) - 1) // 2
        similarity_task = progress.add_task(
            f"[cyan]Computing similarity for {total_pairs:,} pairs...",
            total=total_pairs
        )
        
        calculator = SimilarityCalculator()
        scores = []
        
        for i in range(len(pages)):
            for j in range(i + 1, len(pages)):
                score = calculator.compute_pairwise(pages[i], pages[j], common_blocks)
                scores.append(score)
                progress.update(similarity_task, advance=1)
        
        progress.update(similarity_task, description="[green]✓ Similarity computation complete")
        
        compute_time = time.time() - start_time - fetch_phase_time
        
        # Phase 5: Report generation
        report_task = progress.add_task(
            f"[cyan]Generating reports...",
            total=3
        )
        
        reporter = Reporter(output_dir)
        reporter.write_pages_json(pages)
        progress.update(report_task, advance=1)
        
        reporter.write_pairs_csv(scores)
        progress.update(report_task, advance=1)
        
        reporter.write_markdown_report(
            pages, scores, common_blocks, time.time() - start_time,
            compute_time=compute_time,
            fetch_time=fetch_phase_time,
        )
        progress.update(report_task, advance=1, description="[green]✓ Reports generated")
    
    # Clear state on success
    state_manager.clear_state()
    
    # Summary
    elapsed = time.time() - start_time
    p1_count = sum(1 for s in scores if s.priority == "P1")
    p2_count = sum(1 for s in scores if s.priority == "P2")
    p3_count = sum(1 for s in scores if s.priority == "P3")
    
    console.print(f"\n[bold green]✓ Completed in {elapsed:.2f}s[/bold green]")
    console.print(f"  P1 (high): [red]{p1_count}[/red]")
    console.print(f"  P2 (moderate): [yellow]{p2_count}[/yellow]")
    console.print(f"  P3 (low): [dim]{p3_count}[/dim]")
    console.print(f"\nReports written to: [cyan]{output_dir.absolute()}[/cyan]")
    
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
    console.print(f"\n[bold cyan]Crawling website starting from:[/bold cyan] {start_url}")
    console.print(f"  Max pages: {max_pages}")
    console.print(f"  Follow external: {follow_external}\n")
    
    crawler = WebsiteCrawler(
        max_pages=max_pages,
        timeout=timeout,
        rate_limit=rate_limit,
        max_concurrent=max_concurrent,
        respect_robots=True,
        follow_external=follow_external,
    )
    
    discovered_urls = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        
        crawl_task = progress.add_task(
            "[cyan]Crawling...",
            total=max_pages
        )
        
        def progress_callback(count: int, url: str):
            discovered_urls.append(url)
            progress.update(
                crawl_task,
                completed=count,
                description=f"[cyan]Crawling... [dim]{url[:60]}...[/dim]"
            )
        
        urls = await crawler.crawl(start_url, progress_callback=progress_callback)
        progress.update(crawl_task, description=f"[green]✓ Crawl complete: {len(urls)} pages discovered")
    
    console.print()
    return urls


def main():
    """Main entry point."""
    args = parse_args()
    
    # Check for resume state
    state_manager = StateManager(args.output_dir)
    resume_state = None
    
    if args.no_resume:
        # Force fresh start
        if state_manager.has_state():
            console.print("[yellow]Clearing previous state (--no-resume)[/yellow]")
            state_manager.clear_state()
    elif state_manager.has_state():
        # Ask if want to resume
        resume_info = state_manager.get_resume_info()
        if resume_info:
            elapsed_min = resume_info['elapsed_time'] / 60
            console.print(f"\n[yellow]Found previous run:[/yellow]")
            console.print(f"  Started: {resume_info.get('start_url', 'N/A')}")
            console.print(f"  Fetched: {resume_info['fetched_pages']} pages")
            console.print(f"  Elapsed: {elapsed_min:.1f} minutes ago")
            
            if args.resume:
                resume_state = state_manager.load_state()
                console.print("[green]Resuming from saved state...[/green]\n")
            else:
                console.print("[dim]Use --resume to continue, or --no-resume to start fresh[/dim]\n")
    
    # Crawl mode
    if hasattr(args, 'crawl') and args.crawl:
        if len(args.input) != 1:
            console.print("[red]ERROR: --crawl mode requires exactly one starting URL[/red]")
            return 1
        
        start_url = args.input[0]
        if not start_url.startswith(("http://", "https://")):
            console.print(f"[red]ERROR: Invalid URL: {start_url}[/red]")
            return 1
        
        # Check if resuming crawl
        if resume_state and resume_state.crawl_mode:
            page_inputs = [PageInput(url=url) for url in resume_state.fetched_urls]
            resume_pages = state_manager.pages_from_state(resume_state)
            start_time = resume_state.start_time
        else:
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
                    console.print(f"[red]ERROR: Only discovered {len(urls)} page(s), need at least 2[/red]")
                    return 1
                
                page_inputs = [PageInput(url=url) for url in urls]
                resume_pages = None
                start_time = None
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Crawl interrupted by user[/yellow]")
                return 4
            except Exception as e:
                console.print(f"[red]FATAL ERROR during crawl: {e}[/red]")
                import traceback
                traceback.print_exc()
                return 4
    else:
        # Load URLs
        if resume_state and not resume_state.crawl_mode:
            page_inputs = [PageInput(url=url) for url in resume_state.fetched_urls]
            resume_pages = state_manager.pages_from_state(resume_state)
            start_time = resume_state.start_time
        else:
            page_inputs, error = load_urls(args.input)
            if error:
                console.print(f"[red]ERROR: {error}[/red]")
                return 1
            
            # Validate
            error = validate_urls(page_inputs)
            if error:
                console.print(f"[red]ERROR: {error}[/red]")
                return 1
            
            resume_pages = None
            start_time = None
    
    # Run audit
    fetcher_config = {
        "max_response_size": args.max_response_size,
        "timeout": args.timeout,
        "rate_limit_per_host": args.rate_limit,
        "max_concurrent": args.max_concurrent,
    }
    
    try:
        exit_code = asyncio.run(run_audit(
            page_inputs, 
            args.output_dir, 
            fetcher_config,
            start_time=start_time,
            resume_pages=resume_pages,
        ))
        return exit_code
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user - state saved for resume[/yellow]")
        return 4
    except Exception as e:
        console.print(f"[red]FATAL ERROR: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 4


if __name__ == "__main__":
    sys.exit(main())
