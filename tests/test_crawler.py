"""Test crawler functionality."""

import pytest

from web_similarity_audit.crawler import WebsiteCrawler


@pytest.mark.asyncio
async def test_normalize_url():
    """Test URL normalization."""
    crawler = WebsiteCrawler(max_pages=10)
    
    # Remove fragment
    assert crawler._normalize_url("https://example.com/page#section") == "https://example.com/page"
    
    # Remove trailing slash (non-root)
    assert crawler._normalize_url("https://example.com/page/") == "https://example.com/page"
    
    # Keep trailing slash for root
    assert crawler._normalize_url("https://example.com/") == "https://example.com/"
    
    # Preserve query
    assert crawler._normalize_url("https://example.com/page?id=1") == "https://example.com/page?id=1"


@pytest.mark.asyncio
async def test_is_same_domain():
    """Test domain checking."""
    crawler = WebsiteCrawler(max_pages=10)
    
    base = "https://example.com/page"
    
    assert crawler._is_same_domain("https://example.com/other", base) is True
    assert crawler._is_same_domain("https://example.com/", base) is True
    assert crawler._is_same_domain("https://other.com/page", base) is False
    assert crawler._is_same_domain("https://subdomain.example.com/page", base) is False


@pytest.mark.asyncio
async def test_should_crawl():
    """Test crawl filtering."""
    crawler = WebsiteCrawler(max_pages=10, follow_external=False)
    
    base = "https://example.com/"
    
    # Should crawl same domain HTML
    assert crawler._should_crawl("https://example.com/page", base) is True
    
    # Skip images
    assert crawler._should_crawl("https://example.com/image.jpg", base) is False
    assert crawler._should_crawl("https://example.com/image.png", base) is False
    
    # Skip PDFs
    assert crawler._should_crawl("https://example.com/doc.pdf", base) is False
    
    # Skip CSS/JS
    assert crawler._should_crawl("https://example.com/style.css", base) is False
    assert crawler._should_crawl("https://example.com/script.js", base) is False
    
    # Skip external
    assert crawler._should_crawl("https://other.com/page", base) is False
    
    # Skip non-http
    assert crawler._should_crawl("mailto:test@example.com", base) is False
    assert crawler._should_crawl("tel:+1234567890", base) is False


@pytest.mark.asyncio
async def test_extract_links():
    """Test link extraction."""
    crawler = WebsiteCrawler(max_pages=10)
    
    html = """
    <html>
    <body>
        <a href="/page1">Page 1</a>
        <a href="/page2">Page 2</a>
        <a href="https://external.com/page">External</a>
        <a href="/image.jpg">Image</a>
        <a href="#section">Anchor</a>
    </body>
    </html>
    """
    
    base = "https://example.com/"
    links = crawler._extract_links(html, base)
    
    # Should resolve relative URLs and filter
    assert "https://example.com/page1" in links
    assert "https://example.com/page2" in links
    
    # Should skip image
    assert "https://example.com/image.jpg" not in links
    
    # Fragment-only should normalize to base (then filtered as duplicate)
    assert links.count("https://example.com/") <= 1
