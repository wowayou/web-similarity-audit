# Contributing to Web Similarity Audit

Thank you for considering contributing! This document outlines the development workflow and standards.

## Getting Started

### Prerequisites
- Python 3.10 or higher
- Git
- Basic understanding of web scraping and content similarity

### Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/web-similarity-audit.git
cd web-similarity-audit
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in editable mode with dev dependencies:
```bash
pip install -e '.[dev]'
```

4. Verify installation:
```bash
pytest tests/ -v
web-similarity-audit --version
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=web_similarity_audit --cov-report=html

# Run specific test file
pytest tests/test_similarity.py -v

# Run specific test
pytest tests/test_similarity.py::test_jaccard_similarity -v
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code with ruff
ruff format .

# Lint code
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Type checking (if mypy is configured)
mypy src/
```

### Manual Testing

Test the CLI with real sites:
```bash
# Small test
web-similarity-audit --crawl https://example.com --max-pages 10

# Test resume functionality
web-similarity-audit --crawl https://example.com --max-pages 100
# Press Ctrl+C to interrupt
web-similarity-audit --resume
```

## Code Standards

### Python Style
- Follow PEP 8 (enforced by ruff)
- Use type hints for function signatures
- Maximum line length: 100 characters
- Prefer explicit over implicit
- Write docstrings for all public functions

Example:
```python
def extract_main_content(html: str, url: str) -> tuple[str, bool]:
    """Extract main content from HTML.
    
    Args:
        html: Raw HTML string
        url: Source URL for debugging
        
    Returns:
        Tuple of (extracted_text, success_flag)
    """
    # Implementation
    pass
```

### Commit Messages
Follow the conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Build process or auxiliary tool changes

Examples:
```
feat(crawler): add support for sitemap.xml parsing

fix(similarity): handle empty content in TF-IDF calculation

docs(readme): add installation instructions for Windows

test(extraction): add test for CJK content extraction
```

### Testing Guidelines

1. **Write tests first** for new features (TDD)
2. **Test edge cases**: empty strings, None values, network errors
3. **Use fixtures** for test data (see `tests/fixtures/`)
4. **Mock external calls**: Use `httpx_mock` for HTTP requests
5. **Test determinism**: Same input should always produce same output

Example test structure:
```python
def test_feature_name():
    # Arrange: Set up test data
    input_data = "test"
    
    # Act: Execute the function
    result = function_under_test(input_data)
    
    # Assert: Verify the result
    assert result == expected_value
```

### Documentation

- Update README.md for user-facing changes
- Update CHANGELOG.md under [Unreleased] section
- Add docstrings to new functions
- Update TODO.md if adding planned features

## Project Structure

```
web-similarity-audit/
├── src/web_similarity_audit/
│   ├── __init__.py
│   ├── __main__.py         # CLI entry point
│   ├── cli.py              # Argument parsing
│   ├── crawler.py          # Website crawling
│   ├── fetcher.py          # HTTP fetching
│   ├── extractor.py        # Content extraction
│   ├── similarity.py       # Similarity algorithms
│   ├── template_detector.py # Template detection
│   ├── reporter.py         # Report generation
│   └── state.py            # Crash recovery
├── tests/
│   ├── fixtures/           # Test data
│   ├── test_*.py           # Test modules
│   └── conftest.py         # Pytest configuration
├── examples/               # Usage examples
├── .github/
│   └── workflows/          # CI/CD pipelines
├── pyproject.toml          # Package configuration
├── README.md
├── CHANGELOG.md
├── TODO.md
└── CONTRIBUTING.md (this file)
```

## Adding Features

### Feature Development Checklist

- [ ] Discuss the feature in an issue first
- [ ] Update TODO.md with the plan
- [ ] Write tests for the feature
- [ ] Implement the feature
- [ ] Update documentation (README, docstrings)
- [ ] Update CHANGELOG.md
- [ ] Ensure all tests pass
- [ ] Run linting and formatting
- [ ] Submit pull request

### Example: Adding a New Similarity Signal

1. **Add to `similarity.py`**:
```python
def compute_cosine_similarity(text1: str, text2: str) -> float:
    """Compute cosine similarity between two texts."""
    # Implementation
    pass
```

2. **Add tests in `tests/test_similarity.py`**:
```python
def test_cosine_similarity():
    assert compute_cosine_similarity("hello", "hello") == 1.0
    assert compute_cosine_similarity("hello", "world") < 0.5
```

3. **Integrate in main workflow** (`__main__.py`)
4. **Update output schema** (add column to pairs.csv)
5. **Update documentation** (README.md similarity signals section)

## Submitting Changes

### Pull Request Process

1. **Create a feature branch**:
```bash
git checkout -b feat/your-feature-name
```

2. **Make changes and commit**:
```bash
git add .
git commit -m "feat(scope): description"
```

3. **Push to your fork**:
```bash
git push origin feat/your-feature-name
```

4. **Open a pull request** on GitHub with:
   - Clear description of the change
   - Link to related issue(s)
   - Screenshots/examples if applicable
   - Confirmation that tests pass

5. **Address review feedback**

6. **Squash commits** if requested before merge

### PR Checklist
- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Code follows style guidelines
- [ ] No merge conflicts with main
- [ ] PR description is clear

## Reporting Issues

### Bug Reports
Include:
- Python version and OS
- Command you ran
- Expected vs actual behavior
- Relevant log output
- Minimal reproducible example

### Feature Requests
Include:
- Use case description
- Proposed solution
- Example usage
- Alignment with project goals (explicit, deterministic, explainable)

## Design Principles

Follow these principles when contributing:

1. **Explicit over implicit**: Report failures, don't hide them
2. **Deterministic**: Same input → same output
3. **Explainable**: Every decision has a traceable reason
4. **Fail fast**: Validate early, exit with clear codes
5. **No silent fallbacks**: Make failures visible

Example of **good** design:
```python
if not extraction_success:
    logger.warning(f"Failed to extract content from {url}")
    return "", False  # Explicit failure
```

Example of **bad** design:
```python
try:
    content = extract(html)
except:
    content = html  # Silent fallback, loses information
```

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md with release date
3. Create git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. GitHub Actions will build and publish to PyPI

## Questions?

- Check [README.md](README.md) for usage
- Check [TODO.md](TODO.md) for roadmap
- Open an [issue](https://github.com/wowayou/web-similarity-audit/issues) for questions

## Code of Conduct

- Be respectful and constructive
- Focus on the code, not the person
- Welcome newcomers and help them learn
- Provide clear, actionable feedback

Thank you for contributing! 🎉
