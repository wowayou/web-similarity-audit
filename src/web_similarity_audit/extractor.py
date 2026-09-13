"""Main content extraction using trafilatura and fallback methods."""

import hashlib
import re
import unicodedata
from typing import Optional

import trafilatura
from bs4 import BeautifulSoup

from .models import PageInput, PageResult


class ContentExtractor:
    """Extract main content from HTML with explicit confidence reporting."""
    
    def __init__(self, include_comments: bool = False):
        self.include_comments = include_comments
    
    def extract(self, html: str, page_input: PageInput, status_code: int) -> PageResult:
        """
        Extract main content from HTML following priority order:
        1. CSS selector (if provided)
        2. Start/end markers (if provided)
        3. Trafilatura extraction
        4. Body fallback (marked as uncertain)
        """
        result = PageResult(url=page_input.url, status_code=status_code)
        soup = BeautifulSoup(html, "lxml")
        
        # Priority 1: CSS selector
        if page_input.selector:
            element = soup.select_one(page_input.selector)
            if element:
                result.main_content = self._clean_text(element.get_text())
                result.extraction_method = "selector"
                result.extraction_confident = True
                self._compute_fingerprints(result)
                return result
            else:
                result.error = f"Selector '{page_input.selector}' not found"
                result.extraction_method = "selector_failed"
                result.extraction_confident = False
                return result
        
        # Priority 2: Start/end markers
        if page_input.start_marker and page_input.end_marker:
            content = self._extract_by_markers(
                html, page_input.start_marker, page_input.end_marker
            )
            if content:
                result.main_content = self._clean_text(content)
                result.extraction_method = "markers"
                result.extraction_confident = True
                self._compute_fingerprints(result)
                return result
            else:
                result.error = f"Markers not found in HTML"
                result.extraction_method = "markers_failed"
                result.extraction_confident = False
                return result
        
        # Priority 3: Trafilatura
        extracted = trafilatura.extract(
            html,
            include_comments=self.include_comments,
            include_tables=True,
            no_fallback=False,
            favor_precision=True,
        )
        
        if extracted and len(extracted.strip()) > 100:
            result.main_content = self._clean_text(extracted)
            result.extraction_method = "trafilatura"
            result.extraction_confident = True
            self._compute_fingerprints(result)
            return result
        
        # Priority 4: Body fallback (uncertain)
        body = soup.find("body")
        if body:
            # Remove script, style, nav, footer, header elements
            for tag in body.find_all(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            
            result.main_content = self._clean_text(body.get_text())
            result.extraction_method = "body_fallback"
            result.extraction_confident = False
            result.error = "Main content extraction uncertain: using body fallback"
            self._compute_fingerprints(result)
            return result
        
        # Total failure
        result.error = "No extractable content found"
        result.extraction_method = "failed"
        result.extraction_confident = False
        return result
    
    def _extract_by_markers(
        self, html: str, start_marker: str, end_marker: str
    ) -> Optional[str]:
        """Extract content between start and end markers."""
        start_idx = html.find(start_marker)
        if start_idx == -1:
            return None
        
        start_idx += len(start_marker)
        end_idx = html.find(end_marker, start_idx)
        if end_idx == -1:
            return None
        
        return html[start_idx:end_idx]
    
    def _clean_text(self, text: str) -> str:
        """Normalize and clean extracted text."""
        # NFKC normalization (handles CJK, full-width chars)
        text = unicodedata.normalize("NFKC", text)
        
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        
        # Strip
        text = text.strip()
        
        return text
    
    def _compute_fingerprints(self, result: PageResult):
        """Compute SHA-256, blocks, and text statistics."""
        content = result.main_content
        
        # SHA-256
        result.sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        result.main_content_length = len(content)
        
        # Split into blocks (paragraphs separated by multiple spaces or newlines)
        blocks = [b.strip() for b in re.split(r"\s{2,}", content) if b.strip()]
        result.blocks = [self._normalize_block(b) for b in blocks]
        result.block_count = len(result.blocks)
        
        # Word count
        result.word_count = len(content.split())
        
        # CJK detection
        result.has_cjk = bool(re.search(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]", content))
    
    def _normalize_block(self, block: str) -> str:
        """Normalize a block for template detection."""
        # Lowercase, collapse whitespace
        block = block.lower()
        block = re.sub(r"\s+", " ", block)
        return block.strip()
