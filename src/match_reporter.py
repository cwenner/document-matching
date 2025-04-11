# match_reporter.py

import hashlib
from decimal import Decimal
import logging

from itempair_deviations import (
    DocumentKind,
    DeviationSeverity,
    FieldDeviation,
    # FIELD_COMPARISONS, # Removed unused import
    get_differing_amounts_severity,
)
from document_utils import get_field

logger = logging.getLogger(__name__)


# Helper function for similarity check
def _calculate_overall_severity(
    severities: list[DeviationSeverity],
) -> DeviationSeverity:
    if not severities:
        return DeviationSeverity.NO_SEVERITY
    try:
        return max(severities)
    except Exception as e:
        logger.error(f"Error calculating overall severity from {severities}: {e}")
        return DeviationSeverity.HIGH


def collect_document_deviations(
    doc1: dict | None, doc2: dict | None
) -> list[FieldDeviation]:
    deviations = []
    if not doc1 or not doc2:
        logger.warning("Cannot collect document deviations with missing documents.")
        return deviations

    try:
        kind1 = DocumentKind(get_field(doc1, "kind"))
        kind2 = DocumentKind(get_field(doc2, "kind"))
    except ValueError as e:
        logger.error(f"Invalid document kind for document deviation check: {e}")
        deviations.append(
            FieldDeviation(
                code="invalid-doc-kind", severity=DeviationSeverity.HIGH, message=str(e)
            )
        )
        return deviations

    currency1 = get_field(doc1, "currency")
    currency2 = get_field(doc2, "currency")
    if currency1 is not None and currency2 is not None and currency1 != currency2:
        if str(currency1).strip() and str(currency2).strip():
            deviations.append(
                FieldDeviation(
                    code="currencies-differ",
                    severity=DeviationSeverity.HIGH,
                    message=f"Currencies differ: {currency1} vs {currency2}",
                    field_names=["currency", "currency"],
                    field_values=[currency1, currency2],
                )
            )
        elif not str(currency1).strip() and str(currency2).strip():
            logger.debug(
                f"Currency mismatch ignored: Doc1 currency empty, Doc2 is '{currency2}'."
            )
        elif str(currency1).strip() and not str(currency2).strip():
            logger.debug(
                f"Currency mismatch ignored: Doc1 currency '{currency1}', Doc2 is empty."
            )

    total_amount_field = "incVatAmount"
    amount1_str = get_field(doc1, total_amount_field)
    amount2_str = get_field(doc2, total_amount_field)

    if amount1_str is not None and amount2_str is not None:
        try:
            amount1 = Decimal(str(amount1_str))
            amount2 = Decimal(str(amount2_str))
            severity = get_differing_amounts_severity(amount1, amount2)

            if severity:
                diff = abs(amount1 - amount2)
                deviations.append(
                    FieldDeviation(
                        code="total-amounts-differ",
                        severity=severity,
                        message=f"Total amount ({total_amount_field}) differs by {diff:.2f}",
                        field_names=[total_amount_field, total_amount_field],
                        field_values=[amount1_str, amount2_str],
                    )
                )
        except Exception as e:
            logger.warning(
                f"Could not compare total amounts ('{amount1_str}' vs '{amount2_str}') using field '{total_amount_field}': {e}"
            )

    logger.debug(f"Collected {len(deviations)} document-level deviations.")
    return deviations


def generate_match_report(
    doc1: dict,
    doc2: dict,
    processed_item_pairs: list[dict],
    document_deviations: list[FieldDeviation],
) -> dict:
    if not doc1 or not doc2:
        logger.error("Cannot generate match report with missing input documents.")
        return {"error": "Missing input documents"}

    try:
        kind1 = DocumentKind(get_field(doc1, "kind"))
        kind2 = DocumentKind(get_field(doc2, "kind"))
    except ValueError as e:
        logger.error(f"Cannot generate match report due to invalid document kind: {e}")
        return {"error": f"Invalid document kind: {e}"}

    doc_ids_tuple = tuple(sorted((doc1.get("id", ""), doc2.get("id", ""))))
    report_hash = hashlib.sha1(str(doc_ids_tuple).encode()).hexdigest()[:8]
    report_id = f"rep-{report_hash}"

    report = {
        "version": "v4.1-dev-split",
        "id": report_id,
        "kind": "match-report",
        "site": get_field(doc1, "site") or get_field(doc2, "site") or "unknown-site",
        "stage": "output",
        "headers": [],
        "documents": [
            {"kind": kind1.value, "id": doc1.get("id")},
            {"kind": kind2.value, "id": doc2.get("id")},
        ],
        "labels": ["match"] if processed_item_pairs else ["potential-match-no-items"],
        "metrics": [
            {"name": "certainty", "value": 0.93},
            {
                "name": "deviation-severity",
                "value": DeviationSeverity.NO_SEVERITY.value,
            },
            {"name": f"{kind1.value}-has-future-match-certainty", "value": 0.0},
            {"name": f"{kind2.value}-has-future-match-certainty", "value": 0.0},
            {"name": "matched_item_pairs", "value": len(processed_item_pairs)},
            {"name": f"{kind1.value}_total_items", "value": len(doc1.get("items", []))},
            {"name": f"{kind2.value}_total_items", "value": len(doc2.get("items", []))},
        ],
        "deviations": [dev.dict() for dev in document_deviations],
        "itempairs": [],
    }

    all_report_severities = [dev.severity for dev in document_deviations]

    for pair_data in processed_item_pairs:
        item1_data = pair_data.get("item1")
        item2_data = pair_data.get("item2")
        item_deviations = pair_data.get("deviations", [])

        if not item1_data or not item2_data:
            logger.warning(
                f"Skipping item pair in report due to missing item data: {pair_data}"
            )
            continue

        pair_severity = _calculate_overall_severity(
            [dev.severity for dev in item_deviations]
        )
        all_report_severities.append(pair_severity)

        item_pair_report = {
            "item_indices": [
                item1_data.get("item_index"),
                item2_data.get("item_index"),
            ],
            "match_type": "matched",
            "match_score": pair_data.get("score"),
            "deviation_severity": pair_severity.value,
            "item_unchanged_certainty": 0.95,
            "deviations": [dev.dict() for dev in item_deviations],
        }
        report["itempairs"].append(item_pair_report)

    overall_report_severity = _calculate_overall_severity(all_report_severities)
    for metric in report["metrics"]:
        if metric["name"] == "deviation-severity":
            metric["value"] = overall_report_severity.value
            break

    return report


def generate_no_match_report(doc1, doc2=None):
    if not doc1:
        logger.error("Cannot generate no-match report without primary document.")
        return {"error": "Missing primary document for no-match report"}

    try:
        kind1 = DocumentKind(get_field(doc1, "kind"))
    except ValueError as e:
        logger.error(
            f"Cannot generate no-match report due to invalid document kind: {e}"
        )
        return {"error": f"Invalid document kind: {e}"}

    doc_ids_tuple = tuple(
        sorted((doc1.get("id", ""), doc2.get("id", "") if doc2 else ""))
    )
    report_hash = hashlib.sha1(str(doc_ids_tuple).encode()).hexdigest()[:8]
    report_id = f"rep-{report_hash}-nomatch"

    report = {
        "version": "v4.1-dev-split",
        "id": report_id,
        "kind": "match-report",
        "site": get_field(doc1, "site")
        or (get_field(doc2, "site") if doc2 else None)
        or "unknown-site",
        "stage": "output",
        "headers": [],
        "documents": [{"kind": kind1.value, "id": doc1.get("id")}],
        "labels": ["no-match"],
        "metrics": [
            {"name": "certainty", "value": 0.95},
            {
                "name": "deviation-severity",
                "value": DeviationSeverity.NO_SEVERITY.value,
            },
            {"name": f"{kind1.value}-has-future-match-certainty", "value": 0.88},
            {"name": "matched_item_pairs", "value": 0},
            {"name": f"{kind1.value}_total_items", "value": len(doc1.get("items", []))},
        ],
        "deviations": [],
        "itempairs": [],
    }

    if doc2:
        try:
            kind2 = DocumentKind(get_field(doc2, "kind"))
            report["documents"].append({"kind": kind2.value, "id": doc2.get("id")})
            report["metrics"].append(
                {"name": f"{kind2.value}-has-future-match-certainty", "value": 0.88}
            )
            report["metrics"].append(
                {
                    "name": f"{kind2.value}_total_items",
                    "value": len(doc2.get("items", [])),
                }
            )
        except ValueError as e:
            logger.warning(
                f"Could not add second document {doc2.get('id')} to no-match report due to invalid kind: {e}"
            )

    return report
