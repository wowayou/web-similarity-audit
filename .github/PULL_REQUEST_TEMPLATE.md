## Description

Brief description of the changes in this PR.

## Motivation

Why is this change needed? What problem does it solve?

Fixes #(issue number)

## Changes

- Change 1
- Change 2
- Change 3

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Test improvements

## Testing

How was this tested?

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All tests pass locally

**Test commands run:**
```bash
pytest tests/ -v
```

**Manual testing steps:**
1. Step 1
2. Step 2

## Documentation

- [ ] Updated README.md (if needed)
- [ ] Updated CHANGELOG.md
- [ ] Updated API docs (if needed)
- [ ] Added/updated docstrings
- [ ] Updated examples (if needed)

## Code Quality

- [ ] Code follows project style guidelines
- [ ] Self-review performed
- [ ] Comments added for complex logic
- [ ] No new warnings introduced
- [ ] Type hints added/updated

**Pre-commit checks:**
```bash
black src/ tests/
ruff check src/ tests/
mypy src/
pytest tests/ --cov
```

## Screenshots/Output (if applicable)

Before:
```
[paste output or screenshot]
```

After:
```
[paste output or screenshot]
```

## Breaking Changes

Does this PR introduce breaking changes? If yes, describe:

- What breaks
- Migration path for users
- Deprecation notices added

## Additional Notes

Any additional information or context.

## Checklist

- [ ] My code follows the project's code style
- [ ] I have performed a self-review
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
