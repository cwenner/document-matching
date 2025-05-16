# Document-Matcher

Responsible for producing matching reports given a documents and candidates to match against.

## Serving test

Start server:

```
source .venv/bin/activate
PYTHONPATH=src uvicorn app:app
```

Send a document at it :

```
source .venv/bin/activate
python src/try_client.py
```

