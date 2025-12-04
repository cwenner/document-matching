# itempair_deviations.py

import logging
from decimal import Decimal
from enum import StrEnum
from typing import Any, Type

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Legacy constants - kept for reference but no longer used
# AMOUNT_DEVIATION_MEDIUM_SEVERITY_MIN_ABS_DIFF: float = 1.0
# AMOUNT_DEVIATION_MEDIUM_SEVERITY_MIN_REL_DIFF: float = 0.001
# AMOUNT_DEVIATION_MEDIUM_SEVERITY_MAX_ABS_DIFF: float = 1000.0
# AMOUNT_DEVIATION_MEDIUM_SEVERITY_MAX_REL_DIFF: float = 0.10


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


def _calculate_diff_metrics(
    amount1: Decimal | float, amount2: Decimal | float
) -> tuple[Decimal, Decimal, Decimal, Decimal] | None:
    """Calculate absolute and relative difference metrics."""
    try:
        d_amount1 = Decimal(str(amount1))
        d_amount2 = Decimal(str(amount2))
    except Exception:
        logger.warning(
            f"Could not convert amounts '{amount1}', '{amount2}' to Decimal for comparison."
        )
        return None

    if d_amount1 == d_amount2:
        return None

    abs_diff = abs(d_amount1 - d_amount2)
    sum_abs = abs(d_amount1) + abs(d_amount2)
    rel_diff = (2 * abs_diff / sum_abs) if sum_abs != Decimal(0) else Decimal(0)

    return d_amount1, d_amount2, abs_diff, rel_diff


def get_header_amount_severity(
    amount1: Decimal | float, amount2: Decimal | float
) -> DeviationSeverity | None:
    """
    Severity for header-level total amount differences.

    Thresholds (spec):
    - no-severity: abs <= 0.01 AND rel <= 0.001
    - low: abs <= 1 AND rel <= 0.01
    - medium: abs <= 50 AND rel <= 0.05
    - high: otherwise
    """
    metrics = _calculate_diff_metrics(amount1, amount2)
    if metrics is None:
        return None

    _, _, abs_diff, rel_diff = metrics

    # no-severity: abs <= 0.01 AND rel <= 0.001
    if abs_diff <= Decimal("0.01") and rel_diff <= Decimal("0.001"):
        return DeviationSeverity.NO_SEVERITY

    # low: abs <= 1 AND rel <= 0.01
    if abs_diff <= Decimal("1") and rel_diff <= Decimal("0.01"):
        return DeviationSeverity.LOW

    # medium: abs <= 50 AND rel <= 0.05
    if abs_diff <= Decimal("50") and rel_diff <= Decimal("0.05"):
        return DeviationSeverity.MEDIUM

    return DeviationSeverity.HIGH


def get_line_amount_severity(
    amount1: Decimal | float, amount2: Decimal | float
) -> DeviationSeverity | None:
    """
    Severity for line-level item amount differences.

    Thresholds (spec):
    - no-severity: abs <= 0.01
    - low: abs <= 1 OR rel <= 0.01
    - medium: abs <= 10 OR rel <= 0.10
    - high: otherwise
    """
    metrics = _calculate_diff_metrics(amount1, amount2)
    if metrics is None:
        return None

    _, _, abs_diff, rel_diff = metrics

    # no-severity: abs <= 0.01
    if abs_diff <= Decimal("0.01"):
        return DeviationSeverity.NO_SEVERITY

    # low: abs <= 1 OR rel <= 0.01
    if abs_diff <= Decimal("1") or rel_diff <= Decimal("0.01"):
        return DeviationSeverity.LOW

    # medium: abs <= 10 OR rel <= 0.10
    if abs_diff <= Decimal("10") or rel_diff <= Decimal("0.10"):
        return DeviationSeverity.MEDIUM

    return DeviationSeverity.HIGH


def get_unit_price_severity(
    price1: Decimal | float, price2: Decimal | float
) -> DeviationSeverity | None:
    """
    Severity for unit price differences.
    More sensitive than line totals - uses relative difference primarily.

    Thresholds (spec):
    - no-severity: abs <= 0.005 OR rel <= 0.005
    - low: rel <= 0.05
    - medium: rel <= 0.20
    - high: otherwise
    """
    metrics = _calculate_diff_metrics(price1, price2)
    if metrics is None:
        return None

    _, _, abs_diff, rel_diff = metrics

    # no-severity: abs <= 0.005 OR rel <= 0.005
    if abs_diff <= Decimal("0.005") or rel_diff <= Decimal("0.005"):
        return DeviationSeverity.NO_SEVERITY

    # low: rel <= 0.05
    if rel_diff <= Decimal("0.05"):
        return DeviationSeverity.LOW

    # medium: rel <= 0.20
    if rel_diff <= Decimal("0.20"):
        return DeviationSeverity.MEDIUM

    return DeviationSeverity.HIGH


def get_quantity_severity(
    qty1: Decimal | float, qty2: Decimal | float
) -> DeviationSeverity | None:
    """
    Severity for quantity differences (non-partial delivery).
    Only called when qty > PO qty.

    Thresholds (spec):
    - low: abs <= 1 AND rel <= 0.10
    - medium: abs <= 10 OR rel <= 0.50
    - high: otherwise
    """
    metrics = _calculate_diff_metrics(qty1, qty2)
    if metrics is None:
        return None

    _, _, abs_diff, rel_diff = metrics

    # low: abs <= 1 AND rel <= 0.10
    if abs_diff <= Decimal("1") and rel_diff <= Decimal("0.10"):
        return DeviationSeverity.LOW

    # medium: abs <= 10 OR rel <= 0.50
    if abs_diff <= Decimal("10") or rel_diff <= Decimal("0.50"):
        return DeviationSeverity.MEDIUM

    return DeviationSeverity.HIGH


def get_differing_amounts_severity(
    amount1: Decimal | float, amount2: Decimal | float
) -> DeviationSeverity | None:
    """
    Legacy function - redirects to line amount severity.
    Kept for backward compatibility.
    """
    return get_line_amount_severity(amount1, amount2)


FIELD_COMPARISONS = []

FIELD_COMPARISONS.append(
    FieldComparison(
        code="AMOUNTS_DIFFER",
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
        code="DESCRIPTIONS_DIFFER",
        message="Descriptions differ",
        severity=DeviationSeverity.INFO,
        is_item_field=True,
        field_names={
            DocumentKind.INVOICE: "text",
            DocumentKind.PURCHASE_ORDER: "description",
            DocumentKind.DELIVERY_RECEIPT: "description",
        },
        field_encoded_type=str,
    )
)

# @TODO add thresholds for unit amounts if desired (currently uses MEDium default)
FIELD_COMPARISONS.append(
    FieldComparison(
        code="PRICES_PER_UNIT_DIFFER",
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
        code="QUANTITIES_DIFFER",
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

FIELD_COMPARISONS.append(
    FieldComparison(
        code="ARTICLE_NUMBERS_DIFFER",
        message="Article numbers differ",
        severity=DeviationSeverity.MEDIUM,
        is_item_field=True,
        field_names={
            DocumentKind.INVOICE: "inventory",
            DocumentKind.PURCHASE_ORDER: "inventory",
            DocumentKind.DELIVERY_RECEIPT: "inventory",
        },
        field_encoded_type=str,
    )
)


def getkv_value(kvs: list[dict] | None, name: str) -> Any | None:
    if not isinstance(kvs, list):
        return None
    for kv in kvs:
        if isinstance(kv, dict) and kv.get("name") == name:
            return kv.get("value")
    return None


def check_partial_delivery(
    document_kinds: list[DocumentKind],
    document_item_fields: list[list[dict] | None],
) -> FieldDeviation | None:
    """
    Check for partial delivery: invoice/DR quantity < PO quantity.
    Always returns INFO severity as this is informational, not an error.

    Returns a PARTIAL_DELIVERY deviation if detected, None otherwise.
    """
    po_index = None
    other_index = None
    for i, kind in enumerate(document_kinds):
        if kind == DocumentKind.PURCHASE_ORDER:
            po_index = i
        else:
            other_index = i

    if po_index is None or other_index is None:
        return None

    po_fields = document_item_fields[po_index]
    other_fields = document_item_fields[other_index]

    if po_fields is None or other_fields is None:
        return None

    po_qty_val = getkv_value(po_fields, "quantityToInvoice")
    other_kind = document_kinds[other_index]

    if other_kind == DocumentKind.INVOICE:
        other_qty_val = getkv_value(other_fields, "purchaseReceiptDataQuantity")
    else:
        other_qty_val = getkv_value(other_fields, "quantity")

    if po_qty_val is None or other_qty_val is None:
        return None

    try:
        po_qty = Decimal(str(po_qty_val))
        other_qty = Decimal(str(other_qty_val))
    except Exception:
        logger.warning(
            f"Could not convert quantities '{po_qty_val}', '{other_qty_val}' to Decimal."
        )
        return None

    if other_qty < po_qty:
        return FieldDeviation(
            code="PARTIAL_DELIVERY",
            severity=DeviationSeverity.INFO,
            message=f"Partial delivery: {other_qty} of {po_qty} ordered",
            field_names=["quantity", "quantityToInvoice"],
            field_values=[str(other_qty), str(po_qty)],
        )

    return None


def check_quantity_deviation(
    document_kinds: list[DocumentKind],
    document_item_fields: list[list[dict] | None],
) -> FieldDeviation | None:
    """
    Check for quantity mismatch (not partial delivery).
    Only fires when invoice/DR qty > PO qty.

    Returns a QUANTITIES_DIFFER deviation if detected, None otherwise.
    """
    po_index = None
    other_index = None
    for i, kind in enumerate(document_kinds):
        if kind == DocumentKind.PURCHASE_ORDER:
            po_index = i
        else:
            other_index = i

    if po_index is None or other_index is None:
        return None

    po_fields = document_item_fields[po_index]
    other_fields = document_item_fields[other_index]

    if po_fields is None or other_fields is None:
        return None

    po_qty_val = getkv_value(po_fields, "quantityToInvoice")
    other_kind = document_kinds[other_index]

    if other_kind == DocumentKind.INVOICE:
        other_qty_val = getkv_value(other_fields, "purchaseReceiptDataQuantity")
    else:
        other_qty_val = getkv_value(other_fields, "quantity")

    if po_qty_val is None or other_qty_val is None:
        return None

    try:
        po_qty = Decimal(str(po_qty_val))
        other_qty = Decimal(str(other_qty_val))
    except Exception:
        logger.warning(
            f"Could not convert quantities '{po_qty_val}', '{other_qty_val}' to Decimal."
        )
        return None

    if other_qty > po_qty:
        severity = get_quantity_severity(other_qty, po_qty)
        if severity is not None:
            diff = other_qty - po_qty
            return FieldDeviation(
                code="QUANTITIES_DIFFER",
                severity=severity,
                message=f"Quantity mismatch: {other_qty} vs {po_qty} ordered (diff: {diff:.2f})",
                field_names=["quantity", "quantityToInvoice"],
                field_values=[str(other_qty), str(po_qty)],
            )

    return None


def get_unmatched_item_severity(
    line_amount: Decimal | float | None,
) -> DeviationSeverity:
    """
    Determine severity for unmatched item based on line amount value.

    Thresholds (spec):
    - no-severity: line_amount <= 0.01
    - low: line_amount <= 1
    - medium: line_amount <= 10
    - high: line_amount > 10
    """
    if line_amount is None:
        return DeviationSeverity.LOW

    try:
        amount = Decimal(str(line_amount))
    except Exception:
        return DeviationSeverity.LOW

    if amount <= Decimal("0.01"):
        return DeviationSeverity.NO_SEVERITY
    if amount <= Decimal("1"):
        return DeviationSeverity.LOW
    if amount <= Decimal("10"):
        return DeviationSeverity.MEDIUM
    return DeviationSeverity.HIGH


def create_item_unmatched_deviation(
    item_data: dict,
    document_kind: DocumentKind,
) -> FieldDeviation:
    """
    Create ITEM_UNMATCHED deviation with severity based on line amount.
    """
    amount_field_map = {
        DocumentKind.INVOICE: "debit",
        DocumentKind.PURCHASE_ORDER: "unitAmount",
        DocumentKind.DELIVERY_RECEIPT: "amount",
    }

    raw_item = item_data.get("raw_item", {})
    fields = raw_item.get("fields", [])
    field_name = amount_field_map.get(document_kind)

    line_amount = None
    if fields and field_name:
        line_amount = getkv_value(fields, field_name)

    severity = get_unmatched_item_severity(line_amount)

    return FieldDeviation(
        code="ITEM_UNMATCHED",
        severity=severity,
        message=f"Item from {document_kind.value} could not be matched",
        field_names=[],
        field_values=[],
    )


def check_items_differ(
    similarities: dict | None = None,
) -> FieldDeviation | None:
    """
    Predict if paired items are actually different products.
    Based on article number and description similarities.

    Triggers when:
    - Article numbers differ significantly AND descriptions are dissimilar

    Severity:
    - HIGH when confidence >= 0.8
    - MEDIUM when confidence moderate (0.5-0.8)
    - LOW otherwise (but still reported)
    """
    if not similarities:
        return None

    item_id_sim = similarities.get("item_id")
    desc_sim = similarities.get("description")

    if item_id_sim is None and desc_sim is None:
        return None

    item_id_sim = item_id_sim if item_id_sim is not None else 1.0
    desc_sim = desc_sim if desc_sim is not None else 1.0

    if item_id_sim < 0.5 and desc_sim < 0.5:
        confidence = 1 - (item_id_sim + desc_sim) / 2
        if confidence >= 0.8:
            severity = DeviationSeverity.HIGH
        elif confidence >= 0.5:
            severity = DeviationSeverity.MEDIUM
        else:
            severity = DeviationSeverity.LOW
        return FieldDeviation(
            code="ITEMS_DIFFER",
            severity=severity,
            message=f"Items may be different products (confidence: {confidence:.0%})",
            field_names=[],
            field_values=[],
        )

    if (item_id_sim < 0.3 and desc_sim < 0.7) or (desc_sim < 0.3 and item_id_sim < 0.7):
        confidence = 0.6
        return FieldDeviation(
            code="ITEMS_DIFFER",
            severity=DeviationSeverity.MEDIUM,
            message=f"Items may be different products (confidence: {confidence:.0%})",
            field_names=[],
            field_values=[],
        )

    return None


def check_article_numbers_differ(
    document_kinds: list[DocumentKind],
    document_item_fields: list[list[dict] | None],
    description_similarity: float | None = None,
) -> FieldDeviation | None:
    """
    Check for article number differences with severity based on description similarity.

    Default severity: MEDIUM
    Downgrade to LOW if description_similarity >= 0.9
    """
    values = []
    field_names_used = []

    field_name_map = {
        DocumentKind.INVOICE: "inventory",
        DocumentKind.PURCHASE_ORDER: "inventory",
        DocumentKind.DELIVERY_RECEIPT: "inventory",
    }

    for i, doc_kind in enumerate(document_kinds):
        item_fields = document_item_fields[i] if i < len(document_item_fields) else None
        field_name = field_name_map.get(doc_kind)
        field_names_used.append(field_name)

        if not field_name or item_fields is None:
            values.append(None)
            continue

        value = getkv_value(item_fields, field_name)
        values.append(str(value) if value is not None else None)

    non_empty_values = [v for v in values if v is not None and str(v).strip()]

    if len(non_empty_values) < 2:
        return None

    first_value = non_empty_values[0]
    if all(v == first_value for v in non_empty_values):
        return None

    if description_similarity is not None and description_similarity >= 0.9:
        severity = DeviationSeverity.LOW
    else:
        severity = DeviationSeverity.MEDIUM

    return FieldDeviation(
        code="ARTICLE_NUMBERS_DIFFER",
        severity=severity,
        message=f"Article numbers differ ({' vs '.join(str(v) for v in non_empty_values)})",
        field_names=field_names_used,
        field_values=[str(v) if v is not None else None for v in values],
    )


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
            if comparison.code == "AMOUNTS_DIFFER":
                severity_calc = get_line_amount_severity(value1, value2)
                if severity_calc is not None:
                    current_severity = severity_calc
                    diff = abs(Decimal(str(value1)) - Decimal(str(value2)))
                    final_message = (
                        f"{comparison.message} ({value1} vs {value2}, diff: {diff:.2f})"
                    )
                    deviation_occurred = True
            elif comparison.code == "PRICES_PER_UNIT_DIFFER":
                severity_calc = get_unit_price_severity(value1, value2)
                if severity_calc is not None:
                    current_severity = severity_calc
                    diff = abs(Decimal(str(value1)) - Decimal(str(value2)))
                    final_message = (
                        f"{comparison.message} ({value1} vs {value2}, diff: {diff:.2f})"
                    )
                    deviation_occurred = True
            elif comparison.code == "QUANTITIES_DIFFER":
                severity_calc = get_quantity_severity(value1, value2)
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
    similarities: dict | None = None,
) -> list[FieldDeviation]:
    deviations = []
    if len(document_kinds) != len(document_item_fields):
        logger.error(
            "Mismatch between number of document kinds and item fields provided."
        )
        return deviations

    has_po = DocumentKind.PURCHASE_ORDER in document_kinds

    if has_po:
        partial_delivery = check_partial_delivery(document_kinds, document_item_fields)
        if partial_delivery:
            deviations.append(partial_delivery)
        else:
            qty_deviation = check_quantity_deviation(
                document_kinds, document_item_fields
            )
            if qty_deviation:
                deviations.append(qty_deviation)

    desc_sim = similarities.get("description") if similarities else None
    article_deviation = check_article_numbers_differ(
        document_kinds, document_item_fields, desc_sim
    )
    if article_deviation:
        deviations.append(article_deviation)

    items_differ = check_items_differ(similarities)
    if items_differ:
        deviations.append(items_differ)

    for comparison in FIELD_COMPARISONS:
        if comparison.is_item_field:
            if comparison.code == "QUANTITIES_DIFFER" and has_po:
                continue
            if comparison.code == "ARTICLE_NUMBERS_DIFFER":
                continue
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
                {"name": "description", "value": "Brandslang 63mm"},
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
