"""Nox configuration for automated testing and development tasks."""

import os
import shutil
from pathlib import Path

import nox
import requests

# Default sessions to run when called without arguments
nox.options.sessions = ["test", "lint", "type_check", "format"]
nox.options.reuse_existing_virtualenvs = True

# Python versions to test against
PYTHON_VERSIONS = ["3.12"]

# Project directories
ROOT = Path(__file__).parent
SRC_DIR = ROOT / "src"
TESTS_DIR = ROOT / "tests"

# Environment variables to pass to all sessions
ENV = {
    "PYTHONPATH": str(SRC_DIR),
    "PYTHONUNBUFFERED": "1",
}

# Model download configuration
# Get model URL from environment variable for security
MODEL_URL = os.environ.get("DOCUMENT_PAIRING_MODEL_URL")

MODEL_URLS = {
    "data/models/document-pairing-svm.pkl": MODEL_URL,
}


def is_ci_environment():
    """Detect if running in CI environment."""
    ci_indicators = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_URL",
        "TRAVIS",
        "CIRCLECI",
    ]
    return any(os.environ.get(var) for var in ci_indicators)


def _should_skip_install(session, packages):
    """Check if installation can be skipped - simple approach."""
    # In CI, never skip
    if is_ci_environment():
        return False

    # For now, always return False to avoid using private nox APIs
    # This ensures compatibility across nox versions
    return False


def _mark_install_complete(session):
    """Mark that installation was completed."""
    # Skip marking to avoid using private nox APIs
    # This ensures compatibility across nox versions
    pass


def install_with_cache(session, *packages, force_reinstall=False, editable=False):
    """Install packages with caching logic.

    Args:
        session: The nox session
        *packages: Package specifications to install
        force_reinstall: Force reinstallation even if cached
        editable: Whether to install in editable mode
    """
    # Check for force flag from environment or arguments
    if not force_reinstall:
        force_env = os.environ.get("NOX_FORCE_REINSTALL", "").lower()
        force_reinstall = force_env in ("1", "true", "yes")
        if not force_reinstall and session.posargs:
            force_reinstall = "--force-reinstall" in session.posargs

    # Always reinstall in CI or when forced
    if force_reinstall or is_ci_environment():
        install_args = ["--no-compile", "--no-warn-script-location"]
        if editable:
            session.install("-e", *packages, *install_args)
        else:
            session.install(*packages, *install_args)
        _mark_install_complete(session)
        return

    # For local dev with reused env, check if we need to install
    if _should_skip_install(session, packages):
        session.log("📦 Skipping install - dependencies already satisfied")
        return

    # Install with optimizations
    install_args = [
        "--no-compile",
        "--no-warn-script-location",
        "--upgrade-strategy",
        "only-if-needed",
    ]
    if editable:
        session.install("-e", *packages, *install_args)
    else:
        session.install(*packages, *install_args)

    _mark_install_complete(session)


@nox.session(python=PYTHON_VERSIONS)
def test(session: nox.Session) -> None:
    """Run all tests (pytest-bdd and unit)."""
    # Validate model existence before running tests
    try:
        check_model_exists()
        session.log("Required model file verified")
    except FileNotFoundError as e:
        session.error(str(e))

    # Install all dependencies
    install_with_cache(session, "-r", "requirements-dev.txt")

    # Run pytest with coverage
    session.run(
        "pytest",
        "tests",
        *session.posargs,
        env=ENV,
    )


@nox.session(python=PYTHON_VERSIONS[0])
def lint(session: nox.Session) -> None:
    """Lint code with flake8, black and isort."""
    install_with_cache(session, "black", "isort", "flake8")

    files = ["src", "tests", "noxfile.py"]

    # Run isort check
    session.run("isort", "--check-only", "--profile=black", *files)

    # Run black check
    session.run("black", "--check", *files)

    # Run flake8
    session.run("flake8", *files)


@nox.session(python=PYTHON_VERSIONS[0])
def type_check(session: nox.Session) -> None:
    """Check types with pyright."""
    install_with_cache(session, "pyright")

    # Run pyright
    session.run("pyright", str(SRC_DIR), env=ENV)


@nox.session(python=PYTHON_VERSIONS[0])
def format(session: nox.Session) -> None:
    """Format code with black and isort."""
    install_with_cache(session, "black", "isort")

    files = ["src", "tests", "noxfile.py"]

    # Run isort
    session.run("isort", "--profile=black", *files)

    # Run black
    session.run("black", *files)


@nox.session(python=PYTHON_VERSIONS[0])
def checks(session: nox.Session) -> None:
    """Run all quality checks: format, lint, type_check, and tests."""
    # Notify will run the sessions with the same Python version
    session.notify("format")
    session.notify("lint")
    session.notify("type_check")
    session.notify("test")


@nox.session(python=PYTHON_VERSIONS[0])
def dev(session: nox.Session) -> None:
    """Start the development server."""
    # Ensure models are available
    session.notify("download_models")

    # Install dependencies
    install_with_cache(session, "-r", "requirements.txt")

    # Run uvicorn
    session.run(
        "uvicorn",
        "src.api:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        env=ENV,
    )


@nox.session(python=PYTHON_VERSIONS[0])
def build(session: nox.Session) -> None:
    """Build the package."""
    install_with_cache(session, "build", "twine")

    # Clean previous builds
    session.run("rm", "-rf", "dist", "build", external=True)

    # Build the package
    session.run("python", "-m", "build")

    # Check the built package
    session.run("twine", "check", "dist/*")


@nox.session(python=PYTHON_VERSIONS[0])
def clean(session: nox.Session) -> None:
    """Clean up build artifacts and cache."""
    # Remove Python cache files
    session.run(
        "find",
        ".",
        "-type",
        "d",
        "-name",
        "__pycache__",
        "-exec",
        "rm",
        "-rf",
        "{}",
        "+",
        external=True,
    )

    # Remove Python compiled files
    session.run(
        "find",
        ".",
        "-type",
        "f",
        "-name",
        "*.py[co]",
        "-delete",
        external=True,
    )

    # Remove build artifacts
    session.run(
        "rm",
        "-rf",
        "build",
        "dist",
        "*.egg-info",
        ".pytest_cache",
        ".coverage",
        "coverage.xml",
        "htmlcov",
        ".mypy_cache",
        ".pytype",
        ".ruff_cache",
        external=True,
    )

    # Remove nox artifacts
    session.run("rm", "-rf", ".nox", external=True)


def check_model_exists():
    """Check if all required model files exist in their expected locations."""
    missing_models = []

    for model_path in MODEL_URLS.keys():
        if not Path(model_path).exists():
            missing_models.append(model_path)

    if missing_models:
        raise FileNotFoundError(
            f"Required model file(s) not found: {', '.join(missing_models)}"
        )
    return True


def download_model(model_path, url):
    """Download a model file from the specified URL."""
    path = Path(model_path)

    # Create directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Download the file
        with requests.get(url, stream=True) as response:
            response.raise_for_status()  # Raise an error for bad responses
            with open(path, "wb") as f:
                shutil.copyfileobj(response.raw, f)
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to download model from {url}: {str(e)}")


@nox.session(python=PYTHON_VERSIONS[0])
def download_models(session: nox.Session) -> None:
    """Download required model files if they don't already exist."""
    # Install requests if not already available
    install_with_cache(session, "requests")

    downloaded = False
    for model_path, url in MODEL_URLS.items():
        path = Path(model_path)
        if not path.exists():
            if url is None:
                session.error(
                    f"Model {model_path} is missing and no download URL is configured. "
                    "Please set DOCUMENT_PAIRING_MODEL_URL environment variable."
                )
                continue
            try:
                session.log(f"Downloading model: {model_path}")
                download_model(model_path, url)
                session.log(f"Successfully downloaded model to {model_path}")
                downloaded = True
            except Exception as e:
                session.error(f"Failed to download model {model_path}: {str(e)}")

    if not downloaded:
        session.log("All model files already exist, no downloads needed.")

    # Validate that all required models exist
    try:
        check_model_exists()
        session.log("All required model files verified.")
    except FileNotFoundError as e:
        session.error(str(e))
