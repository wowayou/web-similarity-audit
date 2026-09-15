"""Data models for page extraction and similarity results."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PageInput:
    """Input specification for a single page."""
    url: str
    selector: Optional[str] = None
    start_marker: Optional[str] = None
    end_marker: Optional[str] = None


@dataclass
class PageResult:
    """Extraction result for a single page."""
    url: str
    status_code: Optional[int] = None
    error: Optional[str] = None
    
    # Content extraction
    extraction_method: Optional[str] = None  # 'selector', 'markers', 'trafilatura', 'body_fallback'
    extraction_confident: bool = False
    main_content: str = ""
    main_content_length: int = 0
    
    # Fingerprints
    sha256: str = ""
    block_count: int = 0
    blocks: list[str] = field(default_factory=list)
    
    # Text analysis
    word_count: int = 0
    has_cjk: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "url": self.url,
            "status_code": self.status_code,
            "error": self.error,
            "extraction_method": self.extraction_method,
            "extraction_confident": self.extraction_confident,
            "main_content_length": self.main_content_length,
            "sha256": self.sha256,
            "block_count": self.block_count,
            "word_count": self.word_count,
            "has_cjk": self.has_cjk,
        }


@dataclass
class SimilarityScore:
    """Similarity scores between two pages."""
    url1: str
    url2: str
    
    # Raw similarity signals
    sha256_match: bool = False
    jaccard_3gram: float = 0.0
    tfidf_cosine: float = 0.0
    block_overlap: float = 0.0
    
    # Template-removed view (only if n>=5)
    jaccard_3gram_clean: Optional[float] = None
    tfidf_cosine_clean: Optional[float] = None
    block_overlap_clean: Optional[float] = None
    
    # Classification
    priority: Optional[str] = None  # 'P1', 'P2', 'P3', None
    trigger_reasons: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for CSV/JSON output."""
        return {
            "url1": self.url1,
            "url2": self.url2,
            "sha256_match": self.sha256_match,
            "jaccard_3gram": round(self.jaccard_3gram, 4),
            "tfidf_cosine": round(self.tfidf_cosine, 4),
            "block_overlap": round(self.block_overlap, 4),
            "jaccard_3gram_clean": (
                round(self.jaccard_3gram_clean, 4)
                if self.jaccard_3gram_clean is not None else None
            ),
            "tfidf_cosine_clean": (
                round(self.tfidf_cosine_clean, 4)
                if self.tfidf_cosine_clean is not None else None
            ),
            "block_overlap_clean": (
                round(self.block_overlap_clean, 4)
                if self.block_overlap_clean is not None else None
            ),
            "priority": self.priority,
            "trigger_reasons": "; ".join(self.trigger_reasons) if self.trigger_reasons else "",
        }
