"""Report generation in JSON, CSV, and Markdown formats."""

import csv
import json
from pathlib import Path
from typing import Optional

from .models import PageResult, SimilarityScore

_FAILED_METHODS = {"fetch_failed", "failed", "selector_failed", "markers_failed"}


def _is_failed(page: PageResult) -> bool:
    return page.extraction_method in _FAILED_METHODS


def _is_uncertain(page: PageResult) -> bool:
    return not page.extraction_confident and not _is_failed(page)


def _escape_markdown(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


class Reporter:
    """Generate audit reports in multiple formats."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def write_pages_json(self, pages: list[PageResult]):
        """Write pages.json with per-page extraction results."""
        output = {
            "pages": [p.to_dict() for p in pages],
            "summary": {
                "total": len(pages),
                "successful": sum(1 for p in pages if p.extraction_confident),
                "uncertain": sum(1 for p in pages if _is_uncertain(p)),
                "failed": sum(1 for p in pages if _is_failed(p)),
            }
        }
        
        path = self.output_dir / "pages.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    
    def write_pairs_csv(self, scores: list[SimilarityScore]):
        """Write pairs.csv with pairwise similarity scores."""
        path = self.output_dir / "pairs.csv"
        
        if not scores:
            # Write empty CSV with headers
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "url1", "url2", "priority", "sha256_match",
                    "jaccard_3gram", "tfidf_cosine", "block_overlap",
                    "jaccard_3gram_clean", "tfidf_cosine_clean", "block_overlap_clean",
                    "trigger_reasons"
                ])
            return
        
        with open(path, "w", encoding="utf-8", newline="") as f:
            dict_writer = csv.DictWriter(f, fieldnames=[
                "url1", "url2", "priority", "sha256_match",
                "jaccard_3gram", "tfidf_cosine", "block_overlap",
                "jaccard_3gram_clean", "tfidf_cosine_clean", "block_overlap_clean",
                "trigger_reasons"
            ])
            dict_writer.writeheader()
            for score in scores:
                dict_writer.writerow(score.to_dict())
    
    def write_markdown_report(
        self,
        pages: list[PageResult],
        scores: list[SimilarityScore],
        common_blocks: Optional[set[str]],
        elapsed_time: float,
        compute_time: float | None = None,
        fetch_time: float | None = None,
    ):
        """Write report.md with human-readable summary."""
        p1 = [s for s in scores if s.priority == "P1"]
        p2 = [s for s in scores if s.priority == "P2"]
        p3 = [s for s in scores if s.priority == "P3"]
        
        uncertain = [p for p in pages if _is_uncertain(p)]
        failed = [p for p in pages if _is_failed(p)]
        
        lines = [
            "# Web Page Similarity Audit Report",
            "",
            "## Summary",
            "",
            f"- **Total pages**: {len(pages)}",
            f"- **Successful extractions**: {sum(1 for p in pages if p.extraction_confident)}",
            f"- **Uncertain extractions**: {len(uncertain)}",
            f"- **Failed extractions**: {len(failed)}",
            f"- **Total pairs analyzed**: {len(scores)}",
            f"- **Total time**: {elapsed_time:.2f}s",
            *(
                [f"- **Fetch + extract time**: {fetch_time:.2f}s"]
                if fetch_time is not None else []
            ),
            *(
                [f"- **Computation time**: {compute_time:.2f}s"]
                if compute_time is not None else []
            ),
            "",
            "## Similarity Findings",
            "",
            f"- **P1 (High similarity)**: {len(p1)} pairs",
            f"- **P2 (Moderate similarity)**: {len(p2)} pairs",
            f"- **P3 (Low similarity)**: {len(p3)} pairs",
            "",
        ]
        
        # Template detection note
        if common_blocks is None:
            lines.extend([
                "## Template Removal",
                "",
                f"Template detection disabled (n={len(pages)} < 5). All comparisons use original content.",
                "",
            ])
        elif len(common_blocks) == 0:
            lines.extend([
                "## Template Removal",
                "",
                f"No common blocks detected (threshold: 60% of {len(pages)} pages).",
                "",
            ])
        else:
            lines.extend([
                "## Template Removal",
                "",
                f"Detected {len(common_blocks)} common blocks appearing in ≥60% of pages.",
                "Template-removed similarity scores are included in pairs.csv.",
                "",
            ])
        
        # P1 details
        if p1:
            lines.extend([
                "## P1: High Similarity Pairs",
                "",
                "| URL 1 | URL 2 | Trigger Reasons |",
                "|-------|-------|-----------------|",
            ])
            for score in p1[:20]:  # Limit to first 20
                url1 = _escape_markdown(score.url1)
                url2 = _escape_markdown(score.url2)
                reasons = _escape_markdown("; ".join(score.trigger_reasons))
                lines.append(f"| {url1} | {url2} | {reasons} |")
            if len(p1) > 20:
                lines.append(f"| ... | ... | ({len(p1) - 20} more pairs) |")
            lines.append("")
        
        # Uncertain extractions
        if uncertain:
            lines.extend([
                "## Uncertain Extractions",
                "",
                "The following pages used body fallback (extraction confidence low):",
                "",
            ])
            for page in uncertain:
                lines.append(f"- {_escape_markdown(page.url)}")
            lines.append("")
        
        # Failed extractions
        if failed:
            lines.extend([
                "## Failed Extractions",
                "",
                "The following pages failed main content extraction:",
                "",
            ])
            for page in failed:
                url = _escape_markdown(page.url)
                error = _escape_markdown(page.error)
                lines.append(f"- {url}: {error}")
            lines.append("")
        
        # Write
        path = self.output_dir / "report.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
