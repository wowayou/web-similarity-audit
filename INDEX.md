# Web Page Similarity Auditor - Documentation Index

## 🚀 Getting Started

**New users start here:**
- [QUICKSTART.md](QUICKSTART.md) - Installation and basic usage (5 min read)
- [README.md](README.md) - Complete user guide with examples (15 min read)

## 📚 Documentation

### User Documentation
- **[README.md](README.md)** - Features, usage examples, use cases
  - Installation instructions (pip, pipx)
  - Command-line options
  - Output format specifications
  - Architecture overview
  - Use cases (SEO audit, content migration, consultant deliverables)

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
  - Installation steps
  - Basic usage examples
  - Understanding results (P1/P2/P3)
  - Common issues and solutions

### Technical Documentation
- **[IMPLEMENTATION.md](IMPLEMENTATION.md)** - Technical deep-dive
  - Implementation rationale (why "thin wrapper")
  - Comparison with existing tools
  - Key decisions and tradeoffs
  - Review recommendations implemented
  - Deviations from original PRD

- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Project overview
  - Complete feature checklist
  - Code metrics and statistics
  - Architecture diagram
  - Performance profile
  - Lessons learned

### Project Status
- **[PROJECT_COMPLETE.md](PROJECT_COMPLETE.md)** - Final status report
  - M0 milestone completion
  - All features delivered
  - Next steps (M1/M2)

- **[DELIVERY_CHECKLIST.md](DELIVERY_CHECKLIST.md)** - Detailed checklist
  - Core implementation (100%)
  - Features (14/14)
  - Documentation (6 files)
  - Review recommendations (7/7)
  - Quality standards verified

## 🔧 Code Reference

### Main Package (`src/web_similarity_audit/`)
```
cli.py          - CLI interface and orchestration (262 lines)
fetcher.py      - HTTP client with SSRF protection (164 lines)
extractor.py    - Content extraction cascade (151 lines)
similarity.py   - Multi-signal similarity computation (217 lines)
reporter.py     - JSON/CSV/Markdown output (162 lines)
template.py     - Template block detection (49 lines)
models.py       - Data models (89 lines)
```

### Test Suite (`tests/`)
```
test_basic.py       - Core algorithms (SHA-256, TF-IDF, block overlap)
test_edge_cases.py  - Error handling and edge cases
test_integration.py - End-to-end extraction tests
```

## 🎯 Quick Reference

### Installation
```bash
cd web-similarity-audit
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Run Tests
```bash
pytest tests/ -v
```

### Basic Usage
```bash
# Compare 2 URLs
web-similarity-audit https://example.com https://example.org

# Compare from CSV
web-similarity-audit urls.csv --output-dir results
```

### Demo
```bash
./demo.sh
```

## 📊 Key Metrics

| Metric | Value |
|--------|-------|
| Total LOC | 1,360 |
| Modules | 9 |
| Tests | 12 (100% passing) |
| Dependencies | 4 |
| Documentation | 6 files |
| Python | >=3.10 |

## ✨ Key Features

- **Explicit failure reporting** - No silent fallbacks
- **Multi-signal similarity** - SHA-256, Jaccard, TF-IDF, block overlap
- **SSRF protection** - DNS + IP validation
- **Template detection** - Smart n≥5 threshold
- **CJK support** - Chinese, Japanese, Korean text
- **Multiple outputs** - JSON, CSV, Markdown

## 🎓 Understanding the Tool

### When to Use
- SEO audits (duplicate content detection)
- Content migration verification
- Consultant deliverables with evidence
- CI/CD content quality checks

### Priority Levels
- **P1**: High similarity (≥0.85 TF-IDF OR ≥0.7 Jaccard OR exact match)
- **P2**: Moderate similarity (≥0.6 TF-IDF OR ≥0.4 Jaccard)
- **P3**: Low similarity (≥0.3 TF-IDF OR ≥0.2 Jaccard)

### Extraction Methods
1. CSS selector (if provided in CSV)
2. Start/end markers (if provided in CSV)
3. Trafilatura ML extraction
4. Body fallback (marked as uncertain)

## 🔍 Output Files

Every run generates 3 files in the output directory:

1. **pages.json** - Extraction metadata
   - Status codes, extraction methods, confidence flags
   - SHA-256 hashes, block counts, word counts
   - CJK detection, error messages

2. **pairs.csv** - Similarity scores
   - All pairwise comparisons
   - 4 signals × 2 views (original + template-removed)
   - Trigger reasons explaining classifications

3. **report.md** - Human-readable summary
   - P1/P2/P3 counts
   - Template detection status
   - Top similarity pairs
   - Extraction warnings

## 🚦 Next Steps

### For Users
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run the demo: `./demo.sh`
3. Try with your URLs
4. Check output files

### For Developers
1. Read [IMPLEMENTATION.md](IMPLEMENTATION.md)
2. Review code in `src/web_similarity_audit/`
3. Run tests: `pytest tests/ -v`
4. Check [DELIVERY_CHECKLIST.md](DELIVERY_CHECKLIST.md)

### For Stakeholders
1. Review [PROJECT_COMPLETE.md](PROJECT_COMPLETE.md)
2. Check deliverables in [DELIVERY_CHECKLIST.md](DELIVERY_CHECKLIST.md)
3. See metrics in [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

## 📞 Common Questions

### Q: How many pages can it handle?
A: 2-200 pages. Designed for O(n²) comparison with performance target <5 min for 200 pages.

### Q: Does it work with JavaScript-rendered content?
A: No, it fetches HTML only. Use a headless browser to pre-render SPA sites.

### Q: How accurate is the similarity detection?
A: Uses 4 complementary signals. TF-IDF catches semantic similarity, Jaccard catches typos, block overlap catches copied paragraphs, SHA-256 catches exact duplicates.

### Q: Can I use it in CI/CD?
A: Yes! Exit codes (0/1/2/3/4) make it CI-friendly. JSON output is machine-parseable.

### Q: What about privacy/security?
A: SSRF protection blocks private IPs. No data leaves your machine. No telemetry.

## 🎉 Status

**Version**: 0.1.0 (M0)  
**Status**: ✅ Production Ready  
**Location**: `/home/forbackup/Dev/my-projects/web-similarity-audit/`

All M0 deliverables complete. Ready for field testing and deployment.

---

For questions or issues, refer to the documentation above or check the inline code comments.
