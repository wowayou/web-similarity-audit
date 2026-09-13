"""Similarity computation with multiple signals."""

import math
import re
from collections import Counter
from typing import Optional

from .models import PageResult, SimilarityScore


class SimilarityCalculator:
    """Compute similarity scores between pages using multiple signals."""
    
    def compute_pairwise(
        self,
        page1: PageResult,
        page2: PageResult,
        common_blocks: Optional[set[str]] = None,
    ) -> SimilarityScore:
        """
        Compute similarity between two pages.
        
        Args:
            page1: First page result
            page2: Second page result
            common_blocks: Set of common blocks to remove for template-free view
        """
        score = SimilarityScore(url1=page1.url, url2=page2.url)
        
        # Signal 1: SHA-256 exact match
        score.sha256_match = page1.sha256 == page2.sha256
        
        # Signal 2: n-gram Jaccard (trigrams)
        score.jaccard_3gram = self._jaccard_ngrams(
            page1.main_content, page2.main_content, n=3
        )
        
        # Signal 3: TF-IDF cosine similarity
        score.tfidf_cosine = self._tfidf_cosine(
            page1.main_content, page2.main_content
        )
        
        # Signal 4: Block overlap
        score.block_overlap = self._block_overlap(page1.blocks, page2.blocks)
        
        # Template-removed view (only if common_blocks provided and non-empty)
        if common_blocks:
            clean_blocks1 = [b for b in page1.blocks if b not in common_blocks]
            clean_blocks2 = [b for b in page2.blocks if b not in common_blocks]
            
            if clean_blocks1 and clean_blocks2:
                clean_content1 = " ".join(clean_blocks1)
                clean_content2 = " ".join(clean_blocks2)
                
                score.jaccard_3gram_clean = self._jaccard_ngrams(
                    clean_content1, clean_content2, n=3
                )
                score.tfidf_cosine_clean = self._tfidf_cosine(
                    clean_content1, clean_content2
                )
                score.block_overlap_clean = self._block_overlap(
                    clean_blocks1, clean_blocks2
                )
        
        # Classify priority
        self._classify(score)
        
        return score
    
    def _jaccard_ngrams(self, text1: str, text2: str, n: int = 3) -> float:
        """Compute Jaccard similarity of character n-grams."""
        if not text1 or not text2:
            return 0.0
        
        ngrams1 = self._get_ngrams(text1, n)
        ngrams2 = self._get_ngrams(text2, n)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        
        return intersection / union if union > 0 else 0.0
    
    def _get_ngrams(self, text: str, n: int) -> set[str]:
        """Extract character n-grams from text."""
        # Remove whitespace for n-gram extraction
        text = re.sub(r"\s+", "", text)
        return {text[i:i+n] for i in range(len(text) - n + 1)}
    
    def _tfidf_cosine(self, text1: str, text2: str) -> float:
        """Compute TF-IDF cosine similarity."""
        if not text1 or not text2:
            return 0.0
        
        # Tokenize (split on whitespace and punctuation)
        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Term frequency
        tf1 = Counter(tokens1)
        tf2 = Counter(tokens2)
        
        # Document frequency (binary: in doc1, doc2, or both)
        all_terms = set(tf1.keys()) | set(tf2.keys())
        df = {}
        for term in all_terms:
            df[term] = (1 if term in tf1 else 0) + (1 if term in tf2 else 0)
        
        # TF-IDF vectors (add smoothing to IDF to avoid log(1) = 0)
        vec1 = {}
        vec2 = {}
        for term in all_terms:
            # Use log(1 + N/df) to avoid zero for terms in both docs
            idf = math.log(1 + 2 / df[term])
            if term in tf1:
                vec1[term] = tf1[term] * idf
            if term in tf2:
                vec2[term] = tf2[term] * idf
        
        # Cosine similarity
        dot_product = sum(vec1.get(t, 0) * vec2.get(t, 0) for t in all_terms)
        norm1 = math.sqrt(sum(v * v for v in vec1.values()))
        norm2 = math.sqrt(sum(v * v for v in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words."""
        # Split on whitespace and punctuation, keep alphanumeric + CJK
        tokens = re.findall(r"[\w\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]+", text.lower())
        return tokens
    
    def _block_overlap(self, blocks1: list[str], blocks2: list[str]) -> float:
        """Compute block-level overlap ratio."""
        if not blocks1 or not blocks2:
            return 0.0
        
        set1 = set(blocks1)
        set2 = set(blocks2)
        
        intersection = len(set1 & set2)
        smaller = min(len(set1), len(set2))
        
        return intersection / smaller if smaller > 0 else 0.0
    
    def _classify(self, score: SimilarityScore):
        """
        Classify similarity into P1/P2/P3 and record trigger reasons.
        
        P1 criteria (any one triggers):
        - SHA-256 match
        - TF-IDF >= 0.85
        - Jaccard >= 0.7
        - Block overlap >= 0.8
        
        P2 criteria:
        - TF-IDF >= 0.6 OR Jaccard >= 0.4 OR Block overlap >= 0.5
        
        P3:
        - TF-IDF >= 0.3 OR Jaccard >= 0.2 OR Block overlap >= 0.3
        """
        reasons = []
        
        # P1 checks
        if score.sha256_match:
            score.priority = "P1"
            reasons.append("SHA-256 exact match")
        
        if score.tfidf_cosine >= 0.85:
            score.priority = "P1"
            reasons.append(f"TF-IDF {score.tfidf_cosine:.2f} >= 0.85")
        
        if score.jaccard_3gram >= 0.7:
            score.priority = "P1"
            reasons.append(f"Jaccard {score.jaccard_3gram:.2f} >= 0.7")
        
        if score.block_overlap >= 0.8:
            score.priority = "P1"
            reasons.append(f"Block overlap {score.block_overlap:.2f} >= 0.8")
        
        # P2 checks (if not P1)
        if not score.priority:
            if score.tfidf_cosine >= 0.6:
                score.priority = "P2"
                reasons.append(f"TF-IDF {score.tfidf_cosine:.2f} >= 0.6")
            
            if score.jaccard_3gram >= 0.4:
                score.priority = "P2"
                reasons.append(f"Jaccard {score.jaccard_3gram:.2f} >= 0.4")
            
            if score.block_overlap >= 0.5:
                score.priority = "P2"
                reasons.append(f"Block overlap {score.block_overlap:.2f} >= 0.5")
        
        # P3 checks (if not P1 or P2)
        if not score.priority:
            if score.tfidf_cosine >= 0.3:
                score.priority = "P3"
                reasons.append(f"TF-IDF {score.tfidf_cosine:.2f} >= 0.3")
            
            if score.jaccard_3gram >= 0.2:
                score.priority = "P3"
                reasons.append(f"Jaccard {score.jaccard_3gram:.2f} >= 0.2")
            
            if score.block_overlap >= 0.3:
                score.priority = "P3"
                reasons.append(f"Block overlap {score.block_overlap:.2f} >= 0.3")
        
        score.trigger_reasons = reasons
