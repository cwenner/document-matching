import nox
import os.path
from pathlib import Path
import requests
import shutil

# Default sessions are now the top-level categories
nox.options.sessions = ["download_models", "lint", "test"]
nox.options.reuse_existing_virtualenvs = True

MODEL_URLS = {
    "data/models/document-pairing-svm.pkl": "https://nuprodsandbox.blob.core.windows.net/models/document-pairing-svm.pkl?sp=r&st=2025-06-26T23:46:58Z&se=2026-06-27T07:46:58Z&spr=https&sv=2024-11-04&sr=b&sig=6DBiPYVdDaaw2ES2vDSGr5Q4mlPPa6HURXf66GNdNL0%3D",
}


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
    """Check if all required model files exist in their expected locations."""
    missing_models = []
    
    for model_path in MODEL_URLS.keys():
        if not Path(model_path).exists():
            missing_models.append(model_path)
    
    if missing_models:
        raise FileNotFoundError(f"Required model file(s) not found: {', '.join(missing_models)}")
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
            with open(path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to download model from {url}: {str(e)}")


@nox.session(python=["3.12"])
def download_models(session: nox.Session):
    """Download required model files if they don't already exist."""
    # Install requests if not already available
    session.install("requests")
    
    downloaded = False
    for model_path, url in MODEL_URLS.items():
        path = Path(model_path)
        if not path.exists():
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

