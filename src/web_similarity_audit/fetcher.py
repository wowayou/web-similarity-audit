"""HTTP fetcher with SSRF protection and rate limiting."""

import asyncio
import ipaddress
import socket
from typing import Optional
from urllib.parse import urlparse

import httpx


class SSRFProtectedTransport(httpx.AsyncHTTPTransport):
    """Custom transport that validates IPs after DNS resolution."""
    
    BLOCKED_NETWORKS = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
        ipaddress.ip_network("fe80::/10"),
    ]
    
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Validate target IP before connecting."""
        host = request.url.host
        
        # Resolve DNS
        try:
            addrinfo = await asyncio.get_event_loop().getaddrinfo(
                host, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM
            )
        except socket.gaierror as e:
            raise httpx.ConnectError(f"DNS resolution failed: {e}")
        
        # Check all resolved IPs
        for family, _, _, _, sockaddr in addrinfo:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
                for blocked_net in self.BLOCKED_NETWORKS:
                    if ip in blocked_net:
                        raise httpx.ConnectError(
                            f"SSRF protection: {host} resolves to blocked IP {ip_str}"
                        )
            except ValueError:
                # Invalid IP format, skip
                pass
        
        # Proceed with actual request
        return await super().handle_async_request(request)


class PageFetcher:
    """Fetch web pages with rate limiting and SSRF protection."""
    
    def __init__(
        self,
        max_response_size: int = 2 * 1024 * 1024,  # 2MB
        timeout: float = 10.0,
        max_retries: int = 2,
        rate_limit_per_host: float = 2.0,  # requests per second
        max_concurrent: int = 4,
    ):
        self.max_response_size = max_response_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_per_host = rate_limit_per_host
        self.max_concurrent = max_concurrent
        
        # Per-host rate limiters
        self._host_semaphores: dict[str, asyncio.Semaphore] = {}
        self._host_last_request: dict[str, float] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch(self, url: str) -> tuple[Optional[str], Optional[int], Optional[str]]:
        """
        Fetch a single URL.
        
        Returns:
            (html_content, status_code, error_message)
        """
        parsed = urlparse(url)
        host = parsed.netloc
        
        # Enforce per-host rate limit
        async with self._semaphore:
            now = asyncio.get_event_loop().time()
            if host in self._host_last_request:
                elapsed = now - self._host_last_request[host]
                min_interval = 1.0 / self.rate_limit_per_host
                if elapsed < min_interval:
                    await asyncio.sleep(min_interval - elapsed)
            
            self._host_last_request[host] = asyncio.get_event_loop().time()
            
            # Create client with SSRF protection
            transport = SSRFProtectedTransport()
            async with httpx.AsyncClient(
                transport=transport,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
                max_redirects=3,
            ) as client:
                for attempt in range(self.max_retries + 1):
                    try:
                        response = await client.get(
                            url,
                            headers={
                                "User-Agent": "web-similarity-audit/0.1.0 (SEO audit tool)",
                                "Accept": "text/html,application/xhtml+xml",
                                "Accept-Language": "en-US,en;q=0.9",
                            },
                        )
                        
                        # Check response size
                        if "content-length" in response.headers:
                            size = int(response.headers["content-length"])
                            if size > self.max_response_size:
                                return None, response.status_code, f"Response too large: {size} bytes"
                        
                        # Read with size limit
                        content = b""
                        async for chunk in response.aiter_bytes():
                            content += chunk
                            if len(content) > self.max_response_size:
                                return None, response.status_code, f"Response exceeded {self.max_response_size} bytes"
                        
                        # Decode
                        try:
                            html = content.decode(response.encoding or "utf-8")
                        except UnicodeDecodeError:
                            html = content.decode("utf-8", errors="replace")
                        
                        return html, response.status_code, None
                    
                    except httpx.HTTPStatusError as e:
                        if attempt == self.max_retries:
                            return None, e.response.status_code, f"HTTP {e.response.status_code}"
                    except httpx.RequestError as e:
                        if attempt == self.max_retries:
                            return None, None, str(e)
                    except Exception as e:
                        if attempt == self.max_retries:
                            return None, None, f"Unexpected error: {e}"
                    
                    # Exponential backoff
                    if attempt < self.max_retries:
                        await asyncio.sleep(2 ** attempt)
        
        return None, None, "Max retries exceeded"
    
    async def fetch_all(self, urls: list[str]) -> list[tuple[str, Optional[str], Optional[int], Optional[str]]]:
        """
        Fetch multiple URLs concurrently.
        
        Returns:
            List of (url, html_content, status_code, error_message)
        """
        tasks = [self.fetch(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return [(url, *result) for url, result in zip(urls, results)]
