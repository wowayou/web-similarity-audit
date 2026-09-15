"""Main content extraction using trafilatura and fallback methods."""

import hashlib
import re
import unicodedata
from typing import Optional

import trafilatura
from bs4 import NavigableString, BeautifulSoup

from .models import PageInput, PageResult

# Block-level elements that end a paragraph/block. A newline is inserted
# after each of them before get_text() so block boundaries survive even in
# minified HTML that has no whitespace between tags.
_BLOCK_LEVEL_TAGS = [
    "address", "article", "blockquote", "br", "dd", "details", "div", "dl",
    "dt", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2",
    "h3", "h4", "h5", "h6", "header", "hgroup", "hr", "li", "main", "nav",
    "ol", "p", "pre", "section", "table", "tbody", "td", "tfoot", "th",
    "thead", "tr", "ul",
]


class ContentExtractor:
    """Extract main content from HTML with explicit confidence reporting."""
    
    def __init__(self, include_comments: bool = False):
        self.include_comments = include_comments
    
    def extract(self, html: str, page_input: PageInput, status_code: int) -> PageResult:
        """
        Extract main content from HTML following a strict priority order.

        Precedence (highest first):
            1. CSS ``selector``  (if provided)
            2. ``start_marker`` / ``end_marker``  (if both provided)
            3. Trafilatura automatic extraction
            4. ``<body>`` fallback (marked uncertain)

        Rules:
            * If ``selector`` is provided and matches, it wins even when markers
              are also provided.
            * If ``selector`` is provided but does **not** match, extraction
              fails explicitly (``selector_failed``) and does **not** silently
              fall through to markers or trafilatura. This preserves the
              project's "explicit failure" contract so callers can tell that
              their configured selector is broken.
            * If only ``start_marker``/``end_marker`` are provided and either is
              missing from the HTML, extraction fails explicitly
              (``markers_failed``).
            * Only when the caller provides no explicit selector/markers does
              the tool fall back to trafilatura and finally to the uncertain
              ``<body>`` extraction.

        Text is normalized with NFKC, so full-width forms such as
        ``ＣＷＢ－１５９`` become ``CWB-159`` before hashing. This makes
        full-width and half-width renderings of the same model number compare
        as equal, which is desirable for duplicate detection.
        """
        result = PageResult(url=page_input.url, status_code=status_code)
        soup = BeautifulSoup(html, "lxml")
        
        # Priority 1: CSS selector
        if page_input.selector:
            element = soup.select_one(page_input.selector)
            if element:
                raw_text = self._text_with_block_breaks(element)
                result.main_content = self._clean_text(raw_text)
                result.extraction_method = "selector"
                result.extraction_confident = True
                self._compute_fingerprints(result, raw_text)
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
                self._compute_fingerprints(result, content)
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
            self._compute_fingerprints(result, extracted)
            return result

        # Priority 4: Body fallback (uncertain)
        body = soup.find("body")
        if body:
            # Remove script, style, nav, footer, header elements
            for tag in body.find_all(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            raw_text = self._text_with_block_breaks(body)
            result.main_content = self._clean_text(raw_text)
            result.extraction_method = "body_fallback"
            result.extraction_confident = False
            result.error = "Main content extraction uncertain: using body fallback"
            self._compute_fingerprints(result, raw_text)
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
    
    def _text_with_block_breaks(self, element) -> str:
        """Element text with a newline after each block-level descendant.

        Plain ``get_text()`` joins sibling block elements with whatever
        whitespace the source has — in minified HTML that is nothing, so all
        paragraphs glue into one string and block splitting degrades. The
        inserted newlines give :meth:`_compute_fingerprints` real block
        boundaries regardless of the source formatting.
        """
        for tag in element.find_all(_BLOCK_LEVEL_TAGS):
            tag.insert_after(NavigableString("\n"))
        return element.get_text()

    def _clean_text(self, text: str) -> str:
        """Normalize and clean extracted text."""
        # NFKC normalization (handles CJK, full-width chars)
        text = unicodedata.normalize("NFKC", text)
        
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        
        # Strip
        text = text.strip()
        
        return text
    
    def _compute_fingerprints(self, result: PageResult, raw_text: str):
        """Compute SHA-256, blocks, and text statistics.

        *raw_text* is the extracted text *before* whitespace collapsing:
        block boundaries (paragraph breaks) only exist while newlines and
        runs of whitespace are still intact, so splitting must happen here,
        not on the already-collapsed ``main_content``.
        """
        # SHA-256 over the collapsed, NFKC-normalized main content
        result.sha256 = hashlib.sha256(result.main_content.encode("utf-8")).hexdigest()
        result.main_content_length = len(result.main_content)

        # Split into blocks on the raw text: paragraph breaks are newlines
        # (trafilatura / get_text separate paragraphs with "\\n") or runs of
        # 2+ whitespace characters.
        text = unicodedata.normalize("NFKC", raw_text)
        blocks = [b.strip() for b in re.split(r"\n+|\s{2,}", text) if b.strip()]
        result.blocks = [self._normalize_block(b) for b in blocks]
        result.block_count = len(result.blocks)

        # Word count
        result.word_count = len(result.main_content.split())

        # CJK detection
        result.has_cjk = bool(re.search(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]", result.main_content))
    
    def _normalize_block(self, block: str) -> str:
        """Normalize a block for template detection."""
        # Lowercase, collapse whitespace
        block = block.lower()
        block = re.sub(r"\s+", " ", block)
        return block.strip()
