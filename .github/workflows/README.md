# GitHub Actions Workflows

This repository uses GitHub Actions for CI/CD with PyPI Trusted Publisher (OIDC) authentication.

## Workflows

### 1. CI (`ci.yml`)
- **Trigger**: Push to main/develop, pull requests
- **Purpose**: Run tests, linting, and build checks
- **Jobs**:
  - Lint with Ruff and MyPy
  - Test on Python 3.9-3.12
  - Build and check distribution

### 2. Deploy to PyPI (`deploy.yml`)
- **Trigger**: Git tags matching `v*` (e.g., vX.Y.Z)
- **Purpose**: Deploy releases to PyPI
- **Uses**: OIDC Trusted Publisher (no API token needed!)
- **Environment**: `pypi` (configured in PyPI settings)

### 3. Test Deploy (`test-deploy.yml`)
- **Trigger**: Push to main/develop, manual
- **Purpose**: Test deployment to TestPyPI
- **Environment**: `testpypi`

### 4. Release Pipeline (`release.yml`)
- **Trigger**: GitHub release creation
- **Purpose**: Full release pipeline with tests
- **Steps**:
  1. Run comprehensive tests
  2. Build and validate package
  3. Deploy to PyPI with attestations
  4. Upload artifacts to GitHub release
  5. Verify deployment

## Setup Requirements

### PyPI Trusted Publisher Configuration

Already configured on PyPI.org:
- **Project**: youtrack-rocket-mcp
- **Repository**: ivolnistov/youtrack-rocket-mcp
- **Workflow**: deploy.yml
- **Environment**: pypi

### GitHub Repository Settings

1. **Environments**: Create `pypi` environment
   - Go to Settings → Environments → New environment
   - Name: `pypi`
   - Optional: Add protection rules (e.g., required reviewers)

2. **Tags Protection** (optional):
   - Settings → Tags → Protection rules
   - Pattern: `v*`
   - Only allow users with write access

## How to Release

### Option 1: Using Git Tags
```bash
# Update version in src/youtrack_rocket_mcp/version.py
git add .
git commit -m "Release vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

### Option 2: Using GitHub Release UI
1. Go to Releases → Create new release
2. Choose a tag (e.g., vX.Y.Z)
3. Fill in release notes
4. Click "Publish release"

The workflow will automatically:
- Build the package
- Upload to PyPI using Trusted Publisher
- Generate Sigstore attestations
- No API tokens needed!

## Security Benefits

Using Trusted Publisher provides:
- **No long-lived tokens**: Uses short-lived OIDC tokens
- **Sigstore attestations**: Cryptographic proof of build provenance
- **GitHub identity**: Links package to specific repo/workflow
- **Automatic token rotation**: Tokens expire after each use

## Troubleshooting

### If deployment fails:
1. Check PyPI trusted publisher settings match exactly:
   - Repository name (case-sensitive)
   - Workflow filename
   - Environment name

2. Ensure `id-token: write` permission is set

3. Verify environment `pypi` exists in GitHub settings

### Manual deployment (emergency):
```bash
python -m pip install build twine
python -m build
twine upload dist/*  # Will need API token
```