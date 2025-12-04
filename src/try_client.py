import argparse
import json
import sys
import uuid

import requests

# Script that sends an API requests to the matching service


DEFAULT_URL = "http://localhost:8000/"
TEST_SITE = "badger-logistics"


SAMPLE_INPUT_DOCUMENT = {
    "id": f"client-test-doc-{uuid.uuid4()}",
    "kind": "invoice",
    "site": TEST_SITE,  # Has to be a whitelisted site
    "stage": "input",
    "headers": [
        {"name": "supplierId", "value": "supplier-abc"},
        {"name": "incVatAmount", "value": "121.00"},
        {"name": "excVatAmount", "value": "100.00"},
        {"name": "orderReference", "value": "PO-CLIENT-1"},
        {"name": "currency", "value": "SEK"},
    ],
    "items": [
        {
            "fields": [
                {"name": "lineNumber", "value": "1"},
                {"name": "text", "value": "Test Item Alpha"},
                {"name": "debit", "value": "50.00"},
                {"name": "quantity", "value": "1"},
                {"name": "item-id", "value": "ITEM-A"},
                {"name": "purchaseReceiptDataUnitAmount", "value": "50.00"},
                {"name": "purchaseReceiptDataQuantity", "value": "1"},
                {"name": "purchaseReceiptDatainventory", "value": "ITEM-A"},
            ]
        },
        {
            "fields": [
                {"name": "lineNumber", "value": "2"},
                {"name": "text", "value": "Test Item Beta"},
                {"name": "debit", "value": "50.00"},
                {"name": "quantity", "value": "1"},
                {"name": "item-id", "value": "ITEM-B"},
                {"name": "purchaseReceiptDataUnitAmount", "value": "50.00"},
                {"name": "purchaseReceiptDataQuantity", "value": "1"},
                {"name": "purchaseReceiptDatainventory", "value": "ITEM-B"},
            ]
        },
    ],
}

SAMPLE_CANDIDATE_DOCUMENTS = [
    {
        "id": "client-candidate-po-1",
        "kind": "purchase-order",
        "site": TEST_SITE,
        "stage": "historical",
        "headers": [
            {"name": "supplierId", "value": "supplier-abc"},
            {"name": "incVatAmount", "value": "121.00"},  # Matches exactly
            {"name": "excVatAmount", "value": "100.00"},
            {"name": "orderNumber", "value": "PO-CLIENT-1"},  # Matches reference
            {"name": "currency", "value": "SEK"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "lineNumber", "value": "1"},
                    {
                        "name": "description",
                        "value": "Test Item Alpha PO",
                    },  # Slightly different desc
                    {"name": "unitAmount", "value": "50.00"},
                    {"name": "quantityToInvoice", "value": "1"},
                    {"name": "inventory", "value": "ITEM-A"},  # Matches item ID
                ]
            },
            {
                "fields": [
                    {"name": "lineNumber", "value": "2"},
                    {"name": "description", "value": "Test Item Beta PO"},
                    {"name": "unitAmount", "value": "50.00"},
                    {"name": "quantityToInvoice", "value": "1"},
                    {"name": "inventory", "value": "ITEM-B"},
                ]
            },
        ],
    },
    {
        "id": "client-candidate-po-2-nomatch",
        "kind": "purchase-order",
        "site": TEST_SITE,
        "stage": "historical",
        "headers": [
            {"name": "supplierId", "value": "supplier-xyz"},  # Different supplier
            {"name": "incVatAmount", "value": "999.00"},
            {"name": "excVatAmount", "value": "800.00"},
            {"name": "orderNumber", "value": "PO-CLIENT-UNRELATED"},
            {"name": "currency", "value": "SEK"},
        ],
        "items": [],
    },
]


# @TODO rename
def send_request(url: str, payload: dict):
    """Sends a POST request to the specified URL with the JSON payload."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    print(f"--- Sending POST request to: {url} ---")
    # print(f"Payload:\n{json.dumps(payload, indent=2)}")
    print("-" * 30)

    try:
        response = requests.post(
            url, headers=headers, json=payload, timeout=60
        )  # Add timeout

        print("--- Response ---")
        print(f"Status Code: {response.status_code}")

        if response.ok:
            try:
                response_data = response.json()
                print("Response JSON Body:")
                print(
                    json.dumps(response_data, indent=2, default=str)
                )  # Use default=str for non-serializable types like Decimal
            except json.JSONDecodeError:
                print("Response Body (Non-JSON):")
                print(response.text)
        else:
            print("Error Response Body:")
            print(response.text)

    except requests.exceptions.ConnectionError as e:
        print(f"\nError: Could not connect to the server at {url}.", file=sys.stderr)
        print("Ensure the matching service ('serving.py') is running.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
    except requests.exceptions.Timeout:
        print("\nError: Request timed out after 60 seconds.", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"\nError during request: {e}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Send a test request to the matching service."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"URL of the matching service endpoint (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--input-doc-file", help="Path to a JSON file containing the 'document' object."
    )
    parser.add_argument(
        "--candidates-file",
        help="Path to a JSON file containing the 'candidate_documents' list.",
    )
    parser.add_argument(
        "--add-candidate-file",
        help="Path to a JSON file containing a document to be added to 'candidate_documents'.",
    )
    parser.add_argument(
        "--site",
        default=TEST_SITE,
        help=f"Override the site in the sample document (default: {TEST_SITE}). Use a non-whitelisted site to test dummy logic.",
    )

    args = parser.parse_args()

    payload = {}
    if args.input_doc_file:
        try:
            with open(args.input_doc_file, "r") as f:
                payload["document"] = json.load(f)
        except Exception as e:
            print(
                f"Error loading input document file '{args.input_doc_file}': {e}",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        payload["document"] = SAMPLE_INPUT_DOCUMENT
        # Replace site if specified
        payload["document"]["site"] = args.site
        print(f"Using sample input document with site: {args.site}")

    if args.candidates_file:
        try:
            with open(args.candidates_file, "r") as f:
                payload["candidate_documents"] = json.load(f)
        except Exception as e:
            print(
                f"Error loading candidates file '{args.candidates_file}': {e}",
                file=sys.stderr,
            )
            sys.exit(1)
    if args.add_candidate_file:
        try:
            with open(args.add_candidate_file, "r") as f:
                candidate_doc = json.load(f)
                if "candidate_documents" not in payload:
                    payload["candidate_documents"] = []
                payload["candidate_documents"].append(candidate_doc)
                print("Added candidate document from file.")
        except Exception as e:
            print(
                f"Error loading add candidate file '{args.add_candidate_file}': {e}",
                file=sys.stderr,
            )
            sys.exit(1)
    if not args.candidates_file and not args.add_candidate_file:
        payload["candidate_documents"] = SAMPLE_CANDIDATE_DOCUMENTS
        print("Using sample candidate documents.")

    print(f"Sending {len(payload.get('candidate_documents', []))} candidate documents.")
    target_url = args.url.rstrip("/") + "/"

    send_request(target_url, payload)
