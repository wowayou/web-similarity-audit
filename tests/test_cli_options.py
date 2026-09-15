"""CLI option validation tests."""

import sys

from web_similarity_audit.cli import main


def test_max_pages_has_safe_upper_bound(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "web-similarity-audit",
            "--crawl",
            "https://example.com/",
            "--max-pages",
            "1001",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert main() == 1
