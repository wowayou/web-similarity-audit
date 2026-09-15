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
from .fetcher import PageFetcher, validate_http_url
from .models import PageInput, PageResult
from .reporter import Reporter
from .similarity import SimilarityCalculator
from .template import TemplateDetector
from .state import AuditState, StateError, StateManager

console = Console()


def _remaining_from_state(state: AuditState) -> list[str]:
    """URLs from the saved plan that the interrupted run never fetched."""
    planned = state.planned_urls or list(state.fetched_urls)
    fetched = set(state.fetched_urls)
    return [u for u in planned if u not in fetched]


def _remaining_inputs_from_state(state: AuditState) -> list[PageInput]:
    """Restore pending extraction directives, including CSV selectors."""
    pending_urls = _remaining_from_state(state)
    saved = {item.get("url"): item for item in state.planned_inputs}
    restored = []
    for url in pending_urls:
        item = saved.get(url)
        if item is None:
            restored.append(PageInput(url=url))
        else:
            restored.append(PageInput(
                url=url,
                selector=item.get("selector"),
                start_marker=item.get("start_marker"),
                end_marker=item.get("end_marker"),
            ))
    return restored


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Audit web page similarity with explicit failure reporting"
    )
    parser.add_argument(
        "input",
        nargs="*",
        help="URLs or path to CSV file with URLs, or --crawl with single URL",
    )
    parser.add_argument(
        "--output-dir", "--output",
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
        "--ignore-robots",
        action="store_true",
        help="Ignore robots.txt rules in --crawl mode (default: respect robots.txt)",
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
        "--rate-limit", "--per-host-rate",
        type=float,
        default=2.0,
        help="Requests per second per host (default: 2)",
    )
    parser.add_argument(
        "--max-concurrent", "--concurrency",
        type=int,
        default=4,
        help="Maximum concurrent requests (default: 4)",
    )
    parser.add_argument(
        "--allow-private",
        action="store_true",
        help="Allow fetching private/loopback addresses, e.g. intranet or "
             "staging sites (disables SSRF protection)",
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
    
    for page in pages:
        try:
            validate_http_url(page.url)
        except ValueError as exc:
            return f"Invalid URL '{page.url}': {exc}"
    
    return None


def validate_options(args) -> Optional[str]:
    """Validate numeric options before constructing network primitives."""
    checks = (
        (args.max_pages, "--max-pages"),
        (args.max_response_size, "--max-response-size"),
        (args.timeout, "--timeout"),
        (args.rate_limit, "--rate-limit"),
        (args.max_concurrent, "--max-concurrent"),
    )
    for value, name in checks:
        if value <= 0:
            return f"{name} must be greater than zero"
    return None


async def run_audit(
    page_inputs: list[PageInput],
    output_dir: Path,
    fetcher_config: dict,
    start_time: Optional[float] = None,
    resume_pages: Optional[list[PageResult]] = None,
    crawl_mode: bool = False,
    max_pages: Optional[int] = None,
    start_url: Optional[str] = None,
    planned_inputs_snapshot: Optional[list[dict]] = None,
) -> int:
    """
    Run the full audit pipeline.

    Args:
        page_inputs: Pages still to fetch (on resume: the remaining ones)
        output_dir: Output directory for reports
        fetcher_config: Configuration for PageFetcher
        start_time: Start time (for resume)
        resume_pages: Already fetched pages (for resume)
        crawl_mode: Whether this run is a whole-site crawl (saved in state)

    Returns:
        Exit code
    """
    if start_time is None:
        start_time = time.time()

    state_manager = StateManager(output_dir)
    urls = [p.url for p in page_inputs]
    planned_urls = list(dict.fromkeys(
        [p.url for p in (resume_pages or [])] + urls
    ))
    planned_inputs = planned_inputs_snapshot if planned_inputs_snapshot is not None else [
        {
            "url": p.url, "selector": p.selector,
            "start_marker": p.start_marker, "end_marker": p.end_marker,
        }
        for p in page_inputs
    ]
    state_start_url = start_url or (
        page_inputs[0].url if page_inputs else (pages[0].url if pages else None)
    )
    state_config = {
        "fetcher_config": fetcher_config,
        "crawl_mode": crawl_mode,
        "max_pages": max_pages,
    }

    def save_progress(pages: list[PageResult]):
        state_manager.save_state(
            start_url=state_start_url,
            max_pages=max_pages,
            config=state_config,
            fetched_urls=[p.url for p in pages],
            pages=pages,
            crawl_mode=crawl_mode,
            start_time=start_time,
            # Full list this run is responsible for: already-fetched pages
            # plus the ones still queued, so a later resume can continue.
            planned_urls=planned_urls,
            planned_inputs=planned_inputs,
        )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:

        # Phase 1: Fetch (resume_pages holds previously fetched pages, if any)
        if resume_pages is None:
            pages: list[PageResult] = []
        else:
            pages = list(resume_pages)

        fetcher = PageFetcher(**fetcher_config)
        extractor = ContentExtractor()

        if page_inputs:
            save_progress(pages)

        if page_inputs:
            if resume_pages:
                fetch_task = progress.add_task(
                    f"[cyan]Fetching {len(page_inputs)} remaining pages "
                    f"({len(resume_pages)} already done)...",
                    total=len(page_inputs)
                )
            else:
                fetch_task = progress.add_task(
                    f"[cyan]Fetching {len(page_inputs)} pages...",
                    total=len(page_inputs)
                )

            async def fetch_and_extract(page_input: PageInput) -> PageResult:
                html, status_code, error = await fetcher.fetch(page_input.url)
                if html is not None and status_code is not None:
                    return extractor.extract(html, page_input, status_code)
                return PageResult(
                    url=page_input.url,
                    status_code=status_code,
                    error=error,
                    extraction_method="fetch_failed",
                    extraction_confident=False,
                )

            tasks = [
                asyncio.create_task(fetch_and_extract(item))
                for item in page_inputs
            ]
            completed = 0
            for task in asyncio.as_completed(tasks):
                page = await task
                pages.append(page)
                completed += 1

                progress.update(fetch_task, advance=1)

                # Save state every 10 pages
                if completed % 10 == 0:
                    save_progress(pages)

            progress.update(fetch_task, description="[green]✓ Fetching complete")
        
        # Persist the complete fetched set before any threshold exit.
        save_progress(pages)
        fetch_phase_time = time.time() - start_time
        
        # Check failure thresholds
        if not pages:
            console.print("[red]ERROR: No pages available to audit[/red]")
            return 1

        fetch_failed = sum(
            1 for p in pages
            if p.extraction_method == "fetch_failed"
            or p.status_code is None
            or p.status_code >= 400
        )
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
    max_response_size: int,
    allow_private: bool,
    respect_robots: bool = True,
) -> list[str]:
    """Crawl website and return discovered URLs."""
    console.print(f"\n[bold cyan]Crawling website starting from:[/bold cyan] {start_url}")
    console.print(f"  Max pages: {max_pages}")
    console.print(f"  Follow external: {follow_external}")
    console.print(f"  Respect robots.txt: {respect_robots}\n")
    
    crawler = WebsiteCrawler(
        max_pages=max_pages,
        timeout=timeout,
        rate_limit=rate_limit,
        max_concurrent=max_concurrent,
        max_response_size=max_response_size,
        allow_private=allow_private,
        respect_robots=respect_robots,
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
        for warning in crawler.robots_warnings:
            console.print(f"[yellow]WARNING: {warning}[/yellow]")
        progress.update(crawl_task, description=f"[green]✓ Crawl complete: {len(urls)} pages discovered")
    
    console.print()
    return urls


def main():
    """Main entry point."""
    args = parse_args()
    option_error = validate_options(args)
    if option_error:
        console.print(f"[red]ERROR: {option_error}[/red]")
        return 1
    fetcher_config = {
        "max_response_size": args.max_response_size,
        "timeout": args.timeout,
        "rate_limit_per_host": args.rate_limit,
        "max_concurrent": args.max_concurrent,
        "allow_private": args.allow_private,
    }
    
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
        try:
            resume_info = state_manager.get_resume_info()
        except StateError as exc:
            console.print(f"[red]ERROR: {exc}[/red]")
            return 1
        if resume_info:
            elapsed_min = resume_info['elapsed_time'] / 60
            console.print(f"\n[yellow]Found previous run:[/yellow]")
            console.print(f"  Started: {resume_info.get('start_url', 'N/A')}")
            console.print(f"  Fetched: {resume_info['fetched_pages']} pages")
            console.print(f"  Elapsed: {elapsed_min:.1f} minutes ago")
            
            if args.resume:
                try:
                    resume_state = state_manager.load_state()
                except StateError as exc:
                    console.print(f"[red]ERROR: {exc}[/red]")
                    return 1
                console.print("[green]Resuming from saved state...[/green]\n")
            else:
                console.print("[dim]Use --resume to continue, or --no-resume to start fresh[/dim]\n")
    
    crawl_mode = bool(
        args.crawl or (args.resume and resume_state and resume_state.crawl_mode)
    )
    if resume_state:
        resume_config = {
            "fetcher_config": fetcher_config,
            "crawl_mode": crawl_mode,
            "max_pages": args.max_pages,
        }
        for difference in state_manager.config_differences(
            resume_state, resume_config
        ):
            console.print(f"[yellow]WARNING: resume config differs ({difference})[/yellow]")

    # Crawl mode
    if crawl_mode:
        if not (resume_state and resume_state.crawl_mode) and len(args.input) != 1:
            console.print("[red]ERROR: --crawl mode requires exactly one starting URL[/red]")
            return 1
        
        start_url = (
            resume_state.start_url
            if resume_state and resume_state.crawl_mode else args.input[0]
        )
        try:
            validate_http_url(start_url)
        except ValueError as exc:
            console.print(f"[red]ERROR: Invalid URL '{start_url}': {exc}[/red]")
            return 1
        
        # Check if resuming crawl
        if resume_state and resume_state.crawl_mode:
            remaining_inputs = _remaining_inputs_from_state(resume_state)
            resume_pages = state_manager.pages_from_state(resume_state)
            console.print(
                f"[green]Resuming crawl: {len(resume_pages)} pages already "
                f"fetched, {len(remaining_inputs)} remaining[/green]\n"
            )
            page_inputs = remaining_inputs
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
                    max_response_size=args.max_response_size,
                    allow_private=args.allow_private,
                    respect_robots=not args.ignore_robots,
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
            remaining_inputs = _remaining_inputs_from_state(resume_state)
            resume_pages = state_manager.pages_from_state(resume_state)
            console.print(
                f"[green]Resuming: {len(resume_pages)} pages already "
                f"fetched, {len(remaining_inputs)} remaining[/green]\n"
            )
            page_inputs = remaining_inputs
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

    try:
        exit_code = asyncio.run(run_audit(
            page_inputs,
            args.output_dir,
            fetcher_config,
            start_time=start_time,
            resume_pages=resume_pages,
            crawl_mode=crawl_mode,
            max_pages=args.max_pages,
            start_url=(
                resume_state.start_url if resume_state
                else (start_url if crawl_mode else (page_inputs[0].url if page_inputs else None))
            ),
            planned_inputs_snapshot=(
                resume_state.planned_inputs if resume_state else None
            ),
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
