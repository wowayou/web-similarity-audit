"""Tests for extraction precedence and normalization edge cases (v0.2.1)."""

import unicodedata

from web_similarity_audit.extractor import ContentExtractor
from web_similarity_audit.models import PageInput


# ---------------------------------------------------------------------------
# Extraction precedence: selector > markers > trafilatura > body fallback
# ---------------------------------------------------------------------------

def test_selector_takes_precedence_over_markers():
    """When both selector and markers are provided, selector wins."""
    html = """
    <html><body>
        <div id="main">Selector content here</div>
        <!-- START -->
        <div>Marker content here</div>
        <!-- END -->
    </body></html>
    """
    extractor = ContentExtractor()
    page_input = PageInput(
        url="http://test.com",
        selector="#main",
        start_marker="<!-- START -->",
        end_marker="<!-- END -->",
    )
    result = extractor.extract(html, page_input, 200)

    assert result.extraction_method == "selector"
    assert "selector content" in result.main_content.lower()
    assert "marker content" not in result.main_content.lower()


def test_markers_used_when_no_selector():
    """Markers are used when selector is absent."""
    html = """
    <html><body>
        <div>Noise</div>
        <!-- START -->
        <div>Marker content here</div>
        <!-- END -->
    </body></html>
    """
    extractor = ContentExtractor()
    page_input = PageInput(
        url="http://test.com",
        start_marker="<!-- START -->",
        end_marker="<!-- END -->",
    )
    result = extractor.extract(html, page_input, 200)

    assert result.extraction_method == "markers"
    assert "marker content" in result.main_content.lower()


def test_selector_failure_is_explicit_and_does_not_fall_through():
    """A provided-but-missing selector fails explicitly (no silent fallback)."""
    html = "<html><body><!-- START --><p>Content</p><!-- END --></body></html>"
    extractor = ContentExtractor()
    page_input = PageInput(
        url="http://test.com",
        selector="#does-not-exist",
        start_marker="<!-- START -->",
        end_marker="<!-- END -->",
    )
    result = extractor.extract(html, page_input, 200)

    assert result.extraction_method == "selector_failed"
    assert result.extraction_confident is False
    assert result.error is not None


# ---------------------------------------------------------------------------
# NFKC normalization: full-width vs half-width model numbers
# ---------------------------------------------------------------------------

def test_fullwidth_model_number_normalized_to_ascii():
    """Full-width model numbers are NFKC-normalized to ASCII form."""
    html = "<html><body><article><p>产品型号：ＣＷＢ－１５９</p>" \
           "<p>规格：１５トン</p></article></body></html>"

    extractor = ContentExtractor()
    result = extractor.extract(html, PageInput(url="http://test.com"), 200)

    assert result.has_cjk
    # Full-width ASCII letters/digits normalize to half-width.
    assert "CWB" in result.main_content
    assert "159" in result.main_content


def test_fullwidth_and_halfwidth_numbers_compare_equal():
    """Full-width and half-width forms of the same model produce identical hashes."""
    extractor = ContentExtractor()

    fullwidth = "<html><body><article><p>Model ＣＷＢ－１５９ specs</p></article></body></html>"
    halfwidth = "<html><body><article><p>Model CWB-159 specs</p></article></body></html>"

    r1 = extractor.extract(fullwidth, PageInput(url="http://a.com"), 200)
    r2 = extractor.extract(halfwidth, PageInput(url="http://b.com"), 200)

    assert r1.sha256 == r2.sha256, (
        "Full-width and half-width forms should normalize identically"
    )


def test_nfkc_is_idempotent_on_normalized_text():
    """Applying NFKC twice yields the same result (stability guarantee)."""
    text = "ＣＷＢ－１５９　規格　１２３"
    once = unicodedata.normalize("NFKC", text)
    twice = unicodedata.normalize("NFKC", once)
    assert once == twice
