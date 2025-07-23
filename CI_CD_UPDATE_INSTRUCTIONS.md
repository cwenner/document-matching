# CI/CD Update Instructions

This document outlines the necessary updates to the CI/CD pipeline configuration following the linting and type checking fixes applied to the codebase.

## Overview of Changes

The following fixes have been applied to ensure code quality compliance:

1. **Flake8 Linting**: Fixed all linting errors including:
   - F401: Removed unused imports
   - F541: Fixed f-strings without placeholders
   - E722: Fixed bare except clauses (changed to `except Exception:`)
   - F811: Fixed redefinition errors in pytest-bdd test files
   - F841: Fixed unused variable warnings

2. **Type Checking**: Fixed Python 3.9 compatibility issues:
   - Changed `StrEnum` to `str, Enum` inheritance pattern
   - Updated union syntax from `|` to `Union/Optional`
   - Fixed datetime comparison with None handling
   - Added proper type annotations

## CI/CD Configuration Updates

### 1. Update GitHub Actions Workflow

Ensure your `.github/workflows/ci.yml` (or similar) includes the following checks:

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 pyright
    
    - name: Run flake8
      run: |
        flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Run pyright
      run: |
        pyright src/
  
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 2. Update Pre-commit Hooks

Add or update `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203,W503']

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: local
    hooks:
      - id: pyright
        name: pyright
        entry: pyright
        language: system
        types: [python]
        pass_filenames: false
        args: [src/]
```

### 3. Update noxfile.py

Ensure your `noxfile.py` includes proper linting and type checking sessions:

```python
import nox

@nox.session(python=["3.9", "3.10", "3.11", "3.12"])
def lint(session):
    """Run linters."""
    session.install("flake8", "black", "isort")
    session.run("black", "--check", "src", "tests")
    session.run("isort", "--check-only", "src", "tests")
    session.run("flake8", "src", "tests")

@nox.session(python=["3.9", "3.10", "3.11", "3.12"])
def typecheck(session):
    """Run type checking."""
    session.install("pyright", "-e", ".")
    session.run("pyright", "src")

@nox.session(python=["3.9", "3.10", "3.11", "3.12"])
def test(session):
    """Run tests."""
    session.install("-e", ".[dev]")
    session.run("pytest", "tests/", "-v", "--cov=src")
```

### 4. Dependencies to Ensure Are Installed

Make sure these development dependencies are in your `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-bdd",
    "pytest-mock",
    "pytest-cov",
    "black",
    "isort",
    "flake8",
    "pyright",
    "nox",
]
```

### 5. Environment Variables for CI

Set these environment variables in your CI/CD pipeline:

```bash
# For model loading (if using ML models)
DOCPAIR_MODEL_PATH=/path/to/model.pkl

# For disabling models in tests if needed
DISABLE_MODELS=false

# Python path for tests
PYTHONPATH=src
```

### 6. Handling Flake8 Configuration

Create or update `.flake8` configuration file:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    .venv,
    .eggs,
    *.egg,
    build,
    dist
per-file-ignores =
    # F811: redefinition of unused name from line N (common in pytest-bdd)
    tests/**/test_*.py:F811
```

### 7. Handling Type Checking Configuration

Create or update `pyproject.toml` with pyright configuration:

```toml
[tool.pyright]
pythonVersion = "3.9"
typeCheckingMode = "basic"
include = ["src"]
exclude = ["**/__pycache__", ".venv", "build", "dist"]
reportMissingImports = true
reportMissingTypeStubs = false
```

## Migration Notes

1. **Python Version Compatibility**: The code has been updated to be compatible with Python 3.9+. Ensure CI/CD tests against all supported versions.

2. **Type Annotations**: Type annotations have been added/fixed. Consider gradually increasing type checking strictness.

3. **Test Dependencies**: Some tests require heavy dependencies like `sentence-transformers`. Consider:
   - Using dependency caching in CI to speed up builds
   - Creating separate test suites for unit vs integration tests
   - Mocking heavy dependencies for unit tests

4. **Model Files**: If your tests require ML model files, ensure they are either:
   - Stored in a CI-accessible location (e.g., S3, artifact storage)
   - Mocked for unit tests
   - Downloaded as part of the CI setup step

## Verification Steps

After updating CI/CD configuration:

1. Run `flake8 src/` locally - should pass with no errors
2. Run `pyright src/` locally - should pass with no errors  
3. Run `pytest tests/` locally - should pass (with proper dependencies installed)
4. Push changes to a feature branch and verify CI passes
5. Ensure all matrix builds (Python 3.9-3.12) pass

## Rollback Plan

If issues arise:

1. The original code is preserved in git history
2. Flake8 ignore comments (`# noqa`) have been added sparingly and can be reviewed
3. Type annotations can be gradually removed if causing issues
4. Python 3.10+ syntax can be reverted to 3.9 compatible syntax as done in this update