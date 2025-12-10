# Document-Matcher

A document matching service that compares documents (invoices, purchase orders, delivery receipts) to find matches and generate matching reports. The system uses machine learning models and rule-based matching to identify document pairs and analyze deviations.

## Table of Contents

- [Project Overview](#project-overview)
- [Matching Topology](#matching-topology)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [Development](#development)
- [Testing](#testing)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Contributing](#contributing)

## Project Overview

The Document-Matcher service provides:
- Document similarity prediction using ML models
- Rule-based matching for document pairs
- Deviation analysis between matched documents
- RESTful API for document matching requests
- Comprehensive test suite with BDD scenarios

## Matching Topology

The system uses a **PO-Hub Model** for document matching (see [ADR-001](docs/decisions/ADR-001-matching-topology.md)):

```
Invoice ←→ PO ←→ Delivery Receipt
         (hub)
```

### How It Works

| Matching Direction | Method | Status |
|-------------------|--------|--------|
| Invoice → PO | Reference + ML fallback | Implemented |
| PO → Invoice | Reference + ML fallback | Implemented |
| Delivery → PO | Reference matching | Implemented |
| PO → Delivery | Reference matching | Implemented |
| Invoice ↔ Delivery | Transitive (via shared PO) | Implemented |

### Key Design Decisions

1. **PO as Hub**: The Purchase Order serves as the central document linking invoices and deliveries
2. **Transitive Matching**: Invoice-to-Delivery relationships are inferred through shared PO references
3. **Bidirectional ML**: ML fallback works for both Invoice→PO and PO→Invoice via canonical order normalization ([ADR-002](docs/decisions/ADR-002-model-architecture.md))

For architectural details, see the [Architecture Decision Records](docs/decisions/)

## Repository Structure

```
document-matching/
├── src/                    # Core source code
│   ├── app.py             # FastAPI application
│   ├── matching_service.py # Core matching service
│   ├── docpairing.py      # ML model wrapper
│   └── match_pipeline.py  # Matching orchestration
├── tests/                  # Test suite
│   ├── acceptance/        # BDD step definitions
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── api/               # API tests
├── features/              # BDD feature files
│   ├── api-consumer/      # API usage scenarios
│   ├── developer/         # Development support features
│   ├── evaluation/        # Performance evaluation features
│   └── operational/       # Operational features
├── data/                  # ML models and test data
│   ├── models/            # Trained ML models
│   └── converted-shared-data/ # Test datasets
├── docs/                  # API documentation
├── CONTRIBUTING.md        # Contribution guidelines
├── noxfile.py            # Test automation config
└── pytest.ini            # Test configuration
```

## Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment

### Setup

1. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development dependencies
```

3. Download ML models:
```bash
nox -s download_models
```

### Running the Service

Start the API server:
```bash
PYTHONPATH=src uvicorn app:app
```

Test the service:
```bash
PYTHONPATH=src python -m try_client
```

## Development

### Running Tests

```bash
# Run all tests and linting
nox

# Download models (requires DOCUMENT_PAIRING_MODEL_URL environment variable)
# Contact repository maintainers for the model URL
export DOCUMENT_PAIRING_MODEL_URL="<model-url>"
nox -s download_models

# Run only tests
nox -s test

# Run only linting (black formatting check)
nox -s lint

# Run specific test categories using markers
pytest -m api              # API tests only
pytest -m smoke            # Smoke tests
pytest -m core_matching    # Core matching functionality
pytest -m implemented      # Only implemented features
pytest -m "not wip"        # Skip work-in-progress tests
```

## Model Download

The document matching service requires a pre-trained SVM model. To download the model:

1. Contact the repository maintainers to obtain the model download URL
2. Set the environment variable: `export DOCUMENT_PAIRING_MODEL_URL="<model-url>"`
3. Run: `nox -s download_models`

Note: In CI/CD environments, the model is downloaded during the Docker build process.

### Available Test Markers

The project uses pytest markers to categorize tests:
- `api`, `health`, `smoke` - Test types
- `model`, `core_matching` - Feature areas
- `deviations`, `amount_deviation`, `quantity_deviation` - Deviation types
- `story-1.1`, `story-1.2`, etc. - User story tracking
- `implemented`, `wip`, `not_implemented` - Implementation status

See `pytest.ini` for the complete list.

### Code Formatting

Format code using black:
```bash
black src/ tests/
```

## Testing

### BDD Tests

The project uses Behavior-Driven Development with Gherkin feature files organized by user perspective:

- **api-consumer/** - API usage scenarios
- **developer/** - Development and debugging features
- **evaluation/** - Performance and accuracy evaluation
- **operational/** - Health checks and operational features

### Running Evaluations

Evaluate matching performance using the evaluation script:

#### Direct function calls (recommended):
```bash
PYTHONPATH=src python -m evaluate_matching \
    --dataset ../popoc/data/pairing_sequential.json \
    --max-tested 100 \
    --skip-portion 0.5
```

#### Using API requests (requires running server):
```bash
PYTHONPATH=src python -m evaluate_matching \
    --dataset ../popoc/data/pairing_sequential.json \
    --max-tested 100 \
    --skip-portion 0.5 \
    --use-api
```

#### Evaluation Parameters:
- `--dataset PATH`: Path to the pairing_sequential.json dataset
- `--max-tested N`: Maximum number of documents to test (default: 200)
- `--skip-portion X`: Portion of documents for history building (0.0-1.0, default: 0.5)
- `--use-api`: Use API calls instead of direct function calls
- `--api-url URL`: API endpoint URL (default: http://localhost:8000/)
- `--model-path PATH`: Custom model path (direct calls only)

## API Documentation

API specifications are available in the `docs/` directory:
- API endpoint descriptions
- Sample inputs for different document types
- Match report output format
- Field descriptions and schemas

### Key Endpoints

- `POST /` - Submit documents for matching
- `GET /health` - Service health check

## Configuration

### Environment Variables

- `DISABLE_MODELS=true` - Disable ML model loading (uses dummy logic)
- `DOCPAIR_MODEL_PATH` - Custom path to ML model file
- `PYTHONPATH=src` - Required for running the application
- `MATCH_CONFIDENCE_THRESHOLD` - Confidence threshold for "matched" label (default: 0.5, range: 0.0-1.0)
- `NO_MATCH_CONFIDENCE_THRESHOLD` - Confidence threshold for "no-match" label (default: 0.2, range: 0.0-1.0)

### Whitelisted Sites

The following sites use the real ML pipeline:
- badger-logistics
- falcon-logistics
- christopher-test
- test-site

Other sites will use dummy matching logic.

## Key Components

### Core Services

- **FastAPI App** (`src/app.py`): Main API server with validation and error handling
- **MatchingService** (`src/matching_service.py`): Document processing with lazy initialization
- **DocumentPairingPredictor** (`src/docpairing.py`): ML model wrapper for similarity prediction
- **Match Pipeline** (`src/match_pipeline.py`): Orchestrates the matching process

### Processing Flow

1. Documents arrive via POST to `/` endpoint with candidate documents
2. MatchingService processes using either:
   - Real ML pipeline for whitelisted sites
   - Dummy logic for non-whitelisted sites
3. Results are formatted as v3 match reports with deviations and item pairs

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Code style and standards
- Testing requirements
- Pull request process
- Development workflow

## License

[Add license information here]
