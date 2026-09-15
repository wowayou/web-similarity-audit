"""Tests that extraction produces real content blocks.

Regression guard: block splitting must happen on the raw extracted text
(before whitespace collapsing), otherwise every page degenerates to a
single block and template detection / block overlap become dead signals.
"""

from web_similarity_audit.extractor import ContentExtractor
from web_similarity_audit.models import PageInput
from web_similarity_audit.template import TemplateDetector

SHARED_DISCLAIMER = (
    "All content on this site is licensed under the example license terms "
    "of Example Corp and may not be redistributed without permission."
)


def _article_html(paragraphs: list[str]) -> str:
    body = "".join(f"<p>{p}</p>" for p in paragraphs)
    return f"<html><body><article>{body}</article></body></html>"


def test_trafilatura_multi_paragraph_article_yields_blocks():
    """A 12-paragraph article must yield many blocks, not one."""
    paragraphs = [
        f"Unique paragraph {i} discusses topic {i} with entirely distinct "
        f"wording, reference number {i * 7}, and commentary that differs "
        f"from every other section of the article."
        for i in range(12)
    ]
    result = ContentExtractor().extract(
        _article_html(paragraphs), PageInput(url="https://example.com/a"), 200
    )

    assert result.extraction_method == "trafilatura"
    assert result.block_count >= 6
    assert len(result.blocks) == result.block_count
    # Blocks are normalized: no internal newlines or runs of spaces.
    assert all("\n" not in b and "  " not in b for b in result.blocks)


def test_selector_extraction_splits_paragraphs():
    paragraphs = [
        f"Selector paragraph {i} carries distinct wording set {i} for the "
        f"block splitting check." for i in range(6)
    ]
    html = (
        "<html><body><div id='main'>"
        + "".join(f"<p>{p}</p>" for p in paragraphs)
        + "</div></body></html>"
    )
    result = ContentExtractor().extract(
        html, PageInput(url="https://example.com/b", selector="#main"), 200
    )

    assert result.extraction_method == "selector"
    assert result.block_count >= 4


def test_body_fallback_splits_paragraphs():
    """Even the uncertain body fallback must produce per-paragraph blocks."""
    # Short content that trafilatura declines (below the 100-char threshold),
    # forcing the body-fallback path. Written as minified HTML to also cover
    # block-boundary insertion when the source has no whitespace.
    html = (
        "<html><body>"
        "<p>Fallback paragraph one.</p>"
        "<p>Fallback paragraph two.</p>"
        "<p>Fallback paragraph three.</p>"
        "</body></html>"
    )
    result = ContentExtractor().extract(html, PageInput(url="https://example.com/c"), 200)

    assert result.extraction_method == "body_fallback"
    assert result.block_count == 3


def test_shared_disclaimer_detected_as_common_block():
    """Pages sharing one paragraph must yield a detectable common block."""
    pages = []
    for i in range(6):
        paragraphs = [
            f"Article {i} opening paragraph with its own subject matter "
            f"{i} and supporting details that are unique to this page.",
            SHARED_DISCLAIMER,
            f"Article {i} closing paragraph with different concluding "
            f"remarks {i} and a unique sign-off.",
        ]
        pages.append(ContentExtractor().extract(
            _article_html(paragraphs), PageInput(url=f"https://example.com/{i}"), 200
        ))

    common = TemplateDetector(min_pages=5, threshold=0.6).detect_common_blocks(pages)
    assert common, "template detection returned an empty set for pages with shared content"
    assert any("example license" in block for block in common)
