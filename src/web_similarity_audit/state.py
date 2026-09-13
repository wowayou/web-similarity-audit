"""State management for crash recovery."""

import json
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

from .models import PageResult


@dataclass
class AuditState:
    """Represents the state of an audit run."""
    start_url: Optional[str]
    start_time: float
    total_pages: int
    fetched_urls: list[str]
    pages_data: list[dict]
    output_dir: str
    crawl_mode: bool
    max_pages: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "AuditState":
        """Create from dictionary."""
        return cls(**data)


class StateManager:
    """Manages audit state for crash recovery."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.state_file = output_dir / ".audit_state.json"
    
    def save_state(
        self,
        start_url: Optional[str],
        fetched_urls: list[str],
        pages: list[PageResult],
        crawl_mode: bool = False,
        max_pages: Optional[int] = None,
        start_time: Optional[float] = None,
    ):
        """Save current audit state."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        state = AuditState(
            start_url=start_url,
            start_time=start_time or time.time(),
            total_pages=len(fetched_urls),
            fetched_urls=fetched_urls,
            pages_data=[self._page_to_dict(p) for p in pages],
            output_dir=str(self.output_dir),
            crawl_mode=crawl_mode,
            max_pages=max_pages,
        )
        
        # Write atomically
        temp_file = self.state_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)
        
        temp_file.replace(self.state_file)
    
    def load_state(self) -> Optional[AuditState]:
        """Load saved state if exists."""
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return AuditState.from_dict(data)
        except Exception:
            return None
    
    def clear_state(self):
        """Remove state file after successful completion."""
        if self.state_file.exists():
            self.state_file.unlink()
    
    def has_state(self) -> bool:
        """Check if state file exists."""
        return self.state_file.exists()
    
    def _page_to_dict(self, page: PageResult) -> dict:
        """Convert PageResult to dictionary."""
        return {
            'url': page.url,
            'status_code': page.status_code,
            'error': page.error,
            'title': page.title,
            'main_content': page.main_content,
            'original_content': page.original_content,
            'char_count': page.char_count,
            'word_count': page.word_count,
            'extraction_method': page.extraction_method,
            'extraction_confident': page.extraction_confident,
            'content_hash': page.content_hash,
        }
    
    def pages_from_state(self, state: AuditState) -> list[PageResult]:
        """Convert state pages data back to PageResult objects."""
        pages = []
        for data in state.pages_data:
            page = PageResult(
                url=data['url'],
                status_code=data.get('status_code'),
                error=data.get('error'),
                title=data.get('title'),
                main_content=data.get('main_content', ''),
                original_content=data.get('original_content', ''),
                char_count=data.get('char_count', 0),
                word_count=data.get('word_count', 0),
                extraction_method=data.get('extraction_method', 'unknown'),
                extraction_confident=data.get('extraction_confident', False),
                content_hash=data.get('content_hash'),
            )
            pages.append(page)
        return pages
    
    def get_resume_info(self) -> Optional[dict]:
        """Get information about resumable state."""
        state = self.load_state()
        if not state:
            return None
        
        elapsed = time.time() - state.start_time
        return {
            'start_url': state.start_url,
            'elapsed_time': elapsed,
            'fetched_pages': state.total_pages,
            'crawl_mode': state.crawl_mode,
            'max_pages': state.max_pages,
            'output_dir': state.output_dir,
        }
