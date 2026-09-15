"""Tests for crash-recovery state persistence (save/load round-trip)."""

import time

from web_similarity_audit.models import PageResult
from web_similarity_audit.state import StateManager


def _sample_page(url: str, content: str) -> PageResult:
    return PageResult(
        url=url,
        status_code=200,
        extraction_method="trafilatura",
        extraction_confident=True,
        main_content=content,
        main_content_length=len(content),
        sha256=f"hash-{url[-1]}",
        blocks=[content],
        block_count=1,
        word_count=len(content.split()),
        has_cjk=False,
    )


def test_save_and_load_roundtrip_preserves_page_fields(tmp_path):
    """save_state must serialize every PageResult field without crashing."""
    sm = StateManager(tmp_path)
    pages = [
        _sample_page("https://example.com/a", "alpha page content"),
        _sample_page("https://example.com/b", "beta page content here"),
    ]

    sm.save_state(
        start_url="https://example.com/a",
        fetched_urls=["https://example.com/a", "https://example.com/b"],
        pages=pages,
        start_time=time.time(),
    )

    state = sm.load_state()
    assert state is not None
    assert state.fetched_urls == ["https://example.com/a", "https://example.com/b"]

    restored = sm.pages_from_state(state)
    assert len(restored) == 2
    for orig, back in zip(pages, restored):
        assert back.url == orig.url
        assert back.status_code == orig.status_code
        assert back.extraction_method == orig.extraction_method
        assert back.extraction_confident == orig.extraction_confident
        assert back.main_content == orig.main_content
        assert back.main_content_length == orig.main_content_length
        assert back.sha256 == orig.sha256
        assert back.blocks == orig.blocks
        assert back.block_count == orig.block_count
        assert back.word_count == orig.word_count
        assert back.has_cjk == orig.has_cjk


def test_planned_urls_roundtrip(tmp_path):
    """The full planned URL list must survive save/load so resume can
    fetch the pages that were never reached."""
    sm = StateManager(tmp_path)
    planned = [f"https://example.com/{i}" for i in range(12)]
    fetched = planned[:10]
    pages = [_sample_page(u, f"content of {u}") for u in fetched]
    planned_inputs = [
        {"url": url, "selector": "main", "start_marker": None, "end_marker": None}
        for url in planned
    ]

    sm.save_state(
        start_url=planned[0],
        fetched_urls=fetched,
        pages=pages,
        planned_urls=planned,
        planned_inputs=planned_inputs,
    )

    state = sm.load_state()
    assert state.planned_urls == planned
    assert state.planned_inputs == planned_inputs
    remaining = [u for u in state.planned_urls if u not in set(state.fetched_urls)]
    assert remaining == planned[10:]


def test_crawl_mode_flag_roundtrip(tmp_path):
    sm = StateManager(tmp_path)
    page = _sample_page("https://example.com/a", "content")
    sm.save_state(
        start_url="https://example.com/",
        fetched_urls=["https://example.com/a"],
        pages=[page],
        crawl_mode=True,
        planned_urls=["https://example.com/a", "https://example.com/b"],
    )

    state = sm.load_state()
    assert state.crawl_mode is True
    assert sm.pages_from_state(state)[0].url == "https://example.com/a"


def test_fetch_failed_page_roundtrip(tmp_path):
    """Fetch-failed pages (no content) survive the round-trip too."""
    sm = StateManager(tmp_path)
    failed = PageResult(
        url="https://example.com/x",
        status_code=None,
        error="connection refused",
        extraction_method="fetch_failed",
    )

    sm.save_state("https://example.com/x", ["https://example.com/x"], [failed])
    state = sm.load_state()
    back = sm.pages_from_state(state)[0]
    assert back.url == failed.url
    assert back.status_code is None
    assert back.error == "connection refused"
    assert back.extraction_method == "fetch_failed"
    assert back.extraction_confident is False
