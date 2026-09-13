"""Integration test with sample pages."""

from web_similarity_audit.extractor import ContentExtractor
from web_similarity_audit.models import PageInput
from web_similarity_audit.similarity import SimilarityCalculator
from tests.fixtures.sample_pages import SAMPLE_PAGE_1, SAMPLE_PAGE_2, SAMPLE_PAGE_3


def test_similar_pages_detected():
    """Test that similar pages (1 and 2) are detected as P1."""
    extractor = ContentExtractor()
    
    page1 = extractor.extract(SAMPLE_PAGE_1, PageInput(url="http://test.com/1"), 200)
    page2 = extractor.extract(SAMPLE_PAGE_2, PageInput(url="http://test.com/2"), 200)
    
    assert page1.extraction_confident
    assert page2.extraction_confident
    assert "crane" in page1.main_content.lower()
    
    calc = SimilarityCalculator()
    score = calc.compute_pairwise(page1, page2)
    
    # These pages are nearly identical, should be P1
    assert score.priority == "P1"
    assert score.tfidf_cosine >= 0.85 or score.jaccard_3gram >= 0.7


def test_different_pages_not_p1():
    """Test that different pages (1 and 3) are not P1."""
    extractor = ContentExtractor()
    
    page1 = extractor.extract(SAMPLE_PAGE_1, PageInput(url="http://test.com/1"), 200)
    page3 = extractor.extract(SAMPLE_PAGE_3, PageInput(url="http://test.com/3"), 200)
    
    assert page1.extraction_confident
    assert page3.extraction_confident
    
    calc = SimilarityCalculator()
    score = calc.compute_pairwise(page1, page3)
    
    # These are different products, should not be P1
    assert score.priority != "P1"
