# Document-Matcher

Responsible for producing matching reports given documents and candidates to match against.

## Serving test

Start server:

```
source .venv/bin/activate
PYTHONPATH=src uvicorn app:app
```

Send a document at it:

```
source .venv/bin/activate
PYTHONPATH=src python -m try_client
```

## Evaluation

The evaluate_matching.py script can run document matching evaluation either by:
1. Direct function calls (default, faster) - doesn't require running a server
2. API requests to a running server

### Using direct function calls (recommended)

```
source .venv/bin/activate
PYTHONPATH=src python -m evaluate_matching --dataset ../popoc/data/pairing_sequential.json --max-tested 100 --skip-portion 0.5
```

### Using API requests (requires running server)

```
source .venv/bin/activate
PYTHONPATH=src python -m evaluate_matching --dataset ../popoc/data/pairing_sequential.json --max-tested 100 --skip-portion 0.5 --use-api
```

### Parameters

- `--dataset PATH`: Path to the pairing_sequential.json dataset file
- `--max-tested N`: Maximum number of documents to test (default: 200)
- `--skip-portion X`: Portion of documents to use for building history without testing (0.0-1.0) (default: 0.5)
- `--use-api`: Use API calls instead of direct function calls
- `--api-url URL`: URL of the matching service endpoint (default: http://localhost:8000/)
- `--model-path PATH`: Path to the document pairing model file (only used with direct calls)

### Evaluation Process

The evaluation script:
1. Loads documents from the dataset
2. Processes documents sequentially to mimic real-world document flow
3. Uses the first portion of documents (as per --skip-portion) to build history without testing
4. Tests the next batch of documents (up to --max-tested)
5. For each test document:
   - Gets matching candidates from history based on overlapping supplier IDs
   - Makes predictions using the matching pipeline
   - Evaluates predictions against expected matches
6. Calculates precision and recall metrics for the entire test set

## Testing

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests and linting
nox

# Run just tests
nox -s test

# Run just linting
nox -s lint
```
