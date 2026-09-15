"""End-to-end CLI tests against a local multi-page HTTP site.

These run the full pipeline (fetch -> extract -> template detection ->
similarity -> reports) through ``cli.main()`` against a 12-page site served
from a temp directory.  They require ``--allow-private`` because the site is
on 127.0.0.1, which the SSRF protection otherwise blocks.
"""

import asyncio
import functools
import http.server
import json
import threading

import pytest

from web_similarity_audit.cli import main
from web_similarity_audit.fetcher import PageFetcher
from web_similarity_audit.models import PageResult
from web_similarity_audit.state import StateManager

PAGE_COUNT = 12

SPEED_ARGS = ["--rate-limit", "50", "--max-concurrent", "4", "--timeout", "5"]


def _page_html(title: str, links: list[str]) -> str:
    paragraphs = "".join(
        f"<p>{title} paragraph {n}: this passage discusses subject {title}-{n} "
        f"with concrete details, the figure {n * 13}, and commentary unique "
        f"to this section of the site.</p>"
        for n in range(6)
    )
    nav = "".join(f'<a href="{href}">go to {href}</a>' for href in links)
    return (
        "<html><head><title>"
        f"{title}"
        "</title></head><body>"
        f"<nav><p>example corp site navigation menu</p></nav>"
        f"<div>{nav}</div>"
        f"<article>{paragraphs}</article>"
        f"<footer><p>copyright example corp all rights reserved</p></footer>"
        "</body></html>"
    )


@pytest.fixture()
def local_site(tmp_path):
    """Serve a 12-page site (+ robots.txt) on 127.0.0.1; yield the base URL."""
    root = tmp_path / "site"
    root.mkdir()

    # index links to every content page; content pages chain to the next one
    # so the crawler discovers exactly PAGE_COUNT URLs (never /index.html).
    page_paths = [f"/page{i}.html" for i in range(1, PAGE_COUNT)]
    (root / "index.html").write_text(
        _page_html("index", page_paths), encoding="utf-8"
    )
    for i, path in enumerate(page_paths):
        next_link = [page_paths[(i + 1) % len(page_paths)]]
        (root / path.lstrip("/")).write_text(
            _page_html(path, next_link), encoding="utf-8"
        )

    # The classic "allow everyone, block one bad bot" robots.txt pattern.
    (root / "robots.txt").write_text(
        "User-agent: *\nDisallow:\nUser-agent: BadBot\nDisallow: /\n",
        encoding="utf-8",
    )

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(root)
    )
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def _site_urls(base: str) -> list[str]:
    return [f"{base}/index.html"] + [f"{base}/page{i}.html" for i in range(1, PAGE_COUNT)]


def _read_summary(output_dir) -> dict:
    return json.loads((output_dir / "pages.json").read_text(encoding="utf-8"))["summary"]


def test_fetcher_allows_private_when_opted_in(local_site):
    """allow_private=True must permit loopback fetches (staging/intranet use)."""
    async def run():
        return await PageFetcher(allow_private=True).fetch(f"{local_site}/index.html")

    html, status, error = asyncio.run(run())
    assert error is None
    assert status == 200
    assert "paragraph" in html


def test_cli_list_mode_full_run(local_site, tmp_path, monkeypatch):
    """12 URLs must run to completion (state save at page 10 used to crash)."""
    out = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        ["web-similarity-audit", *_site_urls(local_site), "--output-dir", str(out),
         "--allow-private", *SPEED_ARGS],
    )

    rc = main()

    assert rc == 0
    summary = _read_summary(out)
    assert summary["total"] == PAGE_COUNT
    assert summary["successful"] == PAGE_COUNT
    # Multi-paragraph articles must be split into real blocks.
    pages = json.loads((out / "pages.json").read_text(encoding="utf-8"))["pages"]
    assert all(p["block_count"] >= 4 for p in pages)
    assert (out / "pairs.csv").exists()
    assert (out / "report.md").exists()
    assert not (out / ".audit_state.json").exists(), "state must be cleared on success"


def test_cli_crawl_mode_respects_allow_all_robots(local_site, tmp_path, monkeypatch):
    """The robots.txt trap (empty Disallow for *) must not block discovery."""
    out = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        ["web-similarity-audit", "--crawl", f"{local_site}/", "--max-pages", "20",
         "--output-dir", str(out), "--allow-private", *SPEED_ARGS],
    )

    rc = main()

    assert rc == 0
    assert _read_summary(out)["total"] == PAGE_COUNT


def _seed_state(output_dir, urls, fetched_count: int):
    sm = StateManager(output_dir)
    fetched = urls[:fetched_count]
    pages = [
        PageResult(
            url=u,
            status_code=200,
            extraction_method="trafilatura",
            extraction_confident=True,
            main_content=f"seeded content of {u}",
            main_content_length=len(f"seeded content of {u}"),
            sha256=f"seed-hash-{i}",
            blocks=[f"seeded content of {u}"],
            block_count=1,
            word_count=4,
        )
        for i, u in enumerate(fetched)
    ]
    sm.save_state(
        start_url=urls[0],
        fetched_urls=fetched,
        pages=pages,
        planned_urls=urls,
    )


def test_cli_resume_fetches_remaining_pages(local_site, tmp_path, monkeypatch):
    """--resume must fetch the pages the interrupted run never reached."""
    urls = _site_urls(local_site)
    out = tmp_path / "out"
    _seed_state(out, urls, fetched_count=10)

    monkeypatch.setattr(
        "sys.argv",
        ["web-similarity-audit", *urls, "--output-dir", str(out), "--resume",
         "--allow-private", *SPEED_ARGS],
    )

    rc = main()

    assert rc == 0
    assert _read_summary(out)["total"] == PAGE_COUNT


def test_cli_resume_with_nothing_remaining(local_site, tmp_path, monkeypatch):
    """--resume after every planned page was fetched must just report."""
    urls = _site_urls(local_site)
    out = tmp_path / "out"
    _seed_state(out, urls, fetched_count=PAGE_COUNT)

    monkeypatch.setattr(
        "sys.argv",
        ["web-similarity-audit", "--output-dir", str(out), "--resume",
         "--allow-private", *SPEED_ARGS],
    )

    rc = main()

    assert rc == 0
    assert _read_summary(out)["total"] == PAGE_COUNT
