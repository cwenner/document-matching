# itempair_deviations.py

from decimal import Decimal
from enum import StrEnum
from typing import Any, Type
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

AMOUNT_DEVIATION_MEDIUM_SEVERITY_MIN_ABS_DIFF: float = 1.0
AMOUNT_DEVIATION_MEDIUM_SEVERITY_MIN_REL_DIFF: float = 0.001
AMOUNT_DEVIATION_MEDIUM_SEVERITY_MAX_ABS_DIFF: float = 1000.0
AMOUNT_DEVIATION_MEDIUM_SEVERITY_MAX_REL_DIFF: float = 0.10


class DocumentKind(StrEnum):
    INVOICE = "invoice"
    PURCHASE_ORDER = "purchase-order"
    DELIVERY_RECEIPT = "delivery-receipt"


class DeviationSeverity(StrEnum):
    NO_SEVERITY = "no-severity"
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    # @TODO can we simplify this?
    def _rank(self):
        _ORDER = ["no-severity", "info", "low", "medium", "high"]
        try:
            return _ORDER.index(self.value)
        except ValueError:
            logger.warning(f"Invalid DeviationSeverity value encountered: {self.value}")
            return -1

    def __lt__(self, other):
        if not isinstance(other, DeviationSeverity):
            return NotImplemented
        return self._rank() < other._rank()

    def __le__(self, other):
        if not isinstance(other, DeviationSeverity):
            return NotImplemented
        return self._rank() <= other._rank()

    def __gt__(self, other):
        if not isinstance(other, DeviationSeverity):
            return NotImplemented
        return self._rank() > other._rank()

    def __ge__(self, other):
        if not isinstance(other, DeviationSeverity):
            return NotImplemented
        return self._rank() >= other._rank()


class FieldComparison(BaseModel):
    code: str = ""
    message: str = ""
    severity: DeviationSeverity = DeviationSeverity.NO_SEVERITY
    is_header_field: bool = False
    is_item_field: bool = False
    field_names: dict[DocumentKind, str | None] = Field(default_factory=dict)
    field_encoded_type: Type = str


class FieldDeviation(BaseModel):
    code: str = ""
    message: str = ""
    severity: DeviationSeverity = DeviationSeverity.NO_SEVERITY
    field_names: list[str | None] = []
    field_values: list[Any] = []


def get_differing_amounts_severity(
    amount1: Decimal | float, amount2: Decimal | float
) -> DeviationSeverity | None:
    try:
        d_amount1 = Decimal(str(amount1))
        d_amount2 = Decimal(str(amount2))
    except Exception:
        logger.warning(
            f"Could not convert amounts '{amount1}', '{amount2}' to Decimal for comparison."
        )
        return DeviationSeverity.LOW

    if d_amount1 == d_amount2:
        return None

    abs_diff = abs(d_amount1 - d_amount2)
    sum_abs = abs(d_amount1) + abs(d_amount2)
    rel_diff = (2 * abs_diff / sum_abs) if sum_abs != Decimal(0) else Decimal(0)

    min_abs_med = Decimal(str(AMOUNT_DEVIATION_MEDIUM_SEVERITY_MIN_ABS_DIFF))
    min_rel_med = Decimal(str(AMOUNT_DEVIATION_MEDIUM_SEVERITY_MIN_REL_DIFF))
    max_abs_med = Decimal(str(AMOUNT_DEVIATION_MEDIUM_SEVERITY_MAX_ABS_DIFF))
    max_rel_med = Decimal(str(AMOUNT_DEVIATION_MEDIUM_SEVERITY_MAX_REL_DIFF))

    if abs_diff < min_abs_med and rel_diff < min_rel_med:
        return DeviationSeverity.LOW
    if abs_diff > max_abs_med or rel_diff > max_rel_med:
        return DeviationSeverity.HIGH
    return DeviationSeverity.MEDIUM


FIELD_COMPARISONS = []

FIELD_COMPARISONS.append(
    FieldComparison(
        code="amount-differs",
        message="Amounts differ",
        severity=DeviationSeverity.MEDIUM,
        is_item_field=True,
        field_names={
            DocumentKind.INVOICE: "debit",
            DocumentKind.PURCHASE_ORDER: "!quantityToInvoice*unitAmount",
            DocumentKind.DELIVERY_RECEIPT: "amount",
        },
        field_encoded_type=Decimal,
    )
)

FIELD_COMPARISONS.append(
    FieldComparison(
        code="description-differs",
        message="Descriptions differ",
        severity=DeviationSeverity.INFO,
        is_item_field=True,
        field_names={
            DocumentKind.INVOICE: "text",
            DocumentKind.PURCHASE_ORDER: "description",
            DocumentKind.DELIVERY_RECEIPT: "inventoryDescription",
        },
        field_encoded_type=str,
    )
)

# @TODO add thresholds for unit amounts if desired (currently uses MEDium default)
FIELD_COMPARISONS.append(
    FieldComparison(
        code="unit-amount-differs",
        message="Unit amounts differ",
        severity=DeviationSeverity.MEDIUM,
        is_item_field=True,
        field_names={
            # @TODO Confirm correct Invoice unit price field. Using 'debit' might be incorrect if it's total.
            DocumentKind.INVOICE: "debit",
            DocumentKind.PURCHASE_ORDER: "unitAmount",
            DocumentKind.DELIVERY_RECEIPT: "unitAmount",
        },
        field_encoded_type=Decimal,
    )
)

FIELD_COMPARISONS.append(
    FieldComparison(
        code="quantity-differs",
        message="Quantities differ",
        severity=DeviationSeverity.MEDIUM,
        is_item_field=True,
        field_names={
            # @TODO Confirm correct Invoice quantity field.
            DocumentKind.INVOICE: "purchaseReceiptDataQuantity",
            DocumentKind.PURCHASE_ORDER: "quantityToInvoice",
            DocumentKind.DELIVERY_RECEIPT: "quantity",
        },
        field_encoded_type=Decimal,
    )
)


def getkv_value(kvs: list[dict] | None, name: str) -> Any | None:
    if not isinstance(kvs, list):
        return None
    for kv in kvs:
        if isinstance(kv, dict) and kv.get("name") == name:
            return kv.get("value")
    return None


def check_itempair_comparison(
    comparison: FieldComparison,
    document_kinds: list[DocumentKind],
    document_item_fields: list[list[dict] | None],
) -> FieldDeviation | None:
    values = []
    field_names_used = []

    for i, document_kind in enumerate(document_kinds):
        item_fields = document_item_fields[i] if i < len(document_item_fields) else None
        field_name_config = comparison.field_names.get(document_kind)
        field_names_used.append(field_name_config)

        if not field_name_config or item_fields is None:
            values.append(None)
            continue

        value = None
        try:
            if field_name_config == "!quantityToInvoice*unitAmount":
                if document_kind != DocumentKind.PURCHASE_ORDER:
                    logger.warning(
                        f"Attempted PO amount calculation '{field_name_config}' on non-PO doc type: {document_kind}"
                    )
                    values.append(None)
                    continue

                quant_val = getkv_value(item_fields, "quantityToInvoice")
                unit_price_val = getkv_value(item_fields, "unitAmount")

                if quant_val is not None and unit_price_val is not None:
                    quant = Decimal(str(quant_val))
                    unit_price = Decimal(str(unit_price_val))
                    value = quant * unit_price
                else:
                    logger.debug(
                        f"Missing quantity ('{quant_val}') or unit price ('{unit_price_val}') for amount calculation in {document_kind}."
                    )
                    value = None
            else:
                raw_value = getkv_value(item_fields, field_name_config)
                if raw_value is not None:
                    value = comparison.field_encoded_type(raw_value)

        except Exception as e:
            logger.error(
                f"Failed to process/convert value for {document_kind} field '{field_name_config}' (Raw: '{raw_value}'): {e}",
                exc_info=False,
            )
            value = None

        values.append(value)

    non_empty_values = [value for value in values if value is not None]

    if len(non_empty_values) < 2:
        return None

    max_severity = DeviationSeverity.NO_SEVERITY
    deviation_occurred = False
    final_message = comparison.message

    for i, value1 in enumerate(non_empty_values):
        for value2 in non_empty_values[:i]:
            current_severity = DeviationSeverity.NO_SEVERITY
            if (
                comparison.code == "amount-differs"
                or comparison.code == "unit-amount-differs"
            ):
                severity_calc = get_differing_amounts_severity(value1, value2)
                if severity_calc is not None:
                    current_severity = severity_calc
                    diff = abs(Decimal(str(value1)) - Decimal(str(value2)))
                    final_message = (
                        f"{comparison.message} ({value1} vs {value2}, diff: {diff:.2f})"
                    )
                    deviation_occurred = True
            elif value1 != value2:
                current_severity = comparison.severity
                final_message = f"{comparison.message} ({value1} vs {value2})"
                deviation_occurred = True

            if current_severity > max_severity:
                max_severity = current_severity

    if deviation_occurred and max_severity > DeviationSeverity.NO_SEVERITY:
        serializable_values = [str(v) if isinstance(v, Decimal) else v for v in values]
        return FieldDeviation(
            code=comparison.code,
            message=final_message,
            severity=max_severity,
            field_names=field_names_used,
            field_values=serializable_values,
        )
    return None


def collect_itempair_deviations(
    document_kinds: list[DocumentKind],
    document_item_fields: list[list[dict] | None],
) -> list[FieldDeviation]:
    deviations = []
    if len(document_kinds) != len(document_item_fields):
        logger.error(
            "Mismatch between number of document kinds and item fields provided."
        )
        return deviations

    for comparison in FIELD_COMPARISONS:
        if comparison.is_item_field:
            deviation = check_itempair_comparison(
                comparison, document_kinds, document_item_fields
            )
            if deviation:
                deviations.append(deviation)
    return deviations


if __name__ == "__main__":
    import json

    results = collect_itempair_deviations(
        [
            DocumentKind.INVOICE,
            DocumentKind.PURCHASE_ORDER,
            DocumentKind.DELIVERY_RECEIPT,
        ],
        [
            [
                {"name": "debit", "value": "109.00"},
                {"name": "text", "value": "Brandslang"},
                {"name": "purchaseReceiptDataQuantity", "value": "1"},
            ],
            [
                {"name": "quantityToInvoice", "value": "1"},
                {"name": "unitAmount", "value": "109.00"},
                {"name": "description", "value": "Brandslang Titan"},
            ],
            [
                {"name": "amount", "value": "109.00"},
                {"name": "inventoryDescription", "value": "Brandslang 63mm"},
                {"name": "unitAmount", "value": "109.00"},
                {"name": "quantity", "value": "1"},
            ],
        ],
    )
    print(json.dumps([r.dict() for r in results], indent=2, default=str))

    print("-" * 20)
    results_2docs = collect_itempair_deviations(
        [DocumentKind.PURCHASE_ORDER, DocumentKind.INVOICE],
        [
            [
                {"name": "quantityToInvoice", "value": "5"},
                {"name": "unitAmount", "value": "20.00"},
                {"name": "description", "value": "Blue Widget"},
            ],
            [
                {"name": "debit", "value": "110.00"},
                {"name": "text", "value": "Blue Widget Special"},
                {"name": "purchaseReceiptDataQuantity", "value": "5"},
            ],
        ],
    )
    print(json.dumps([r.dict() for r in results_2docs], indent=2, default=str))
