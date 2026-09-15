"""Tests that make SSRF enforcement regressions observable."""

import asyncio
import functools
import http.server
import threading

import httpx
import pytest

from web_similarity_audit.crawler import WebsiteCrawler
from web_similarity_audit.fetcher import (
    PageFetcher,
    SSRFBlockedError,
    SSRFProtectedTransport,
)


@pytest.fixture()
def local_site(tmp_path):
    """Serve twelve local HTML pages for protected/unprotected contrast."""
    root = tmp_path / "site"
    root.mkdir()
    page_names = [f"page{number}.html" for number in range(1, 12)]
    links = "".join(f'<a href="/{name}">{name}</a>' for name in page_names)
    (root / "index.html").write_text(
        f"<html><body>{links}<p>index content</p></body></html>", encoding="utf-8"
    )
    for name in page_names:
        (root / name).write_text(
            f"<html><body><p>{name} content</p></body></html>", encoding="utf-8"
        )
    (root / "robots.txt").write_text("User-agent: *\\nDisallow:\\n", encoding="utf-8")
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.asyncio
async def test_fetch_and_crawler_require_explicit_private_opt_in(local_site):
    """If PageFetcher stops creating its protected transport, this fails."""
    page_url = f"{local_site}/index.html"
    protected_fetcher = PageFetcher(max_retries=0)
    html, status, error = await protected_fetcher.fetch(page_url)
    assert (html, status) == (None, None)
    assert error.startswith("SSRF protection")

    private_fetcher = PageFetcher(
        allow_private=True, max_retries=0, rate_limit_per_host=50
    )
    html, status, error = await private_fetcher.fetch(page_url)
    assert error is None
    assert status == 200
    assert "index content" in html

    protected_crawler = WebsiteCrawler(max_pages=20, rate_limit=50, max_concurrent=4)
    assert await protected_crawler.crawl(page_url) == []
    private_crawler = WebsiteCrawler(
        max_pages=20, rate_limit=50, max_concurrent=4, allow_private=True
    )
    assert len(await private_crawler.crawl(page_url)) == 12


@pytest.mark.asyncio
async def test_dns_preflight_rejects_mixed_answers_and_allows_public(monkeypatch):
    loop = asyncio.get_running_loop()

    async def mixed_answers(host, port, **kwargs):
        return [
            (2, 1, 6, "", ("93.184.216.34", port)),
            (2, 1, 6, "", ("10.0.0.5", port)),
        ]

    monkeypatch.setattr(loop, "getaddrinfo", mixed_answers)
    transport = SSRFProtectedTransport()
    request = httpx.Request("GET", "http://a.example/")
    with pytest.raises(SSRFBlockedError, match="10.0.0.5"):
        await transport.handle_async_request(request)

    async def public_answers(host, port, **kwargs):
        return [(2, 1, 6, "", ("93.184.216.34", port))]

    async def allow_request(self, request):
        return httpx.Response(200, request=request, text="ok")

    monkeypatch.setattr(loop, "getaddrinfo", public_answers)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", allow_request)
    response = await transport.handle_async_request(request)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_redirect_to_private_address_is_rejected(monkeypatch):
    loop = asyncio.get_running_loop()

    async def answers(host, port, **kwargs):
        address = "93.184.216.34" if host == "a.example" else "127.0.0.1"
        return [(2, 1, 6, "", (address, port))]

    async def redirecting_request(self, request):
        if request.headers["host"] == "a.example":
            return httpx.Response(
                302, headers={"location": "http://b.example/"}, request=request
            )
        raise AssertionError("private redirect must not reach the base transport")

    monkeypatch.setattr(loop, "getaddrinfo", answers)
    monkeypatch.setattr(
        httpx.AsyncHTTPTransport, "handle_async_request", redirecting_request
    )
    html, status, error = await PageFetcher(max_retries=0).fetch("http://a.example/")
    assert (html, status) == (None, None)
    assert "SSRF protection" in error
    assert "b.example" in error
