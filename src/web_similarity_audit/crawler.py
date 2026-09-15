"""Website crawler for whole-site similarity audit."""

import asyncio
from collections import deque
from typing import Callable, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .fetcher import USER_AGENT, PageFetcher, validate_http_url
from .robots import DEFAULT_USER_AGENT, RobotsRules

MAX_CRAWL_DELAY_SECONDS = 3600.0


class WebsiteCrawler:
    """
    Crawl a website and collect internal page URLs.
    
    Similar to Screaming Frog's crawling mode, but focused on collecting
    pages for similarity analysis rather than full SEO audit.
    """
    
    def __init__(
        self,
        max_pages: int = 200,
        timeout: float = 10.0,
        rate_limit: float = 2.0,
        max_concurrent: int = 4,
        respect_robots: bool = True,
        follow_external: bool = False,
        max_response_size: int = 2 * 1024 * 1024,
        allow_private: bool = False,
    ):
        """
        Initialize crawler.
        
        Args:
            max_pages: Maximum pages to crawl
            timeout: Request timeout in seconds
            rate_limit: Requests per second
            max_concurrent: Maximum concurrent requests
            respect_robots: Respect robots.txt (basic implementation)
            follow_external: Follow external links (default: internal only)
        """
        self.max_pages = max_pages
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.max_concurrent = max_concurrent
        self.respect_robots = respect_robots
        self.max_response_size = max_response_size
        self.allow_private = allow_private
        self.follow_external = follow_external
        
        self.visited: set[str] = set()
        self.queue: deque[str] = deque()
        # Trademark: rules keyed by host netloc (per RFC 9309, robots.txt is
        # host-scoped, not path-scoped).
        self._robots: dict[str, RobotsRules] = {}
        self._robots_denied: set[str] = set()
        self.robots_warnings: list[str] = []
        
    def _normalize_url(self, url: str) -> str:
        """Normalize URL (remove fragment, trailing slash on non-root)."""
        parsed = urlparse(url)
        # Remove fragment
        url_no_fragment = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            url_no_fragment += f"?{parsed.query}"
        
        # Remove trailing slash (but keep for root)
        if url_no_fragment.endswith("/") and parsed.path != "/":
            url_no_fragment = url_no_fragment[:-1]
        
        return url_no_fragment
    
    def _is_same_domain(self, url: str, base_url: str) -> bool:
        """Check if URL is on same domain as base."""
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_url)
        return parsed_url.netloc == parsed_base.netloc
    
    def _should_crawl(self, url: str, base_url: str) -> bool:
        """Check if URL should be crawled."""
        try:
            parsed = validate_http_url(url)
        except ValueError:
            return False
        
        # Skip common non-HTML extensions
        path_lower = parsed.path.lower()
        skip_extensions = (
            ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
            ".pdf", ".zip", ".tar", ".gz",
            ".css", ".js", ".json", ".xml",
            ".mp4", ".mp3", ".avi", ".mov",
            ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        )
        if any(path_lower.endswith(ext) for ext in skip_extensions):
            return False
        
        # Check domain
        if not self.follow_external and not self._is_same_domain(url, base_url):
            return False
        
        # Check robots.txt (prefix-based, longest-match precedence)
        if self.respect_robots:
            if parsed.netloc in self._robots_denied:
                return False
            rules = self._robots.get(parsed.netloc)
            if rules is not None and not rules.can_fetch(url, DEFAULT_USER_AGENT):
                return False
        
        return True
    
    async def _fetch_robots_txt(
        self, base_url: str, fetcher: PageFetcher
    ) -> None:
        """Fetch and parse robots.txt for the host of *base_url*.

        A 4xx response is treated as no published rules. Network failures,
        5xx responses, 429, and redirects deny crawling for the host.
        """
        parsed = urlparse(base_url)
        host = parsed.netloc
        if host in self._robots:
            return

        robots_url = f"{parsed.scheme}://{host}/robots.txt"
        text = ""

        body, status, _ = await fetcher.fetch(
            robots_url,
            require_html=False,
            user_agent=USER_AGENT,
            follow_redirects=False,
        )
        if status == 200 and body is not None:
            text = body

        self._robots[host] = RobotsRules.parse(text)
        unavailable = (
            status is None
            or status == 429
            or status >= 500
            or (status is not None and 300 <= status < 400)
        )
        if unavailable:
            reason = f"status {status}" if status is not None else "unreachable"
            self._robots_denied.add(host)
            self.robots_warnings.append(
                f"robots.txt unavailable for {host} ({reason}); crawling denied"
            )
            return
        rules = self._robots[host]
        if self.respect_robots and rules.crawl_delay is not None:
            delay = rules.crawl_delay
            if delay < 0:
                self.robots_warnings.append(
                    f"negative Crawl-delay for {host}; ignoring"
                )
            elif delay > MAX_CRAWL_DELAY_SECONDS:
                self.robots_warnings.append(
                    f"Crawl-delay for {host} exceeds {MAX_CRAWL_DELAY_SECONDS:g}s; capping"
                )
                fetcher.set_host_min_interval(host, MAX_CRAWL_DELAY_SECONDS)
            else:
                fetcher.set_host_min_interval(host, delay)
        
    def _extract_links(self, html: str, base_url: str) -> list[str]:
        """Extract links from HTML."""
        soup = BeautifulSoup(html, "lxml")
        links = []
        
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if not isinstance(href, str):
                continue
            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            normalized = self._normalize_url(absolute_url)
            
            if self._should_crawl(normalized, base_url):
                links.append(normalized)
        
        return links
    
    async def crawl(
        self,
        start_url: str,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> list[str]:
        """
        Crawl website starting from start_url.
        
        Args:
            start_url: Starting URL (homepage or any page)
            progress_callback: Optional callback(current_count, url) for progress
        
        Returns:
            List of discovered URLs (including start_url)
        """
        validate_http_url(start_url)
        self.visited.clear()
        self.queue.clear()
        self._robots.clear()
        self._robots_denied.clear()
        self.robots_warnings.clear()
        start_url = self._normalize_url(start_url)
        self.queue.append(start_url)
        results: list[str] = []
        fetcher = PageFetcher(
            max_response_size=self.max_response_size,
            timeout=self.timeout,
            max_retries=0,
            rate_limit_per_host=self.rate_limit,
            max_concurrent=self.max_concurrent,
            allow_private=self.allow_private,
        )

        if self.respect_robots:
            await self._fetch_robots_txt(start_url, fetcher)
            if not self._should_crawl(start_url, start_url):
                return []
        
        
        async def process_url(url: str):
            """Process a single URL through the shared protected fetcher."""
            if url in self.visited or len(results) >= self.max_pages:
                return

            self.visited.add(url)
            if self.respect_robots:
                await self._fetch_robots_txt(url, fetcher)
                if not self._should_crawl(url, start_url):
                    return

            html, status, _ = await fetcher.fetch(url)
            if html is not None and status == 200:
                results.append(url)

                if progress_callback:
                    progress_callback(len(results), url)

                if len(results) < self.max_pages:
                    links = self._extract_links(html, url)
                    for link in links:
                        if link not in self.visited and link not in self.queue:
                            self.queue.append(link)
        
        # BFS crawl
        while self.queue and len(results) < self.max_pages:
            # Process batch
            batch_size = min(self.max_concurrent, len(self.queue), self.max_pages - len(results))
            batch = [self.queue.popleft() for _ in range(batch_size)]
            
            await asyncio.gather(*[process_url(url) for url in batch])
        
        return results
