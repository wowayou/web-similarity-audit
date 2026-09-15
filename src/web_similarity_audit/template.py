"""Template detection and removal."""

from collections import Counter
from typing import Optional

from .models import PageResult


class TemplateDetector:
    """Detect common blocks across pages for template removal."""
    
    def __init__(self, min_pages: int = 5, threshold: float = 0.6):
        """
        Args:
            min_pages: Minimum number of pages before template detection is enabled
            threshold: Fraction of pages a block must appear in to be considered template
        """
        self.min_pages = min_pages
        self.threshold = threshold
    
    def detect_common_blocks(
        self, pages: list[PageResult]
    ) -> Optional[set[str]]:
        """
        Detect blocks that appear in >= threshold fraction of pages.
        
        Returns None if n < min_pages (template detection disabled).
        """
        # Only enable for n >= min_pages
        if len(pages) < self.min_pages:
            return None
        
        # Count block occurrences
        block_counts: Counter[str] = Counter()
        for page in pages:
            # Use set to count each block once per page
            unique_blocks = set(page.blocks)
            for block in unique_blocks:
                block_counts[block] += 1
        
        # Identify common blocks
        n = len(pages)
        threshold_count = n * self.threshold
        common_blocks = {
            block for block, count in block_counts.items()
            if count >= threshold_count
        }
        
        return common_blocks
