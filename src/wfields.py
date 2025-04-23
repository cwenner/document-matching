import base64
import json
import logging

from document_utils import get_field, DocumentKind

# @TODO Move customer specific field naming here


logger = logging.getLogger(__name__)


def unpack_attachments(doc):
    if doc.get("attachments"):
        for attachment in doc["attachments"]:
            if attachment["name"].endswith(".pdf"):
                pass
            elif attachment["name"] == "interpreted_data.json":
                if "interpreted_data" not in doc:
                    try:
                        doc["interpreted_data"] = json.loads(
                            base64.b64decode(
                                attachment["value"],
                            ).decode("utf-8")
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to decode interpreted_data.json: {e}",
                            exc_info=False,
                        )
            elif attachment["name"] == "interpreted_xml.json":
                if "interpreted_xml" not in doc:
                    try:
                        doc["interpreted_xml"] = json.loads(
                            base64.b64decode(
                                attachment["value"],
                            ).decode("utf-8")
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to decode interpreted_xml.json: {e}",
                            exc_info=False,
                        )


def get_supplier_ids(doc):
    supplier_ids = []
    for n in [
        "supplierId",
        "supplierExternalId",
        "supplierInternalId",
        "supplierIncomingId",
    ]:
        h = get_field(doc, n)
        if h:
            supplier_ids.append(h)
    # @TODO interpreted_xml as well?
    if doc.get("interpreted_data"):
        h = doc.get("interpreted_data").get("supplierId")
        if h:
            supplier_ids.append(h)
    return supplier_ids


def get_item_description(item) -> str:
    return (
        get_field(item, "inventoryDescription")
        or get_field(item, "description")
        or get_field(item, "text")
    )


def get_item_article_number(item) -> str:
    return get_field(item, "inventoryNumber") or get_field(item, "inventory")


def extract_item_data(item, document_kind, item_index):
    item_data = {
        "number": None,
        "description": None,
        "tax-percent": None,
        "unit-price": None,
        "quantity": None,
        "currency": None,
        "item-id": None,
        "item_index": item_index,
        "raw_item": item,  # Keep the original item structure
        "document_kind": document_kind,
    }

    def _safe_float(value):
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    def _safe_int(value):
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    def _clean_desc(value):
        return (
            value.replace("\n", " ") if isinstance(value, str) else ""
        )  # Replace newline with space for consistency

    # Use get_field consistently to handle 'fields' list or direct keys
    if document_kind == DocumentKind.PURCHASE_ORDER:
        item_data["number"] = _safe_int(get_field(item, "lineNumber"))
        item_data["description"] = _clean_desc(get_item_description(item))
        item_data["unit-price"] = _safe_float(get_field(item, "unitAmount"))
        item_data["quantity"] = _safe_float(get_field(item, "quantityToInvoice"))
        item_data["item-id"] = get_field(item, "inventory")
        item_data["unit-of-measure"] = get_field(item, "uom")
        item_data["vat-code"] = get_field(item, "vatCode")
        item_data["vat-code-id"] = get_field(item, "vatCodeId")
    elif document_kind == DocumentKind.INVOICE:
        item_data["number"] = _safe_int(get_field(item, "lineNumber"))
        item_data["description"] = _clean_desc(get_item_description(item))
        # @TODO We need to extract these from original data
        unit_price = (
            # @TODO This is only available in final
            get_field(item, "purchaseReceiptDataUnitAmount")
            # @TODO This is no longer available
            or get_field(item, "unit-price")
        )
        item_data["unit-price"] = _safe_float(unit_price)
        # We may need to make these adjustments consistently
        item_data["unit-price-adjusted"] = item_data["unit-price"]
        item_data["quantity"] = _safe_float(
            get_field(item, "purchaseReceiptDataQuantity")
            # @TODO we need to pull this from original data
            or get_field(item, "quantity")
        )
        item_data["item-id"] = (
            get_field(item, "purchaseReceiptDatainventory")
            # @TODO we need to pull this from original data
            or get_field(item, "inventory")
        )
    elif document_kind == DocumentKind.DELIVERY_RECEIPT:
        item_data["number"] = _safe_int(get_field(item, "lineNumber"))
        item_data["description"] = _clean_desc(get_item_description(item))
        item_data["unit-price"] = _safe_float(get_field(item, "unitAmount"))
        item_data["quantity"] = _safe_float(get_field(item, "quantity"))
        item_data["unit-of-measure"] = get_field(item, "uom")
        item_data["item-id"] = get_item_article_number(item)
    else:
        logger.warning(
            f"Unknown document kind '{document_kind}' encountered during item extraction."
        )
        return None  # Return None for unknown types

    return item_data


def get_document_items(doc):
    if not isinstance(doc, dict):
        logger.warning(
            "Invalid document format passed to get_document_items: expected dict."
        )
        return []
    try:
        # Use get_field to check header or root level for 'kind'
        kind_str = get_field(doc, "kind")
        if not kind_str:
            raise ValueError("Document kind is missing or not found.")
        doc_kind = DocumentKind(kind_str)
    except ValueError as e:
        logger.warning(
            f"Invalid or missing document kind in document ID {doc.get('id')}: {e}"
        )
        return []

    # Use get_field to check header or root level for 'items'
    items = get_field(doc, "items")
    if items is None:
        items = doc.get("items", [])  # Fallback to root if not in headers/fields
    if not isinstance(items, list):
        logger.warning(
            f"Document items format is not a list for doc ID {doc.get('id')}."
        )
        return []

    extracted_items = []
    for i, item in enumerate(items):
        # Ensure item is a dict before processing
        if isinstance(item, dict):
            item_data = extract_item_data(item, doc_kind, i)
            if item_data:  # Only append if extraction was successful
                extracted_items.append(item_data)
        else:
            logger.warning(
                f"Skipping non-dict item at index {i} in document ID {doc.get('id')}"
            )
    return extracted_items


if __name__ == "__main__":
    # Configure basic logging if running standalone
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    print("--- Testing document_utils ---")

    # --- Test Data ---
    sample_po = {
        "id": "po-1",
        "kind": "purchase-order",
        "site": "SiteA",
        "headers": [
            {"name": "orderNumber", "value": "PO123"},
            {"name": "currency", "value": "SEK"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "lineNumber", "value": "1"},
                    {"name": "description", "value": "Widget A"},
                    {"name": "unitAmount", "value": "10.50"},
                    {"name": "quantityToInvoice", "value": "5"},
                    {"name": "inventory", "value": "WID-A"},
                ]
            },
            {
                "description": "Service B",
                "unitAmount": "100",
                "quantityToInvoice": "1",
            },  # Item without fields structure
        ],
    }
    sample_invoice = {
        "id": "inv-1",
        "kind": "invoice",
        "site": "SiteA",
        "headers": [
            {"name": "invoiceNumber", "value": "INV123"},
            {"name": "currency", "value": "SEK"},
            {"name": "incVatAmount", "value": "75.63"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "lineNumber", "value": "1"},
                    {"name": "text", "value": "Widget A \n Delivered"},
                    {"name": "debit", "value": "52.50"},
                    {"name": "quantity", "value": "5"},
                    {"name": "item-id", "value": "WID-A"},
                ],
                "purchaseReceiptDataUnitAmount": "10.50",
            },
            {"text": "Service B Charge", "debit": "100", "quantity": "1"},
        ],
    }
    sample_delivery = {
        "id": "del-1",
        "kind": "delivery-receipt",
        "site": "SiteA",
        "headers": [{"name": "deliveryNumber", "value": "DEL123"}],
        "items": [
            {
                "fields": [
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventoryDescription", "value": "Widget A"},
                    {"name": "unitAmount", "value": "10.50"},
                    {"name": "quantity", "value": "5"},
                    {"name": "inventory", "value": "WID-A"},
                ]
            }
        ],
    }
    invalid_doc = {"id": "bad-doc"}
    doc_with_non_list_items = {
        "id": "bad-items",
        "kind": "invoice",
        "items": "not a list",
    }

    # --- Test get_field ---
    print("\nTesting get_field:")
    print(f"  PO Order Number (Header): {get_field(sample_po, 'orderNumber')}")
    print(
        f"  PO Item 1 Description (Field): {get_field(sample_po['items'][0], 'description')}"
    )
    print(
        f"  PO Item 2 Description (Root): {get_field(sample_po['items'][1], 'description')}"
    )
    print(
        f"  Invoice Total Amount (Header): {get_field(sample_invoice, 'incVatAmount')}"
    )
    print(
        f"  Invoice Item 1 Text (Field): {get_field(sample_invoice['items'][0], 'text')}"
    )
    print(f"  Non-existent field: {get_field(sample_po, 'nonExistent')}")

    # --- Test get_document_items ---
    print("\nTesting get_document_items:")
    po_items = get_document_items(sample_po)
    print(f"  Extracted PO Items ({len(po_items)}):")
    print(json.dumps(po_items, indent=2, default=str))

    invoice_items = get_document_items(sample_invoice)
    print(f"\n  Extracted Invoice Items ({len(invoice_items)}):")
    print(json.dumps(invoice_items, indent=2, default=str))

    delivery_items = get_document_items(sample_delivery)
    print(f"\n  Extracted Delivery Items ({len(delivery_items)}):")
    print(json.dumps(delivery_items, indent=2, default=str))

    invalid_items = get_document_items(invalid_doc)
    print(f"\n  Extracted Invalid Doc Items ({len(invalid_items)}): {invalid_items}")

    bad_format_items = get_document_items(doc_with_non_list_items)
    print(
        f"\n  Extracted Bad Format Doc Items ({len(bad_format_items)}): {bad_format_items}"
    )

    print("\n--- document_utils tests finished ---")
