"""State management for crash recovery."""

import json
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

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
    # Every URL the run intends to audit, so a resumed run can fetch the
    # pages the interrupted one never reached.
    planned_urls: list[str] = field(default_factory=list)
    # Extraction directives for pending CSV inputs. Older state files omit it.
    planned_inputs: list[dict] = field(default_factory=list)
    
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
        planned_urls: Optional[list[str]] = None,
        planned_inputs: Optional[list[dict]] = None,
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
            planned_urls=planned_urls if planned_urls is not None else list(fetched_urls),
            planned_inputs=planned_inputs or [],
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
            'extraction_method': page.extraction_method,
            'extraction_confident': page.extraction_confident,
            'main_content': page.main_content,
            'main_content_length': page.main_content_length,
            'sha256': page.sha256,
            'block_count': page.block_count,
            'blocks': list(page.blocks),
            'word_count': page.word_count,
            'has_cjk': page.has_cjk,
        }

    def pages_from_state(self, state: AuditState) -> list[PageResult]:
        """Convert state pages data back to PageResult objects."""
        pages = []
        for data in state.pages_data:
            page = PageResult(
                url=data['url'],
                status_code=data.get('status_code'),
                error=data.get('error'),
                extraction_method=data.get('extraction_method'),
                extraction_confident=data.get('extraction_confident', False),
                main_content=data.get('main_content', ''),
                main_content_length=data.get('main_content_length', 0),
                sha256=data.get('sha256', ''),
                block_count=data.get('block_count', 0),
                blocks=data.get('blocks', []),
                word_count=data.get('word_count', 0),
                has_cjk=data.get('has_cjk', False),
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
