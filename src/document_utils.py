from enum import StrEnum


class DocumentKind(StrEnum):
    INVOICE = "invoice"
    PURCHASE_ORDER = "purchase-order"
    DELIVERY_RECEIPT = "delivery-receipt"


def get_field(element, key):
    if not isinstance(element, dict):
        return None
    # Check headers first
    if "headers" in element:
        for header in element.get("headers", []):
            if isinstance(header, dict) and header.get("name") == key:
                return header.get("value")
    # Then check item fields if present
    if "fields" in element:
        for field in element.get("fields", []):
            if isinstance(field, dict) and field.get("name") == key:
                return field.get("value")
    # Finally, check root level keys
    return element.get(key)
