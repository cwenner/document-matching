import nox

# Default sessions are now the top-level categories
nox.options.sessions = ["lint", "test"]
nox.options.reuse_existing_virtualenvs = True


@nox.session(python=["3.12"])
def test(session: nox.Session):
    """Run all tests (pytest-bdd and unit)."""
    # Install all dependencies, including dev ones
    session.install("-r", "requirements-dev.txt")

    # Run pytest
    # Pass any arguments from the nox command line to pytest
    session.run("pytest", *session.posargs, env={"PYTHONPATH": "src"})


@nox.session(python=["3.12"])
def lint(session: nox.Session):
    """Lint using black and potentially other linters in the future."""
    session.install("black")
    session.run("black", ".", "--check")  # Check formatting for all files


# @TODO later add ruff and custom code-quality checks.
