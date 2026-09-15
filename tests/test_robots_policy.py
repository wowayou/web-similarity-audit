"""Crawler behavior when robots.txt is unavailable or throttles requests."""

import pytest

import web_similarity_audit.crawler as crawler_module
from web_similarity_audit.crawler import WebsiteCrawler


class FakeFetcher:
    def __init__(self, robots_result):
        self.robots_result = robots_result
        self.minimum_intervals = {}

    async def fetch(self, url, **kwargs):
        if url.endswith("/robots.txt"):
            return self.robots_result
        return "<html><body>page</body></html>", 200, None

    def set_host_min_interval(self, host, seconds):
        self.minimum_intervals[host] = seconds


@pytest.mark.asyncio
async def test_robots_server_error_denies_crawl(monkeypatch):
    fake = FakeFetcher((None, 500, "server error"))
    monkeypatch.setattr(crawler_module, "PageFetcher", lambda **kwargs: fake)

    crawler = WebsiteCrawler(max_pages=2)
    assert await crawler.crawl("https://example.com/") == []
    assert crawler.robots_warnings == [
        "robots.txt unavailable for example.com (status 500); crawling denied"
    ]


@pytest.mark.asyncio
async def test_robots_not_found_allows_crawl(monkeypatch):
    fake = FakeFetcher((None, 404, "not found"))
    monkeypatch.setattr(crawler_module, "PageFetcher", lambda **kwargs: fake)

    crawler = WebsiteCrawler(max_pages=2)
    assert await crawler.crawl("https://example.com/") == ["https://example.com/"]
    assert crawler.robots_warnings == []


@pytest.mark.asyncio
async def test_crawl_delay_sets_host_minimum_interval(monkeypatch):
    fake = FakeFetcher(("User-agent: *\nCrawl-delay: 1\nDisallow:\n", 200, None))
    monkeypatch.setattr(crawler_module, "PageFetcher", lambda **kwargs: fake)

    crawler = WebsiteCrawler(max_pages=2, rate_limit=50)
    assert await crawler.crawl("https://example.com/") == ["https://example.com/"]
    assert fake.minimum_intervals == {"example.com": 1.0}


@pytest.mark.asyncio
async def test_robots_429_denies_crawl(monkeypatch):
    fake = FakeFetcher((None, 429, "rate limited"))
    monkeypatch.setattr(crawler_module, "PageFetcher", lambda **kwargs: fake)

    crawler = WebsiteCrawler(max_pages=2)
    assert await crawler.crawl("https://example.com/") == []
    assert crawler.robots_warnings == [
        "robots.txt unavailable for example.com (status 429); crawling denied"
    ]


@pytest.mark.asyncio
async def test_robots_redirect_denies_crawl(monkeypatch):
    fake = FakeFetcher((None, 302, "redirect"))
    monkeypatch.setattr(crawler_module, "PageFetcher", lambda **kwargs: fake)

    crawler = WebsiteCrawler(max_pages=2)
    assert await crawler.crawl("https://example.com/") == []
    assert crawler.robots_warnings == [
        "robots.txt unavailable for example.com (status 302); crawling denied"
    ]


@pytest.mark.asyncio
async def test_negative_crawl_delay_is_ignored(monkeypatch):
    robots = chr(10).join(["User-agent: *", "Crawl-delay: -1", "Disallow:", ""])
    fake = FakeFetcher((robots, 200, None))
    monkeypatch.setattr(crawler_module, "PageFetcher", lambda **kwargs: fake)

    crawler = WebsiteCrawler(max_pages=2, rate_limit=50)
    assert await crawler.crawl("https://example.com/") == ["https://example.com/"]
    assert fake.minimum_intervals == {}
    assert any("negative Crawl-delay" in warning for warning in crawler.robots_warnings)


@pytest.mark.asyncio
async def test_oversized_crawl_delay_is_capped(monkeypatch):
    robots = chr(10).join(["User-agent: *", "Crawl-delay: 999999", "Disallow:", ""])
    fake = FakeFetcher((robots, 200, None))
    monkeypatch.setattr(crawler_module, "PageFetcher", lambda **kwargs: fake)

    crawler = WebsiteCrawler(max_pages=2, rate_limit=50)
    assert await crawler.crawl("https://example.com/") == ["https://example.com/"]
    assert fake.minimum_intervals == {"example.com": 3600.0}
    assert any("capping" in warning for warning in crawler.robots_warnings)
