from enum import Enum
from typing import Any, Optional, Union


class DocumentKind(str, Enum):
    INVOICE = "invoice"
    PURCHASE_ORDER = "purchase-order"
    DELIVERY_RECEIPT = "delivery-receipt"


def get_field(element: Union[list, dict], key: str) -> Optional[Any]:
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
