import datetime
import decimal
import json
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel as PydanticBaseModel


class UniversalJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder that should handle all common types
    behind the scenes.

    Handles:
    - datetime.datetime
    - datetime.date
    - uuid.UUID
    - decimal.Decimal
    - enum.Enum
    - bytes
    - Pydantic V2 BaseModels
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, PydanticBaseModel):
            try:
                return o.model_dump(mode="json")
            except Exception as e:
                print(f"Warning: Failed to dump Pydantic model {type(o)}: {e}")
                pass  # Fall through to super().default()
        elif isinstance(o, datetime.datetime):
            if o.tzinfo:
                return o.isoformat()
            else:
                # Assume timezone?
                # return o.replace(tzinfo=datetime.timezone.utc).isoformat()
                return o.isoformat()
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, uuid.UUID):
            return str(o)
        elif isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, Enum):
            # Use the enum's value
            return o.value
        elif isinstance(o, bytes):
            # Represent bytes as base64 encoded string
            import base64

            return base64.b64encode(o).decode("ascii")
        elif isinstance(o, set):
            return list(o)
        # Let the base class default method raise
        return super().default(o)
