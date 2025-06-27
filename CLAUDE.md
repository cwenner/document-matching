# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CRITICAL: How to Work with This Codebase

When working with this repository, you MUST follow this process:

1. **Read ALL documentation first** - Before any exploration, read every .md file in the root directory completely
2. **Follow the provided roadmap** - If documentation specifies key files to understand, read those files first in the specified order
3. **Use the specified commands** - If documentation provides testing/development commands, use those exact commands
4. **Work systematically through the documentation's guidance** - Don't invent your own exploration approach when explicit guidance exists

Random exploration when structured guidance exists is prohibited. This documentation is your mandatory roadmap - follow it systematically.

## Project Overview

This is a document matching service that compares documents (invoices, purchase orders, delivery receipts) to find matches and generate matching reports. The system uses machine learning models and rule-based matching to identify document pairs and analyze deviations.

## Repository Structure

- **src/**: Core source code (FastAPI app, matching service, ML pipeline)
- **tests/**: Test suite with acceptance (BDD), unit, and integration tests
- **features/**: BDD feature definitions organized by user perspective
- **data/**: ML models and test datasets organized by document type
- **docs/**: API specifications and documentation

## Key Architecture Components

### Core Services
- **FastAPI App** (`src/app.py`): Main API server with health endpoint and document matching endpoint
- **MatchingService** (`src/matching_service.py`): Core service handling document processing with lazy initialization
- **DocumentPairingPredictor** (`src/docpairing.py`): ML model wrapper for document similarity prediction
- **Match Pipeline** (`src/match_pipeline.py`): Orchestrates the matching process between documents

### Key Processing Flow
1. Documents arrive via POST to `/` endpoint with candidate documents
2. MatchingService processes using either:
   - Real ML pipeline for whitelisted sites (badger-logistics, falcon-logistics, etc.)
   - Dummy logic for non-whitelisted sites
3. Results are formatted as v3 match reports with deviations and item pairs

### Data Structure
- Test data in `data/converted-shared-data/` organized by document type and supplier
- ML model stored in `data/models/document-pairing-svm.pkl`
- Feature files in `features/` directory using Gherkin BDD format

## Common Development Commands

### Environment Setup
```bash
source .venv/bin/activate
```

### Running the Service
```bash
PYTHONPATH=src uvicorn app:app
```

### Testing the Service
```bash
# Send test request to running server
PYTHONPATH=src python -m try_client

# Run all tests and linting
nox

# Run just tests
nox -s test

# Run just linting (black formatting check)
nox -s lint

# Run specific test markers
pytest -m api
pytest -m smoke
pytest -m core_matching
```

### Running Evaluations
```bash
# Direct function calls (recommended)
PYTHONPATH=src python -m evaluate_matching --dataset ../popoc/data/pairing_sequential.json --max-tested 100 --skip-portion 0.5

# Using API calls (requires running server)
PYTHONPATH=src python -m evaluate_matching --dataset ../popoc/data/pairing_sequential.json --max-tested 100 --skip-portion 0.5 --use-api
```

### Code Formatting
```bash
black src/ tests/
```

## Important Configuration

### Environment Variables
- `DISABLE_MODELS=true`: Disables ML model loading, uses dummy logic only
- `DOCPAIR_MODEL_PATH`: Custom path to ML model file

### Whitelisted Sites
Sites that use real ML pipeline: badger-logistics, falcon-logistics, christopher-test, test-site

### Test Structure
- BDD tests in `features/` with step definitions in `tests/acceptance/steps/`
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- API tests in `tests/api/`

## Key Files to Understand
- `src/matching_service.py:304`: Whitelist logic determining real vs dummy processing
- `src/app.py:40`: Main request handler with validation and error handling
- `src/match_reporter.py`: V3 match report generation with deviation detection
- `tests/acceptance/steps/api_steps.py`: BDD step definitions for API testing
- `tests/config.py`: Test configuration and path management
- `noxfile.py`: Test and lint session configuration
- `pytest.ini`: Test markers and warning filters
- `features/`: BDD scenarios organized by user perspective
- `CONTRIBUTING.md`: Developer guide for contributing to the project