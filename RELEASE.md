# Release Process

This document describes the release process for web-similarity-audit.

## Versioning

We use [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backwards-compatible manner
- **PATCH** version for backwards-compatible bug fixes

## Pre-Release Checklist

Before creating a release:

1. **Update version number**
   ```bash
   # In pyproject.toml
   version = "0.2.0"  # Update this line
   ```

2. **Update CHANGELOG.md**
   - Add a new section for the version
   - List all changes under appropriate categories:
     - Added
     - Changed
     - Deprecated
     - Removed
     - Fixed
     - Security
   - Include issue/PR references
   - Set release date

3. **Run full test suite**
   ```bash
   pytest tests/ -v
   ```

4. **Test package build**
   ```bash
   python -m build
   pip install dist/*.whl
   web-similarity-audit --version
   ```

5. **Update documentation**
   - README.md
   - README.zh-CN.md
   - Any API changes
   - Examples if needed

6. **Commit changes**
   ```bash
   git add pyproject.toml CHANGELOG.md README.md
   git commit -m "chore: bump version to 0.2.0"
   git push origin main
   ```

## Creating a Release

### 1. Create and push a git tag

```bash
# Ensure you're on main and up to date
git checkout main
git pull origin main

# Create annotated tag
git tag -a v0.2.0 -m "Release version 0.2.0"

# Push tag to trigger release workflow
git push origin v0.2.0
```

### 2. Automated release process

The GitHub Actions workflow will automatically:
1. Build source distribution and wheel
2. Run `twine check` for package validation
3. Publish to PyPI (requires trusted publishing setup)
4. Extract changelog for this version
5. Create GitHub release with artifacts
6. Sign distributions with Sigstore

### 3. Verify the release

1. **Check PyPI**
   - Visit https://pypi.org/project/web-similarity-audit/
   - Verify version appears
   - Check that README renders correctly

2. **Test installation**
   ```bash
   pip install --upgrade web-similarity-audit
   web-similarity-audit --version
   ```

3. **Check GitHub Release**
   - Visit https://github.com/wowayou/web-similarity-audit/releases
   - Verify release notes are correct
   - Download and verify artifacts

### 4. Announce the release

- Update any relevant project pages
- Post to relevant communities if significant
- Update documentation sites if any

## PyPI Trusted Publishing Setup

This project uses PyPI's trusted publishing (no API tokens needed).

### First-time setup (maintainer only)

1. Go to PyPI project settings:
   https://pypi.org/manage/project/web-similarity-audit/settings/

2. Scroll to "Publishing" section

3. Add a new publisher:
   - **PyPI Project Name**: `web-similarity-audit`
   - **Owner**: `wowayou`
   - **Repository name**: `web-similarity-audit`
   - **Workflow name**: `release.yml`
   - **Environment name**: `pypi`

4. The workflow will now be able to publish without manual API tokens

## Hotfix Releases

For critical bugs in production:

1. Create hotfix branch from the release tag:
   ```bash
   git checkout -b hotfix/v0.2.1 v0.2.0
   ```

2. Fix the bug and commit:
   ```bash
   git commit -m "fix: critical bug description"
   ```

3. Update version and changelog

4. Create pull request to main

5. After merge, tag and release:
   ```bash
   git checkout main
   git pull
   git tag -a v0.2.1 -m "Hotfix release 0.2.1"
   git push origin v0.2.1
   ```

## Release Cadence

- **Patch releases**: As needed for bug fixes
- **Minor releases**: Monthly or when significant features are ready
- **Major releases**: When breaking changes are necessary

## Rollback Procedure

If a release has critical issues:

1. **Yank the release on PyPI** (does not delete, marks as unavailable):
   - Go to PyPI project page
   - Find the problematic version
   - Click "Options" → "Yank release"
   - Provide reason

2. **Mark GitHub release as pre-release** or delete:
   - Go to GitHub releases
   - Edit the release
   - Check "This is a pre-release"
   - Or delete if not yet widely used

3. **Release a fix**:
   - Follow hotfix process above
   - Bump patch version
   - Document the issue in changelog

## Post-Release

1. **Monitor for issues**
   - Watch GitHub issues
   - Monitor PyPI download stats
   - Check for user feedback

2. **Plan next release**
   - Update TODO.md
   - Move completed items to CHANGELOG.md
   - Set milestones for next version

## Troubleshooting

### Release workflow fails

1. Check GitHub Actions logs
2. Common issues:
   - PyPI trusted publishing not configured
   - Test failures
   - Build errors
   - Changelog extraction failed

### Package not appearing on PyPI

1. Wait 5-10 minutes (indexing delay)
2. Check workflow completed successfully
3. Verify PyPI account permissions
4. Check for email from PyPI about failures

### Version conflict

If you accidentally pushed the same version:
1. Delete the git tag locally and remotely:
   ```bash
   git tag -d v0.2.0
   git push origin :refs/tags/v0.2.0
   ```
2. Bump version number
3. Create new tag

## Security Releases

For security vulnerabilities:

1. **Do not disclose publicly until fixed**
2. Follow SECURITY.md reporting process
3. Prepare fix in private
4. Coordinate disclosure timeline
5. Release with security advisory:
   - GitHub Security Advisory
   - Mention CVE if assigned
   - Credit reporter (if they agree)

## Questions?

Contact maintainers or open a discussion on GitHub.
