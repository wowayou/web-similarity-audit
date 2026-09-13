# Pull Request

## Description

<!-- Provide a clear description of your changes -->

## Type of Change

<!-- Check all that apply -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Test improvement

## Related Issues

<!-- Link to related issues -->

Fixes #
Relates to #

## Changes Made

<!-- Detailed list of changes -->

- 
- 
- 

## Testing

<!-- Describe the tests you ran and how to reproduce -->

### Test Commands

```bash
# Commands used to test
pytest tests/ -v
web-similarity-audit --crawl https://example.com --max-pages 50
```

### Test Results

- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

**Test coverage:**
<!-- Output of pytest --cov -->

```
```

### Test Environment

- OS: <!-- e.g., Ubuntu 22.04, macOS 13, Windows 11 -->
- Python: <!-- e.g., 3.10.5 -->
- Installation: <!-- pipx, pip, from source -->

## Documentation

<!-- Check all that apply -->

- [ ] Updated README.md
- [ ] Updated relevant docs in docs/
- [ ] Updated CHANGELOG.md
- [ ] Added docstrings to new functions
- [ ] Updated type hints

## Checklist

<!-- Ensure all items are completed -->

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Performance Impact

<!-- If applicable, describe performance impact -->

**Before:**
```
Time: X seconds
Memory: Y MB
```

**After:**
```
Time: X seconds
Memory: Y MB
```

## Breaking Changes

<!-- If this is a breaking change, describe migration path -->

**Migration guide:**

```bash
# Before
web-similarity-audit old-command

# After
web-similarity-audit new-command
```

## Screenshots

<!-- If applicable, add screenshots -->

## Additional Notes

<!-- Any additional information for reviewers -->

---

## Reviewer Checklist

<!-- For maintainers -->

- [ ] Code quality and style
- [ ] Test coverage adequate
- [ ] Documentation complete
- [ ] No security concerns
- [ ] Performance acceptable
- [ ] Breaking changes justified
- [ ] CHANGELOG.md updated
