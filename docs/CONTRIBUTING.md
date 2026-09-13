# Contributing to Web Similarity Audit

Thank you for considering contributing! This document outlines the process and guidelines.

## Code of Conduct

Be respectful, inclusive, and professional. Harassment and discriminatory behavior are not tolerated.

## Ways to Contribute

### 1. Report Bugs

Found a bug? Open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version)
- Relevant logs or error messages

**Template:**
```markdown
**Bug Description**
Brief description

**To Reproduce**
1. Run command: `web-similarity-audit --crawl https://example.com`
2. Observe error

**Expected Behavior**
Should complete without error

**Environment**
- OS: Ubuntu 22.04
- Python: 3.10.12
- Package version: 0.1.0

**Logs**
```
[paste error output]
```
```

### 2. Suggest Features

Have an idea? Open a discussion or issue with:
- Use case description
- Proposed solution
- Alternative approaches considered
- Impact on existing functionality

### 3. Improve Documentation

Documentation improvements are always welcome:
- Fix typos or unclear wording
- Add examples
- Improve explanations
- Translate to other languages

### 4. Submit Code

See development setup below.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Basic understanding of asyncio and web scraping

### Initial Setup

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/web-similarity-audit.git
cd web-similarity-audit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Development Dependencies

The `[dev]` extra includes:
- pytest: Testing framework
- pytest-asyncio: Async test support
- pytest-cov: Coverage reporting
- black: Code formatter
- ruff: Fast linter
- mypy: Type checking
- pre-commit: Git hook management

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch naming:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `ci/` - CI/CD changes

### 2. Make Changes

Follow the code style guide below.

### 3. Write Tests

```bash
# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_analyzer.py::test_jaccard_similarity -v

# Run with coverage
pytest tests/ --cov=src/web_similarity_audit --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Test requirements:**
- All new features must have tests
- Bug fixes should include regression tests
- Aim for >80% code coverage
- Tests should be fast (<5s for unit tests)

### 4. Check Code Quality

```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type check with mypy
mypy src/

# Run all checks (pre-commit)
pre-commit run --all-files
```

### 5. Update Documentation

- Update docstrings for public APIs
- Update README.md if adding user-facing features
- Update CHANGELOG.md under "Unreleased" section
- Add examples if appropriate

### 6. Commit Changes

```bash
git add .
git commit -m "feat: add block overlap similarity metric

- Implement block-level text comparison
- Add block_overlap field to SimilarityPair
- Update priority logic to include block overlap
- Add tests for block detection and comparison

Fixes #123"
```

**Commit message format:**
```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance (dependencies, build, etc.)
- `ci`: CI/CD changes

**Example:**
```
feat: add progress bar for crawling

- Show current/total pages discovered
- Display estimated time remaining
- Update every 0.5 seconds

Closes #45
```

### 7. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
# Fill in the PR template
```

## Code Style Guide

### Python Style

**Follow PEP 8 and project conventions:**

```python
# Good: Clear, documented, typed
async def fetch_page(
    url: str,
    timeout: int = 15,
    max_retries: int = 3
) -> PageData:
    """
    Fetch a single web page.
    
    Args:
        url: Full URL to fetch
        timeout: Request timeout in seconds
        max_retries: Number of retry attempts
    
    Returns:
        PageData object with HTML content and metadata
    
    Raises:
        FetchError: If fetch fails after all retries
        SSRFError: If URL resolves to private IP
    """
    # Implementation
    pass

# Bad: Unclear, undocumented, untyped
async def fetch(url, t=15, r=3):
    # No docstring
    pass
```

**Naming conventions:**
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

**Type hints:**
```python
# Always use type hints for public APIs
def compute_similarity(
    text_a: str,
    text_b: str
) -> float:
    pass

# Use Union, Optional, List, Dict from typing
from typing import List, Optional, Dict

def process_urls(
    urls: List[str],
    config: Optional[Dict[str, any]] = None
) -> List[PageData]:
    pass
```

**Docstrings:**
```python
def function_name(arg1: str, arg2: int) -> bool:
    """
    Short one-line summary.
    
    Longer description if needed. Explain the purpose,
    behavior, and any important details.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When arg1 is empty
        RuntimeError: When operation fails
    
    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

**Imports:**
```python
# Standard library first
import asyncio
import json
from typing import List, Optional

# Third-party packages
import httpx
from bs4 import BeautifulSoup

# Local modules
from web_similarity_audit.extractor import Extractor
from web_similarity_audit.utils import normalize_text
```

### Testing Style

```python
import pytest
from web_similarity_audit import Auditor

class TestAuditor:
    """Test suite for Auditor class."""
    
    def test_initialization_with_defaults(self):
        """Should initialize with default configuration."""
        auditor = Auditor()
        assert auditor.concurrency == 4
        assert auditor.per_host_rate == 2.0
    
    def test_initialization_with_custom_config(self):
        """Should accept custom configuration."""
        auditor = Auditor(concurrency=8, per_host_rate=1.0)
        assert auditor.concurrency == 8
        assert auditor.per_host_rate == 1.0
    
    @pytest.mark.asyncio
    async def test_audit_urls_with_empty_list(self):
        """Should raise ValueError for empty URL list."""
        auditor = Auditor()
        with pytest.raises(ValueError, match="at least 2 URLs"):
            await auditor.audit_urls([])
    
    def test_edge_case_with_special_characters(self):
        """Should handle URLs with special characters."""
        # Test implementation
        pass
```

**Test naming:**
- Test files: `test_<module>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<what>_<condition>_<expected>`

**Test organization:**
```
tests/
├── unit/              # Fast, isolated tests
│   ├── test_analyzer.py
│   ├── test_extractor.py
│   └── test_fetcher.py
├── integration/       # Tests with real HTTP, files
│   ├── test_cli.py
│   └── test_end_to_end.py
├── fixtures/          # Test data
│   ├── sample_pages.py
│   └── html/
│       ├── page1.html
│       └── page2.html
└── conftest.py        # Shared fixtures
```

## Architecture Guidelines

### Module Organization

```
src/web_similarity_audit/
├── __init__.py       # Public API exports
├── __main__.py       # CLI entry point
├── cli.py            # CLI logic (argparse, etc.)
├── core/             # Core business logic
│   ├── analyzer.py
│   ├── extractor.py
│   └── fetcher.py
├── models.py         # Data classes
├── utils.py          # Shared utilities
└── exceptions.py     # Custom exceptions
```

### Dependency Rules

1. **No circular dependencies**
2. **Core modules depend only on stdlib + documented deps**
3. **CLI depends on core, not vice versa**
4. **Test code never imported by production code**

### Error Handling

```python
# Define specific exceptions
class AuditError(Exception):
    """Base exception for audit errors."""
    pass

class FetchError(AuditError):
    """HTTP fetch failed."""
    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to fetch {url}: {reason}")

# Use specific exceptions
def fetch_page(url: str) -> PageData:
    try:
        response = httpx.get(url)
        response.raise_for_status()
    except httpx.TimeoutException:
        raise FetchError(url, "timeout")
    except httpx.HTTPStatusError as e:
        raise FetchError(url, f"HTTP {e.response.status_code}")
```

### Performance

- Use `asyncio` for I/O-bound operations
- Use generators for large datasets
- Profile before optimizing
- Document complexity: `O(n²)` for pairwise comparison

```python
# Good: Generator for large result sets
def iter_pairs(pages: List[PageData]):
    """Yield pairs without loading all in memory."""
    for i, page_a in enumerate(pages):
        for page_b in pages[i+1:]:
            yield (page_a, page_b)

# Bad: Load everything in memory
def get_all_pairs(pages: List[PageData]) -> List[Tuple[PageData, PageData]]:
    return [(a, b) for i, a in enumerate(pages) for b in pages[i+1:]]
```

## Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Code is formatted with black
- [ ] No linter warnings
- [ ] Type checks pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow convention

### PR Template

Your PR should include:

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed? What problem does it solve?

## Changes
- List of changes
- With bullet points

## Testing
How was this tested?
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Screenshots (if applicable)
Before/after screenshots or CLI output

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review performed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added
- [ ] All tests pass
- [ ] No new warnings

## Related Issues
Fixes #123
Related to #456
```

### Review Process

1. **Automated checks** run (CI/CD)
2. **Maintainer review** (1-2 business days)
3. **Address feedback** if needed
4. **Approval and merge**

### After Merge

- Your branch will be deleted
- Changes appear in next release
- You'll be credited in CHANGELOG.md

## Release Process

Maintainers only. See [RELEASE.md](../RELEASE.md) for details.

## Getting Help

### Stuck on Something?

1. Check existing documentation
2. Search closed issues
3. Ask in Discussions
4. Open an issue with your question

### Want to Discuss an Idea?

Use GitHub Discussions for:
- Feature ideas
- Architecture questions
- Design decisions
- General questions

## Recognition

Contributors are recognized in:
- CHANGELOG.md for each release
- GitHub contributors page
- Special thanks in documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Open an issue
- Start a discussion
- Email maintainers (see package metadata)

Thank you for contributing! 🎉
