"""Regression tests for network and output security boundaries."""

import asyncio
import gzip
import zlib
import json

import httpx
import pytest

from web_similarity_audit.cli import main
from web_similarity_audit.crawler import WebsiteCrawler
from web_similarity_audit.fetcher import PageFetcher, is_public_ip
from web_similarity_audit.models import PageResult, SimilarityScore
from web_similarity_audit.reporter import Reporter


class _ChunkStream(httpx.AsyncByteStream):
    def __init__(self, chunks):
        self.chunks = chunks

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk


class _NeverReadStream(httpx.AsyncByteStream):
    async def __aiter__(self):
        raise AssertionError("compressed response body must not be read")
        yield b""  # pragma: no cover


def test_non_public_address_classes_are_blocked():
    assert is_public_ip("8.8.8.8") is True
    for address in (
        "127.0.0.1", "169.254.169.254", "10.0.0.1", "100.64.0.1",
        "224.0.0.1", "::1", "fe80::1",
    ):
        assert is_public_ip(address) is False


def test_explicit_deny_list_blocks_version_sensitive_ranges():
    """Ranges stdlib is_global has classified inconsistently across versions."""
    for address in (
        "100.64.0.1",  # CGNAT: CVE-2024-4032 changed is_global semantics
        "198.18.0.1",  # benchmarking
        "240.0.0.1",  # reserved
        "64:ff9b::10.0.0.1",  # NAT64 embedding a private IPv4
        "64:ff9b::169.254.169.254",  # NAT64 embedding a metadata endpoint
        "::ffff:10.0.0.1",  # IPv4-mapped private
    ):
        assert is_public_ip(address) is False, address


def test_mapped_and_nat64_public_targets_remain_allowed():
    assert is_public_ip("::ffff:8.8.8.8") is True
    assert is_public_ip("64:ff9b::808:808") is True  # NAT64 of 8.8.8.8


@pytest.mark.asyncio
async def test_crawler_uses_ssrf_protection_by_default():
    crawler = WebsiteCrawler(
        max_pages=1,
        max_concurrent=1,
        rate_limit=100,
    )
    assert await crawler.crawl("http://127.0.0.1:9/") == []


@pytest.mark.asyncio
async def test_fetch_rejects_credentials_and_invalid_port():
    fetcher = PageFetcher(max_retries=0)
    for url in ("https://user:pass@example.com/", "https://example.com:bad/"):
        html, status, error = await fetcher.fetch(url)
        assert html is None
        assert status is None
        assert error.startswith("Invalid URL:")


@pytest.mark.asyncio
async def test_streaming_limit_applies_without_content_length(monkeypatch):
    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            stream=_ChunkStream([b"<html>", b"x" * 64, b"</html>"]),
        )

    fetcher = PageFetcher(max_response_size=32, max_retries=0)
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(fetcher, "_transport", lambda: transport)

    html, status, error = await fetcher.fetch("https://example.com/")
    assert html is None
    assert status == 200
    assert "exceeded 32 bytes" in error


@pytest.mark.asyncio
async def test_fetch_all_honors_concurrency_limit(monkeypatch):
    active = 0
    peak = 0

    async def handler(request):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.02)
        active -= 1
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            stream=_ChunkStream([b"<html>ok</html>"]),
        )

    fetcher = PageFetcher(max_concurrent=2, rate_limit_per_host=100, max_retries=0)
    monkeypatch.setattr(fetcher, "_transport", lambda: httpx.MockTransport(handler))
    results = await fetcher.fetch_all(
        [f"https://host{i}.example/" for i in range(4)]
    )
    assert peak == 2
    assert all(result[1] == "<html>ok</html>" for result in results)


@pytest.mark.asyncio
async def test_brotli_response_is_rejected_before_body_read(monkeypatch):
    async def handler(request):
        return httpx.Response(
            200,
            headers={
                "content-type": "text/html",
                "content-encoding": "br",
            },
            stream=_NeverReadStream(),
        )

    fetcher = PageFetcher(max_retries=0)
    monkeypatch.setattr(fetcher, "_transport", lambda: httpx.MockTransport(handler))
    html, status, error = await fetcher.fetch("https://example.com/")
    assert (html, status) == (None, 200)
    assert error == "Unsupported content encoding: br"


def test_invalid_numeric_cli_option_fails_before_network(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["web-similarity-audit", "https://a.example", "https://b.example",
         "--rate-limit", "0"],
    )
    assert main() == 1


def test_report_counts_failures_and_escapes_markdown(tmp_path):
    pages = [
        PageResult(
            url="https://example.com/fallback",
            error="uncertain fallback",
            extraction_method="body_fallback",
        ),
        PageResult(
            url="https://example.com/a|b",
            error="network | failure",
            extraction_method="fetch_failed",
        ),
    ]
    score = SimilarityScore(
        url1="https://example.com/a|b",
        url2="https://example.com/c",
        priority="P1",
        trigger_reasons=["reason | detail"],
    )
    reporter = Reporter(tmp_path)
    reporter.write_pages_json(pages)
    reporter.write_markdown_report(pages, [score], None, 0.1)

    summary = json.loads((tmp_path / "pages.json").read_text())["summary"]
    assert summary == {"total": 2, "successful": 0, "uncertain": 1, "failed": 1}
    report = (tmp_path / "report.md").read_text()
    assert "a\\|b" in report
    assert "network \\| failure" in report


def test_clean_zero_scores_are_not_serialized_as_missing():
    score = SimilarityScore(
        url1="https://a.example",
        url2="https://b.example",
        jaccard_3gram_clean=0.0,
        tfidf_cosine_clean=0.0,
        block_overlap_clean=0.0,
    )
    data = score.to_dict()
    assert data["jaccard_3gram_clean"] == 0.0
    assert data["tfidf_cosine_clean"] == 0.0
    assert data["block_overlap_clean"] == 0.0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content_encoding", "compress"),
    [("gzip", gzip.compress), ("deflate", zlib.compress)],
)
async def test_bounded_compression_decodes_supported_encodings(
    monkeypatch, content_encoding, compress
):
    payload = b"<html><body>compressed page</body></html>"
    encoded = compress(payload)

    async def handler(request):
        return httpx.Response(
            200,
            headers={
                "content-type": "text/html",
                "content-encoding": content_encoding,
            },
            stream=_ChunkStream([encoded]),
        )

    fetcher = PageFetcher(max_retries=0)
    monkeypatch.setattr(fetcher, "_transport", lambda: httpx.MockTransport(handler))

    html, status, error = await fetcher.fetch("https://example.com/")
    assert (html, status, error) == (payload.decode(), 200, None)


@pytest.mark.asyncio
async def test_compressed_expansion_obeys_response_limit(monkeypatch):
    payload = b"<html><body>" + (b"x" * 10000) + b"</body></html>"
    encoded = gzip.compress(payload)

    async def handler(request):
        return httpx.Response(
            200,
            headers={
                "content-type": "text/html",
                "content-encoding": "gzip",
            },
            stream=_ChunkStream([encoded]),
        )

    fetcher = PageFetcher(max_response_size=1024, max_retries=0)
    monkeypatch.setattr(fetcher, "_transport", lambda: httpx.MockTransport(handler))

    html, status, error = await fetcher.fetch("https://example.com/")
    assert html is None
    assert status == 200
    assert "exceeded 1024 bytes" in error


def test_negative_host_interval_is_ignored():
    fetcher = PageFetcher()
    fetcher.set_host_min_interval("example.com", -1)
    assert fetcher._host_min_intervals == {}
