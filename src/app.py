import json
import sys

from fastapi import Request, Response, FastAPI

app = FastAPI()
print("✔  Ready to match", file=sys.stderr)


@app.get("/")
async def ready_handler(_request: Request):
    """This endpoint is used by Kubernetes to determine if the container is ready to match"""
    return Response("Ready to match\r\n")

@app.post("/")
async def request_handler(request: Request):
    trace_id = request.headers.get("x-om-trace-id", "<x-om-trace-id missing>")
    indata = await request.json()
    document = indata["document"]

    print(
        json.dumps(
            {
                "traceId": trace_id,
                "level": "info",
                "site": document.get("site", "<site missing>"),
                "documentId": document.get("id", "<id missing>"),
                "stage": document.get("stage", "<stage missing>"),
                "kind": document.get("kind", "<kind missing>"),
                "statusCode": 200,
                "message": "Success",
            }
        ),
        file=sys.stderr,
    )

    return get_matching_report(document)

def get_matching_report(document):
    document_id = document.get("id", "<id missing>")
    if hash(document_id) % 2 == 0:
        return _no_match_report(document)
    else:
        return _match_report(document)

def _no_match_report(document):
    return {
        "version": "v3",
        "id": document["id"],
        "kind": "match-report",
        "site": document["site"],
        "stage": "output",
        "headers": [],
        "documents": [
            {
                "kind": "invoice",
                "id": document["id"]
            }
        ],
        "labels": [
            "no-match"
        ],
        "metrics": [
            {"name": "certainty", "value": 0.95733},
            {"name": "deviation-severity", "value": "no-severity"},
            {"name": "invoice-has-future-match-certainty", "value": 0.88}
        ],
        "deviations": [],
        "itempairs": []
    }

def _match_report(document):
    return {
        "version": "v3",
        "id": document["id"],
        "kind": "match-report",
        "site": document["site"],
        "stage": "output",
        "headers": [],
        "documents": [
            {"kind": document["kind"], "id": document["id"]},
            {"kind": "purchase-order" if document["kind"] == "invoice" else "invoice", "id": "b5a3c7d2-8f91-4e2a-9d78-6a3b4f92d318"}
        ],
        "labels": [
            "match"
        ],
        "metrics": [
            {"name": "certainty", "value": 0.93151},
            {"name": "deviation-severity", "value": "high"},
            {"name": "invoice-has-future-match-certainty", "value": 0.98},
            {"name": "purchase-order-has-future-match-certainty", "value": 0.99}
        ],
        "deviations": [
            {
                "code": "amounts-differ",
                "severity": "high",
                "message": "Incl VAT amount differs by 42.75",
                "field_names": ["headers.incVatAmount", "headers.inc_vat_amount"],
                "values": ["1950.25", "1993.00"]
            }
        ],
        "itempairs": [
            {
                "item_indices": [2, 3],
                "match_type": "matched",
                "deviation_severity": "medium",
                "item_unchanged_certainty": 0.88,
                "deviations": [
                    {
                        "field_names": ["fields.quantityToInvoice", "fields.quantity"],
                        "values": [9, 11],
                        "severity": "medium",
                        "message": "Quantity differs by 2",
                        "code": "quantity-too-many"
                    }
                ]
            }
        ]
    }