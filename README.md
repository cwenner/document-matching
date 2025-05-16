# Document-Matcher

Responsible for producing matching reports given a documents and candidates to match against.

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

Run against an evaluation set:
```
PYTHONPATH=src python -m evaluate_matching --dataset ../popoc/data/pairing_structured.json --max-tested 100 --skip-portion 0.5
```
