"""
Example: Crawl a website and audit for duplicate pages.

This example shows how to use the crawl mode to automatically discover
and audit all pages on a website, similar to Screaming Frog's approach.
"""

import asyncio

from web_similarity_audit.crawler import WebsiteCrawler
from web_similarity_audit.extractor import ContentExtractor
from web_similarity_audit.fetcher import PageFetcher
from web_similarity_audit.models import PageInput, PageResult
from web_similarity_audit.similarity import SimilarityCalculator
from web_similarity_audit.template import TemplateDetector


async def crawl_and_audit_example():
    """Example: Crawl a website and find duplicate pages."""
    
    # Step 1: Crawl the website
    print("Step 1: Crawling website...")
    crawler = WebsiteCrawler(
        max_pages=50,
        timeout=10.0,
        rate_limit=2.0,
        max_concurrent=4,
        follow_external=False,
    )
    
    start_url = "https://example.com"
    
    def progress(count, url):
        print(f"  Found: [{count}] {url}")
    
    urls = await crawler.crawl(start_url, progress_callback=progress)
    print(f"\nDiscovered {len(urls)} pages\n")
    
    # Step 2: Fetch all pages
    print("Step 2: Fetching pages...")
    fetcher = PageFetcher(
        max_response_size=2 * 1024 * 1024,
        timeout=10.0,
        rate_limit_per_host=2.0,
        max_concurrent=4,
    )
    fetch_results = await fetcher.fetch_all(urls)
    
    # Step 3: Extract main content
    print("Step 3: Extracting main content...")
    extractor = ContentExtractor()
    pages: list[PageResult] = []
    
    page_inputs = [PageInput(url=url) for url in urls]
    for page_input, (url, html, status_code, error) in zip(page_inputs, fetch_results):
        if html:
            result = extractor.extract(html, page_input, status_code)
        else:
            result = PageResult(
                url=url,
                status_code=status_code,
                error=error,
                extraction_method="fetch_failed",
                extraction_confident=False,
            )
        pages.append(result)
    
    successful = sum(1 for p in pages if p.raw_content)
    print(f"  Successfully extracted: {successful}/{len(pages)}\n")
    
    # Step 4: Detect common template blocks
    print("Step 4: Detecting template blocks...")
    template_detector = TemplateDetector(min_pages=5, threshold=0.6)
    common_blocks = template_detector.detect_common_blocks(pages)
    
    if common_blocks:
        print(f"  Found {len(common_blocks)} common blocks\n")
    else:
        print("  No common blocks detected\n")
    
    # Step 5: Compute similarity
    print("Step 5: Computing pairwise similarity...")
    calculator = SimilarityCalculator()
    
    p1_pairs = []
    p2_pairs = []
    
    for i in range(len(pages)):
        for j in range(i + 1, len(pages)):
            score = calculator.compute_pairwise(pages[i], pages[j], common_blocks)
            
            if score.priority == "P1":
                p1_pairs.append((pages[i].url, pages[j].url, score))
            elif score.priority == "P2":
                p2_pairs.append((pages[i].url, pages[j].url, score))
    
    # Step 6: Display results
    print("\n" + "=" * 80)
    print(f"AUDIT RESULTS")
    print("=" * 80)
    print(f"\nTotal pages: {len(pages)}")
    print(f"P1 (high similarity): {len(p1_pairs)}")
    print(f"P2 (moderate similarity): {len(p2_pairs)}")
    
    if p1_pairs:
        print("\n--- P1 High Similarity Pairs ---")
        for url1, url2, score in p1_pairs[:5]:  # Show first 5
            print(f"\n{url1}")
            print(f"  <-> {url2}")
            print(f"  Reason: {score.trigger_reason}")
            print(f"  TF-IDF: {score.tfidf_cosine_raw:.3f}")
            print(f"  Jaccard: {score.jaccard_bigram_raw:.3f}")
    
    if len(p1_pairs) > 5:
        print(f"\n... and {len(p1_pairs) - 5} more P1 pairs")


if __name__ == "__main__":
    asyncio.run(crawl_and_audit_example())
