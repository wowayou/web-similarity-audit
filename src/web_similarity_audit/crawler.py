"""Website crawler for whole-site similarity audit."""

import asyncio
from collections import deque
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .robots import DEFAULT_USER_AGENT, RobotsRules


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
        self.follow_external = follow_external
        
        self.visited: set[str] = set()
        self.queue: deque[str] = deque()
        # Trademark: rules keyed by host netloc (per RFC 9309, robots.txt is
        # host-scoped, not path-scoped).
        self._robots: dict[str, RobotsRules] = {}
        
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
        parsed = urlparse(url)
        
        # Must be http(s)
        if parsed.scheme not in ("http", "https"):
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
            rules = self._robots.get(parsed.netloc)
            if rules is not None and not rules.can_fetch(url, DEFAULT_USER_AGENT):
                return False
        
        return True
    
    async def _fetch_robots_txt(self, base_url: str) -> None:
        """Fetch and parse robots.txt for the host of *base_url*.

        Failures are non-fatal: if robots.txt cannot be retrieved we treat the
        host as unrestricted (the conventional, permissive default).
        """
        parsed = urlparse(base_url)
        host = parsed.netloc
        if host in self._robots:
            return

        robots_url = f"{parsed.scheme}://{host}/robots.txt"
        text = ""

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    robots_url,
                    follow_redirects=True,
                    headers={"User-Agent": DEFAULT_USER_AGENT},
                )
                if response.status_code == 200:
                    text = response.text
        except Exception:
            # Network/parse errors: treat as no restrictions.
            text = ""

        self._robots[host] = RobotsRules.parse(text)
        
    def _extract_links(self, html: str, base_url: str) -> list[str]:
        """Extract links from HTML."""
        soup = BeautifulSoup(html, "lxml")
        links = []
        
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            normalized = self._normalize_url(absolute_url)
            
            if self._should_crawl(normalized, base_url):
                links.append(normalized)
        
        return links
    
    async def crawl(
        self,
        start_url: str,
        progress_callback: Optional[callable] = None,
    ) -> list[str]:
        """
        Crawl website starting from start_url.
        
        Args:
            start_url: Starting URL (homepage or any page)
            progress_callback: Optional callback(current_count, url) for progress
        
        Returns:
            List of discovered URLs (including start_url)
        """
        start_url = self._normalize_url(start_url)
        self.queue.append(start_url)
        results: list[str] = []
        
        # Fetch robots.txt
        if self.respect_robots:
            await self._fetch_robots_txt(start_url)
        
        # Semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Rate limiting
        last_request_time = {}
        rate_limit_lock = asyncio.Lock()
        
        async def rate_limited_fetch(url: str) -> tuple[str, Optional[str]]:
            """Fetch with rate limiting per host."""
            parsed = urlparse(url)
            host = parsed.netloc
            
            async with rate_limit_lock:
                if host in last_request_time:
                    elapsed = asyncio.get_event_loop().time() - last_request_time[host]
                    min_interval = 1.0 / self.rate_limit
                    if elapsed < min_interval:
                        await asyncio.sleep(min_interval - elapsed)
                last_request_time[host] = asyncio.get_event_loop().time()
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        url,
                        follow_redirects=True,
                        headers={"User-Agent": "web-similarity-audit/0.1.0 (crawler)"},
                    )
                    if response.status_code == 200 and "text/html" in response.headers.get("content-type", ""):
                        return url, response.text
            except Exception:
                pass
            
            return url, None
        
        async def process_url(url: str):
            """Process a single URL."""
            async with semaphore:
                if url in self.visited or len(results) >= self.max_pages:
                    return
                
                self.visited.add(url)
                
                # Fetch
                _, html = await rate_limited_fetch(url)
                
                if html:
                    results.append(url)
                    
                    if progress_callback:
                        progress_callback(len(results), url)
                    
                    # Extract and queue new links
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
