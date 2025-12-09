from enum import Enum


class DocumentKind(str, Enum):
    """Enumeration of supported document types.

    Attributes:
        INVOICE: Invoice document type
        PURCHASE_ORDER: Purchase order document type
        DELIVERY_RECEIPT: Delivery receipt document type
    """

    INVOICE = "invoice"
    PURCHASE_ORDER = "purchase-order"
    DELIVERY_RECEIPT = "delivery-receipt"


def get_field(element, key):
    """Extract a field value from a document element.

    Supports multiple data structures:
    - List of key-value dictionaries (with 'name' and 'value' fields)
    - Dictionary with 'headers' or 'fields' lists containing key-value pairs
    - Direct dictionary access

    Args:
        element: Document element (dict or list) to extract from
        key: Field name to look up

    Returns:
        Field value if found, None otherwise

    Raises:
        Exception: If element is neither a dict nor a list
    """
    if isinstance(element, list):
        for item in element:
            if isinstance(item, dict):
                if item.get("name") == key:
                    return item.get("value")
        return None

    elif isinstance(element, dict):
        if "headers" in element:
            for header in element.get("headers", []):
                if isinstance(header, dict) and header.get("name") == key:
                    return header.get("value")

        if "fields" in element:
            for field in element.get("fields", []):
                if isinstance(field, dict) and field.get("name") == key:
                    return field.get("value")
        return element.get(key)

    else:
        raise Exception(
            f"Invalid element type: {type(element)}. Expected dict or list."
        )
