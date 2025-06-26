import nox
import os.path
from pathlib import Path

# Default sessions are now the top-level categories
nox.options.sessions = ["lint", "test"]
nox.options.reuse_existing_virtualenvs = True


@nox.session(python=["3.12"])
def test(session: nox.Session):
    """Run all tests (pytest-bdd and unit)."""
    # Validate model existence before running tests
    try:
        check_model_exists()
        session.log("Required model file verified")
    except FileNotFoundError as e:
        session.error(str(e))
        
    # Install all dependencies, including dev ones
    session.install("-r", "requirements-dev.txt")

    # Run pytest
    # Pass any arguments from the nox command line to pytest
    session.run("pytest", "tests", *session.posargs, env={"PYTHONPATH": "src"})


@nox.session(python=["3.12"])
def lint(session: nox.Session):
    """Lint using black and potentially other linters in the future."""
    session.install("black")
    session.run("black", ".", "--check")  # Check formatting for all files


# @TODO later add ruff and custom code-quality checks.


def check_model_exists():
    """Check if the required model file exists in the expected location."""
    model_path = Path("data/models/document-pairing-svm.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Required model file not found: {model_path}")
    return True

