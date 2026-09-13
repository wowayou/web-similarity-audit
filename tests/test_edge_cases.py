"""Test edge cases and error handling."""

import pytest
from web_similarity_audit.extractor import ContentExtractor
from web_similarity_audit.models import PageInput
from web_similarity_audit.template import TemplateDetector


def test_extraction_with_custom_selector():
    """Test CSS selector extraction."""
    html = """
    <html>
    <body>
        <nav>Navigation</nav>
        <div id="main">Main content here</div>
        <footer>Footer</footer>
    </body>
    </html>
    """
    
    extractor = ContentExtractor()
    page_input = PageInput(url="http://test.com", selector="#main")
    result = extractor.extract(html, page_input, 200)
    
    assert result.extraction_confident
    assert result.extraction_method == "selector"
    assert "main content" in result.main_content.lower()
    assert "navigation" not in result.main_content.lower()
    assert "footer" not in result.main_content.lower()


def test_extraction_with_markers():
    """Test start/end marker extraction."""
    html = """
    <html>
    <body>
        <div>Header stuff</div>
        <!-- START CONTENT -->
        <div>Important content</div>
        <!-- END CONTENT -->
        <div>Footer stuff</div>
    </body>
    </html>
    """
    
    extractor = ContentExtractor()
    page_input = PageInput(
        url="http://test.com",
        start_marker="<!-- START CONTENT -->",
        end_marker="<!-- END CONTENT -->",
    )
    result = extractor.extract(html, page_input, 200)
    
    assert result.extraction_confident
    assert result.extraction_method == "markers"
    assert "important content" in result.main_content.lower()
    assert "header stuff" not in result.main_content.lower()


def test_selector_not_found():
    """Test that missing selector is reported as failure."""
    html = "<html><body><p>Test</p></body></html>"
    
    extractor = ContentExtractor()
    page_input = PageInput(url="http://test.com", selector="#nonexistent")
    result = extractor.extract(html, page_input, 200)
    
    assert not result.extraction_confident
    assert result.extraction_method == "selector_failed"
    assert result.error is not None
    assert "not found" in result.error.lower()


def test_markers_not_found():
    """Test that missing markers are reported as failure."""
    html = "<html><body><p>Test</p></body></html>"
    
    extractor = ContentExtractor()
    page_input = PageInput(
        url="http://test.com",
        start_marker="<!-- MISSING -->",
        end_marker="<!-- ALSO MISSING -->",
    )
    result = extractor.extract(html, page_input, 200)
    
    assert not result.extraction_confident
    assert result.extraction_method == "markers_failed"
    assert result.error is not None


def test_template_detection_disabled_below_5():
    """Test that template detection is disabled for n<5."""
    from web_similarity_audit.models import PageResult
    
    detector = TemplateDetector(min_pages=5, threshold=0.6)
    
    pages = [
        PageResult(url=f"http://test.com/{i}", blocks=["common", f"unique{i}"])
        for i in range(4)
    ]
    
    result = detector.detect_common_blocks(pages)
    
    assert result is None  # Disabled


def test_template_detection_enabled_at_5():
    """Test that template detection works for n>=5."""
    from web_similarity_audit.models import PageResult
    
    detector = TemplateDetector(min_pages=5, threshold=0.6)
    
    # 5 pages, "common" appears in all 5, "header" in 4, "unique" in 1 each
    pages = [
        PageResult(url=f"http://test.com/{i}", blocks=["common", "header", f"unique{i}"])
        for i in range(4)
    ]
    pages.append(PageResult(url="http://test.com/4", blocks=["common", "unique4"]))
    
    result = detector.detect_common_blocks(pages)
    
    # "common" appears in 5/5 (100%) - should be detected
    # "header" appears in 4/5 (80%) - should be detected
    # "uniqueX" appears in 1/5 (20%) - should NOT be detected
    assert result is not None
    assert "common" in result
    assert "header" in result
    assert "unique0" not in result


def test_cjk_text_normalization():
    """Test NFKC normalization handles CJK correctly."""
    html = """
    <html>
    <body>
        <p>产品型号：ＣＷＢ－１５９</p>
        <p>規格：１５トン</p>
    </body>
    </html>
    """
    
    extractor = ContentExtractor()
    page_input = PageInput(url="http://test.com")
    result = extractor.extract(html, page_input, 200)
    
    assert result.has_cjk
    # NFKC should normalize full-width chars to half-width
    assert "CWB" in result.main_content  # Full-width ＣＷＢ → CWB
    assert "15" in result.main_content   # Full-width １５ → 15
