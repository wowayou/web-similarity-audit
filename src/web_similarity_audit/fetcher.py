"""HTTP fetching with URL validation, SSRF checks, and resource limits."""

from __future__ import annotations

import asyncio
import ipaddress
import os
import socket
import ssl
from functools import lru_cache
from typing import Optional
from urllib.parse import ParseResult, urlparse

import certifi
import httpx

from . import __version__

USER_AGENT = f"web-similarity-audit/{__version__} (SEO audit tool)"


@lru_cache(maxsize=1)
def default_verify_context() -> ssl.SSLContext:
    """Build and cache the default certificate-verification context."""
    ca_file = os.environ.get("SSL_CERT_FILE")
    ca_dir = os.environ.get("SSL_CERT_DIR")
    if ca_file:
        return ssl.create_default_context(cafile=ca_file)
    if ca_dir:
        return ssl.create_default_context(capath=ca_dir)
    return ssl.create_default_context(cafile=certifi.where())


def validate_http_url(url: str) -> ParseResult:
    """Validate a fetch target and return its parsed representation.

    Validation happens inside the fetcher as well as at the CLI boundary so
    library callers cannot bypass it accidentally.
    """
    if not isinstance(url, str) or not url:
        raise ValueError("URL must be a non-empty string")

    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("only http:// and https:// URLs are supported")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("credentials in URLs are not allowed")
    try:
        _ = parsed.port
    except ValueError as exc:
        raise ValueError(f"invalid URL port: {exc}") from exc
    return parsed


def is_public_ip(value: str) -> bool:
    """Return whether *value* is globally routable unicast IP space."""
    try:
        address = ipaddress.ip_address(value)
        return address.is_global and not address.is_multicast
    except ValueError:
        return False


class SSRFBlockedError(httpx.ConnectError):
    """A deterministic policy rejection that must not be retried."""


class SSRFProtectedTransport(httpx.AsyncHTTPTransport):
    """Reject targets whose DNS answers include non-public addresses.

    Every redirect is a separate HTTPX request and is checked again. The
    transport disables environment proxies: a proxy would move DNS resolution
    outside this process and invalidate the local preflight check.

    The outbound connection is pinned to a DNS answer that passed validation.
    Deployments accepting hostile URLs should still enforce outbound firewall
    rules as defense in depth.
    """

    def __init__(self) -> None:
        super().__init__(verify=default_verify_context(), trust_env=False)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Validate every resolved address before allowing the request."""
        host = request.url.host
        if not host:
            raise SSRFBlockedError(
                "SSRF protection: target has no hostname", request=request
            )

        try:
            addrinfo = await asyncio.get_running_loop().getaddrinfo(
                host,
                request.url.port,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise httpx.ConnectError(
                f"DNS resolution failed for {host}: {exc}", request=request
            ) from exc

        addresses = {sockaddr[0] for _, _, _, _, sockaddr in addrinfo}
        if not addresses:
            raise httpx.ConnectError(
                f"DNS resolution returned no addresses for {host}", request=request
            )

        blocked = sorted(address for address in addresses if not is_public_ip(address))
        if blocked:
            raise SSRFBlockedError(
                f"SSRF protection: {host} resolves to non-public IP {blocked[0]}",
                request=request,
            )

        # Connect to the vetted answer, not a second DNS lookup. HTTPX keeps
        # the existing Host header; SNI and certificate validation retain the
        # original hostname through the httpcore extension.
        selected_address = sorted(addresses)[0]
        request.url = request.url.copy_with(host=selected_address)
        request.extensions["sni_hostname"] = host
        return await super().handle_async_request(request)


class PageFetcher:
    """Fetch web pages with rate limiting and SSRF protection."""

    def __init__(
        self,
        max_response_size: int = 2 * 1024 * 1024,
        timeout: float = 10.0,
        max_retries: int = 2,
        rate_limit_per_host: float = 2.0,
        max_concurrent: int = 4,
        allow_private: bool = False,
    ) -> None:
        if max_response_size <= 0:
            raise ValueError("max_response_size must be greater than zero")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if rate_limit_per_host <= 0:
            raise ValueError("rate_limit_per_host must be greater than zero")
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be greater than zero")

        self.max_response_size = max_response_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_per_host = rate_limit_per_host
        self.max_concurrent = max_concurrent
        self.allow_private = allow_private

        self._host_locks: dict[str, asyncio.Lock] = {}
        self._host_last_request: dict[str, float] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def _wait_for_rate_limit(self, host: str) -> None:
        """Serialize request starts per host and enforce the configured RPS."""
        lock = self._host_locks.setdefault(host, asyncio.Lock())
        async with lock:
            loop = asyncio.get_running_loop()
            previous = self._host_last_request.get(host)
            if previous is not None:
                delay = (1.0 / self.rate_limit_per_host) - (loop.time() - previous)
                if delay > 0:
                    await asyncio.sleep(delay)
            self._host_last_request[host] = loop.time()

    def _transport(self) -> httpx.AsyncBaseTransport | None:
        if self.allow_private:
            return None
        return SSRFProtectedTransport()

    async def fetch(
        self,
        url: str,
        *,
        require_html: bool = True,
        user_agent: str = USER_AGENT,
    ) -> tuple[Optional[str], Optional[int], Optional[str]]:
        """Fetch one URL and return ``(text, status, error)``."""
        try:
            parsed = validate_http_url(url)
        except ValueError as exc:
            return None, None, f"Invalid URL: {exc}"

        host_key = parsed.netloc.lower()
        async with self._semaphore:
            await self._wait_for_rate_limit(host_key)

            transport = self._transport()
            client_kwargs: dict = {
                "timeout": httpx.Timeout(self.timeout),
                "follow_redirects": True,
                "max_redirects": 3,
                "trust_env": False,
            }
            if transport is None:
                client_kwargs["verify"] = default_verify_context()
            else:
                client_kwargs["transport"] = transport

            async with httpx.AsyncClient(**client_kwargs) as client:
                for attempt in range(self.max_retries + 1):
                    try:
                        async with client.stream(
                            "GET",
                            url,
                            headers={
                                "User-Agent": user_agent,
                                "Accept": (
                                    "text/html,application/xhtml+xml"
                                    if require_html
                                    else "text/plain,*/*;q=0.1"
                                ),
                                "Accept-Language": "en-US,en;q=0.9",
                                "Accept-Encoding": "identity",
                            },
                        ) as response:
                            content_encoding = response.headers.get(
                                "content-encoding", "identity"
                            ).strip().lower()
                            if content_encoding not in {"", "identity"}:
                                return (
                                    None,
                                    response.status_code,
                                    f"Unsupported content encoding: {content_encoding}",
                                )

                            content_type = response.headers.get("content-type", "")
                            media_type = content_type.partition(";")[0].strip().lower()
                            if require_html and media_type not in {
                                "text/html",
                                "application/xhtml+xml",
                            }:
                                return (
                                    None,
                                    response.status_code,
                                    f"Unsupported content type: {media_type or 'missing'}",
                                )

                            content_length = response.headers.get("content-length")
                            if content_length is not None:
                                try:
                                    announced_size = int(content_length)
                                except ValueError:
                                    announced_size = None
                                if (
                                    announced_size is not None
                                    and announced_size > self.max_response_size
                                ):
                                    return (
                                        None,
                                        response.status_code,
                                        f"Response too large: {announced_size} bytes",
                                    )

                            chunks: list[bytes] = []
                            received = 0
                            async for chunk in response.aiter_bytes():
                                received += len(chunk)
                                if received > self.max_response_size:
                                    return (
                                        None,
                                        response.status_code,
                                        "Response exceeded "
                                        f"{self.max_response_size} bytes",
                                    )
                                chunks.append(chunk)

                            content = b"".join(chunks)
                            encoding = response.encoding or "utf-8"
                            try:
                                text = content.decode(encoding)
                            except (LookupError, UnicodeDecodeError):
                                text = content.decode("utf-8", errors="replace")
                            return text, response.status_code, None

                    except SSRFBlockedError as exc:
                        return None, None, str(exc)
                    except httpx.RequestError as exc:
                        if attempt == self.max_retries:
                            return None, None, str(exc)
                    except Exception as exc:
                        if attempt == self.max_retries:
                            return None, None, f"Unexpected error: {exc}"

                    if attempt < self.max_retries:
                        await asyncio.sleep(2**attempt)

        return None, None, "Max retries exceeded"

    async def fetch_all(
        self, urls: list[str]
    ) -> list[tuple[str, Optional[str], Optional[int], Optional[str]]]:
        """Fetch multiple URLs concurrently, preserving input order."""
        results = await asyncio.gather(*(self.fetch(url) for url in urls))
        return [(url, *result) for url, result in zip(urls, results, strict=True)]
