import json
import datetime
import uuid
import decimal
from enum import Enum
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

    def default(self, obj):
        if isinstance(obj, PydanticBaseModel):
            try:
                return obj.model_dump(mode="json")
            except Exception as e:
                print(f"Warning: Failed to dump Pydantic model {type(obj)}: {e}")
                pass  # Fall through to super().default()
        elif isinstance(obj, datetime.datetime):
            if obj.tzinfo:
                return obj.isoformat()
            else:
                # Assume timezone?
                # return obj.replace(tzinfo=datetime.timezone.utc).isoformat()
                return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, decimal.Decimal):
            return str(obj)
        elif isinstance(obj, Enum):
            # Use the enum's value
            return obj.value
        elif isinstance(obj, bytes):
            # Represent bytes as base64 encoded string
            import base64

            return base64.b64encode(obj).decode("ascii")
        elif isinstance(obj, set):
            return list(obj)
        # Let the base class default method raise
        return super().default(obj)
