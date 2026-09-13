# Contributing to Web Similarity Audit

Thank you for considering contributing! This document outlines the development workflow and guidelines.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/web-similarity-audit.git
   cd web-similarity-audit
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. **Install in editable mode with dev dependencies**
   ```bash
   pip install -e .
   pip install pytest pytest-asyncio pytest-cov ruff mypy
   ```

## Running Tests

Run the full test suite:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=src/web_similarity_audit --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_similarity.py -v
```

## Code Quality

### Linting
```bash
ruff check src/ tests/
ruff format src/ tests/  # auto-format
```

### Type Checking
```bash
mypy src/web_similarity_audit --ignore-missing-imports
```

## Coding Standards

- **Python version**: 3.10+
- **Style**: Follow PEP 8, enforced by ruff
- **Imports**: Group stdlib, third-party, local; sort alphabetically
- **Type hints**: Use for public APIs and complex functions
- **Docstrings**: Use for modules, classes, and public functions
- **Line length**: 100 characters (soft limit)

## Commit Messages

Follow conventional commits format:

```
type(scope): brief description

Longer explanation if needed

- Bullet points for details
- Reference issues with #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `ci`: CI/CD changes
- `chore`: Build, dependencies, etc.

Examples:
```
feat(crawler): add sitemap.xml parsing support
fix(extractor): handle empty trafilatura responses
docs: update README with new --resume flag
test: add fixtures for CJK text normalization
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes**
   - Write tests for new functionality
   - Update documentation if needed
   - Run tests and linters locally

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add feature description"
   ```

4. **Push to your fork**
   ```bash
   git push origin feat/your-feature-name
   ```

5. **Open a Pull Request**
   - Describe what the PR does
   - Link related issues
   - Ensure CI passes

## Adding New Features

### Before Starting
1. Check TODO.md and existing issues
2. Open an issue to discuss major changes
3. Get feedback on approach before investing time

### Implementation Checklist
- [ ] Write tests first (TDD encouraged)
- [ ] Implement feature following existing patterns
- [ ] Update docstrings and type hints
- [ ] Add usage examples to README if user-facing
- [ ] Update CHANGELOG.md under [Unreleased]
- [ ] Ensure all tests pass
- [ ] Run linters and fix issues

### Testing Guidelines
- Unit tests in `tests/test_*.py`
- Use fixtures in `tests/fixtures/`
- Mock external HTTP calls
- Test edge cases and error paths
- Aim for >80% coverage for new code

## Project Structure

```
src/web_similarity_audit/
├── cli.py              # Entry point, argument parsing
├── crawler.py          # Website crawling logic
├── fetcher.py          # HTTP client with SSRF protection
├── extractor.py        # Content extraction (trafilatura)
├── template.py         # Template block detection
├── similarity.py       # Similarity algorithms
├── reporter.py         # Report generation
├── state.py            # Crash recovery
├── models.py           # Data classes
└── utils.py            # Utilities (normalization, etc.)

tests/
├── test_*.py           # Test modules
└── fixtures/           # Test data
```

## Design Principles

1. **Explicit over implicit**: Report failures, don't hide them
2. **Deterministic**: No randomness, same input = same output
3. **Explainable**: Every decision has a reason users can inspect
4. **Fail fast**: Validate early, exit with clear error codes
5. **No silent fallbacks**: If extraction fails, say so explicitly

## Common Tasks

### Adding a New Similarity Signal

1. Add computation in `similarity.py`:
   ```python
   def compute_new_signal(text_a: str, text_b: str) -> float:
       """Compute new similarity metric."""
       # Implementation
       return score
   ```

2. Update `SimilarityResult` model in `models.py`
3. Add to comparison logic in `similarity.py`
4. Update priority thresholds if needed
5. Add tests in `tests/test_similarity.py`
6. Document in README

### Adding a New CLI Flag

1. Add argument in `cli.py` `setup_parser()`
2. Pass to relevant function
3. Update help text
4. Add to README usage section
5. Test with `pytest tests/test_integration.py`

## Getting Help

- Open an issue for bugs or feature requests
- Tag @maintainers for questions
- Check existing issues and PRs first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
