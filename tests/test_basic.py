"""Basic tests for similarity calculation."""

from web_similarity_audit.models import PageResult
from web_similarity_audit.similarity import SimilarityCalculator


def test_sha256_match():
    """Test SHA-256 exact match detection."""
    calc = SimilarityCalculator()
    
    page1 = PageResult(url="http://a.com")
    page1.sha256 = "abc123"
    page1.main_content = "test"
    page1.blocks = ["test"]
    
    page2 = PageResult(url="http://b.com")
    page2.sha256 = "abc123"
    page2.main_content = "test"
    page2.blocks = ["test"]
    
    score = calc.compute_pairwise(page1, page2)
    
    assert score.sha256_match is True
    assert score.priority == "P1"
    assert "SHA-256 exact match" in score.trigger_reasons


def test_high_tfidf_triggers_p1():
    """Test TF-IDF >= 0.85 triggers P1."""
    calc = SimilarityCalculator()
    
    page1 = PageResult(url="http://a.com")
    page1.sha256 = "abc"
    page1.main_content = "the quick brown fox jumps over the lazy dog"
    page1.blocks = ["the quick brown fox", "jumps over the lazy dog"]
    
    page2 = PageResult(url="http://b.com")
    page2.sha256 = "def"
    page2.main_content = "the quick brown fox jumps over the lazy dog"
    page2.blocks = ["the quick brown fox", "jumps over the lazy dog"]
    
    score = calc.compute_pairwise(page1, page2)
    
    # Should be very high similarity
    assert score.tfidf_cosine >= 0.85
    assert score.priority == "P1"


def test_block_overlap():
    """Test block overlap calculation."""
    calc = SimilarityCalculator()
    
    page1 = PageResult(url="http://a.com")
    page1.sha256 = "abc"
    page1.main_content = "block1 block2 block3"
    page1.blocks = ["block1", "block2", "block3"]
    
    page2 = PageResult(url="http://b.com")
    page2.sha256 = "def"
    page2.main_content = "block1 block2 block4"
    page2.blocks = ["block1", "block2", "block4"]
    
    score = calc.compute_pairwise(page1, page2)
    
    # 2/3 blocks in common
    assert score.block_overlap == 2/3
