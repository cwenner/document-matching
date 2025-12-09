"""Integration tests for full matching pipeline.

This module tests the end-to-end document matching flow from submission
to report generation, covering two-way and three-way matching with deviation detection.
"""

import json

import pytest
from fastapi.testclient import TestClient

import app


@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    return TestClient(app.app)


@pytest.fixture
def context():
    """Shared context between test functions."""
    return {}


class TestFullMatchingPipeline:
    """Integration tests for the complete matching pipeline."""

    def test_two_way_matching_invoice_to_po(self, client, context):
        """Test full pipeline for two-way matching: Invoice to Purchase Order.

        This test covers:
        - Document submission via API endpoint
        - Document pairing prediction
        - Item pairing within matched documents
        - Deviation detection (amounts, quantities, descriptions)
        - Match report generation with all required fields
        """
        # Arrange: Create primary invoice document
        primary_invoice = {
            "version": "v3",
            "id": "INT-INV-001",
            "kind": "invoice",
            "site": "integration-test",
            "stage": "input",
            "headers": [
                {"name": "supplierId", "value": "SUPP-100"},
                {"name": "invoiceDate", "value": "2025-12-08"},
                {"name": "invoiceNumber", "value": "INV-2025-1208"},
                {"name": "incVatAmount", "value": "1200.00"},
                {"name": "currencyCode", "value": "USD"},
                {"name": "excVatAmount", "value": "1000.00"},
                {"name": "type", "value": "DEBIT"},
                {"name": "orderReference", "value": "PO-2025-500"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "text", "value": "Widget Pro Model X"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "WDG-PRO-X"},
                        {"name": "purchaseReceiptDataQuantity", "value": "10"},
                        {"name": "debit", "value": "500.00"},
                        {"name": "purchaseReceiptDataUnitAmount", "value": "50.00"},
                    ]
                },
                {
                    "fields": [
                        {"name": "text", "value": "Gadget Standard Y"},
                        {"name": "lineNumber", "value": "2"},
                        {"name": "inventory", "value": "GDG-STD-Y"},
                        {"name": "purchaseReceiptDataQuantity", "value": "20"},
                        {"name": "debit", "value": "500.00"},
                        {"name": "purchaseReceiptDataUnitAmount", "value": "25.00"},
                    ]
                },
            ],
        }

        # Candidate purchase order with matching PO reference but slight deviations
        candidate_po = {
            "version": "v3",
            "id": "INT-PO-001",
            "kind": "purchase-order",
            "site": "integration-test",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-2025-500"},
                {"name": "supplierId", "value": "SUPP-100"},
                {"name": "description", "value": "Standard order"},
                {"name": "orderDate", "value": "2025-12-01"},
                {"name": "incVatAmount", "value": "1150.00"},  # Small amount deviation
                {"name": "excVatAmount", "value": "958.33"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "PO-ITEM-001"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "WDG-PRO-X"},
                        {"name": "description", "value": "Widget Pro Model X"},
                        {"name": "uom", "value": "EA"},
                        {"name": "unitAmount", "value": "48.00"},  # Price deviation
                        {"name": "quantityOrdered", "value": "10"},
                        {"name": "quantityToReceive", "value": "10"},
                        {"name": "quantityReceived", "value": "0"},
                        {"name": "quantityToInvoice", "value": "10"},
                    ]
                },
                {
                    "fields": [
                        {"name": "id", "value": "PO-ITEM-002"},
                        {"name": "lineNumber", "value": "2"},
                        {"name": "inventory", "value": "GDG-STD-Y"},
                        {"name": "description", "value": "Gadget Standard Y"},
                        {"name": "uom", "value": "EA"},
                        {"name": "unitAmount", "value": "25.00"},
                        {"name": "quantityOrdered", "value": "22"},  # Quantity deviation
                        {"name": "quantityToReceive", "value": "22"},
                        {"name": "quantityReceived", "value": "0"},
                        {"name": "quantityToInvoice", "value": "22"},
                    ]
                },
            ],
        }

        payload = {
            "document": primary_invoice,
            "candidate-documents": [candidate_po],
        }

        # Act: Send request through full pipeline
        response = client.post("/", json=payload)

        # Assert: Verify response structure and content
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        result = response.json()

        # Verify match report structure
        assert result["kind"] == "match-report", "Should return a match report"
        assert result["version"] == "v3", "Should have version v3"
        assert "id" in result, "Match report should have an ID"

        # Verify labels indicate a match
        assert "labels" in result, "Match report should have labels"
        assert "match" in result["labels"], "Should have 'match' label"

        # Verify matched documents are included
        assert "documents" in result, "Match report should include documents"
        assert len(result["documents"]) == 2, "Should have exactly 2 documents in two-way match"

        doc_ids = [doc["id"] for doc in result["documents"]]
        assert "INT-INV-001" in doc_ids, "Should include primary invoice"
        assert "INT-PO-001" in doc_ids, "Should include matched PO"

        # Verify item pairs are present
        assert "itempairs" in result, "Match report should include itempairs"
        assert len(result["itempairs"]) > 0, "Should have at least one item pair"

        # Verify deviations are detected
        assert "deviations" in result, "Match report should include deviations array"

        # Check for document-level amount deviation
        deviation_codes = [dev.get("code") for dev in result.get("deviations", [])]
        assert "AMOUNTS_DIFFER" in deviation_codes, "Should detect amount deviation at document level"

        # Verify item-level deviations
        item_deviation_codes = []
        for itempair in result["itempairs"]:
            assert "deviations" in itempair, "Each itempair should have deviations array"
            for dev in itempair["deviations"]:
                item_deviation_codes.append(dev.get("code"))

        # Should detect price or quantity deviations at item level
        assert any(
            code in item_deviation_codes
            for code in ["PRICES_PER_UNIT_DIFFER", "QUANTITIES_DIFFER"]
        ), "Should detect item-level deviations (price or quantity)"

        # Verify all deviations have required fields
        for dev in result.get("deviations", []):
            assert "code" in dev, "Deviation should have code"
            assert "severity" in dev, "Deviation should have severity"
            assert "message" in dev, "Deviation should have message"
            assert dev["severity"] in ["no-severity", "info", "low", "medium", "high"], \
                f"Invalid severity: {dev['severity']}"

        # Verify metrics are present
        assert "metrics" in result, "Match report should include metrics"
        metric_names = [m.get("name") for m in result["metrics"]]
        assert "match-certainty" in metric_names, "Should include match-certainty metric"

    def test_three_way_matching_invoice_po_delivery(self, client, context):
        """Test full pipeline for three-way matching: Invoice, Purchase Order, and Delivery Receipt.

        This test covers:
        - Matching across three document types
        - Complex deviation scenarios across multiple documents
        - Report generation for three-way matches
        """
        # Arrange: Create three related documents
        primary_invoice = {
            "version": "v3",
            "id": "INT3-INV-001",
            "kind": "invoice",
            "site": "integration-test",
            "stage": "input",
            "headers": [
                {"name": "supplierId", "value": "SUPP-200"},
                {"name": "invoiceDate", "value": "2025-12-08"},
                {"name": "invoiceNumber", "value": "INV-2025-3W-001"},
                {"name": "incVatAmount", "value": "600.00"},
                {"name": "currencyCode", "value": "EUR"},
                {"name": "excVatAmount", "value": "500.00"},
                {"name": "type", "value": "DEBIT"},
                {"name": "orderReference", "value": "PO-2025-3W-100"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "text", "value": "Component Alpha"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "COMP-ALPHA"},
                        {"name": "purchaseReceiptDataQuantity", "value": "5"},
                        {"name": "debit", "value": "500.00"},
                        {"name": "purchaseReceiptDataUnitAmount", "value": "100.00"},
                    ]
                },
            ],
        }

        # Purchase order
        candidate_po = {
            "version": "v3",
            "id": "INT3-PO-001",
            "kind": "purchase-order",
            "site": "integration-test",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-2025-3W-100"},
                {"name": "supplierId", "value": "SUPP-200"},
                {"name": "description", "value": "Component order"},
                {"name": "orderDate", "value": "2025-11-01"},
                {"name": "incVatAmount", "value": "600.00"},
                {"name": "excVatAmount", "value": "500.00"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "PO3-ITEM-001"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "COMP-ALPHA"},
                        {"name": "description", "value": "Component Alpha"},
                        {"name": "uom", "value": "EA"},
                        {"name": "unitAmount", "value": "100.00"},
                        {"name": "quantityOrdered", "value": "5"},
                        {"name": "quantityToReceive", "value": "5"},
                        {"name": "quantityReceived", "value": "5"},
                        {"name": "quantityToInvoice", "value": "5"},
                    ]
                },
            ],
        }

        # Delivery receipt
        candidate_delivery = {
            "version": "v3",
            "id": "INT3-DR-001",
            "kind": "delivery-receipt",
            "site": "integration-test",
            "stage": "final",
            "headers": [
                {"name": "deliveryReceiptNumber", "value": "DR-2025-001"},
                {"name": "supplierId", "value": "SUPP-200"},
                {"name": "deliveryDate", "value": "2025-11-15"},
                {"name": "orderReference", "value": "PO-2025-3W-100"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "DR3-ITEM-001"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "COMP-ALPHA"},
                        {"name": "description", "value": "Component Alpha"},
                        {"name": "quantityReceived", "value": "5"},
                        {"name": "uom", "value": "EA"},
                    ]
                },
            ],
        }

        payload = {
            "document": primary_invoice,
            "candidate-documents": [candidate_po, candidate_delivery],
        }

        # Act: Send request through full pipeline
        response = client.post("/", json=payload)

        # Assert: Verify response for three-way match
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        result = response.json()

        # Basic structure validation
        assert result["kind"] == "match-report", "Should return a match report"
        assert "match" in result.get("labels", []), "Should indicate a match"

        # For three-way matching, the system matches invoice to PO first
        # The delivery receipt would be matched separately or linked through PO reference
        assert "documents" in result, "Should include matched documents"
        assert len(result["documents"]) >= 2, "Should have at least 2 documents matched"

        # Verify basic report structure
        assert "itempairs" in result, "Should include itempairs"
        assert "deviations" in result, "Should include deviations"
        assert "metrics" in result, "Should include metrics"

    def test_no_match_scenario(self, client, context):
        """Test full pipeline when no match is found.

        This test covers:
        - No-match report generation
        - Proper handling of mismatched documents
        - Correct labels and certainty metrics for no-match
        """
        # Arrange: Create invoice with no matching candidates
        primary_invoice = {
            "version": "v3",
            "id": "INT-NOMATCH-INV-001",
            "kind": "invoice",
            "site": "integration-test",
            "stage": "input",
            "headers": [
                {"name": "supplierId", "value": "SUPP-999"},
                {"name": "invoiceDate", "value": "2025-12-08"},
                {"name": "invoiceNumber", "value": "INV-NOMATCH-001"},
                {"name": "incVatAmount", "value": "100.00"},
                {"name": "currencyCode", "value": "USD"},
                {"name": "excVatAmount", "value": "83.33"},
                {"name": "type", "value": "DEBIT"},
                {"name": "orderReference", "value": "PO-NONEXISTENT"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "text", "value": "Unique Product"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "debit", "value": "83.33"},
                    ]
                },
            ],
        }

        # Candidate with different supplier - should not match
        candidate_po = {
            "version": "v3",
            "id": "INT-NOMATCH-PO-001",
            "kind": "purchase-order",
            "site": "integration-test",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-DIFFERENT-123"},
                {"name": "supplierId", "value": "SUPP-000"},  # Different supplier
                {"name": "description", "value": "Different order"},
                {"name": "orderDate", "value": "2025-12-01"},
                {"name": "incVatAmount", "value": "100.00"},
                {"name": "excVatAmount", "value": "83.33"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "PO-ITEM-999"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "DIFF-PROD"},
                        {"name": "description", "value": "Different Product"},
                        {"name": "uom", "value": "EA"},
                        {"name": "unitAmount", "value": "83.33"},
                        {"name": "quantityOrdered", "value": "1"},
                    ]
                },
            ],
        }

        payload = {
            "document": primary_invoice,
            "candidate-documents": [candidate_po],
        }

        # Act: Send request through full pipeline
        response = client.post("/", json=payload)

        # Assert: Verify no-match response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        result = response.json()

        # Verify no-match report structure
        assert result["kind"] == "match-report", "Should return a match report"
        assert "labels" in result, "Should have labels"
        assert "no-match" in result["labels"], "Should have 'no-match' label"

        # Verify only primary document is included
        assert "documents" in result, "Should include documents"
        assert len(result["documents"]) == 1, "No-match should only include primary document"
        assert result["documents"][0]["id"] == "INT-NOMATCH-INV-001", \
            "Should include primary document"

        # Verify certainty metric indicates low confidence match (high confidence no-match)
        assert "metrics" in result, "Should include metrics"
        certainty_metric = None
        for metric in result["metrics"]:
            if metric.get("name") == "match-certainty":
                certainty_metric = metric
                break

        assert certainty_metric is not None, "Should include match-certainty metric"
        # For no-match, certainty should be below threshold (typically < 0.2)
        assert float(certainty_metric.get("value", 1.0)) < 0.3, \
            "No-match should have low match-certainty value"

    def test_empty_candidates_list(self, client, context):
        """Test pipeline with empty candidate list.

        This test covers:
        - Handling of empty candidate documents list
        - Proper no-match report generation
        """
        # Arrange: Invoice with no candidates
        primary_invoice = {
            "version": "v3",
            "id": "INT-EMPTY-INV-001",
            "kind": "invoice",
            "site": "integration-test",
            "stage": "input",
            "headers": [
                {"name": "supplierId", "value": "SUPP-111"},
                {"name": "invoiceDate", "value": "2025-12-08"},
                {"name": "invoiceNumber", "value": "INV-EMPTY-001"},
                {"name": "incVatAmount", "value": "50.00"},
                {"name": "currencyCode", "value": "USD"},
                {"name": "excVatAmount", "value": "41.67"},
                {"name": "type", "value": "DEBIT"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "text", "value": "Standalone Item"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "debit", "value": "41.67"},
                    ]
                },
            ],
        }

        payload = {
            "document": primary_invoice,
            "candidate-documents": [],  # Empty list
        }

        # Act: Send request
        response = client.post("/", json=payload)

        # Assert: Verify no-match response for empty candidates
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        result = response.json()

        # Should return no-match report
        assert result["kind"] == "match-report", "Should return a match report"
        assert "no-match" in result.get("labels", []), "Should indicate no-match"
        assert len(result.get("documents", [])) == 1, "Should only include primary document"

    def test_comprehensive_deviation_detection(self, client, context):
        """Test that the pipeline detects various types of deviations.

        This test specifically validates:
        - Amount deviations (document and item level)
        - Quantity deviations
        - Price per unit deviations
        - Description deviations
        - Unmatched items
        - Deviation severity classification
        """
        # Arrange: Create documents with multiple deviation types
        primary_invoice = {
            "version": "v3",
            "id": "INT-DEV-INV-001",
            "kind": "invoice",
            "site": "integration-test",
            "stage": "input",
            "headers": [
                {"name": "supplierId", "value": "SUPP-300"},
                {"name": "invoiceDate", "value": "2025-12-08"},
                {"name": "invoiceNumber", "value": "INV-DEV-001"},
                {"name": "incVatAmount", "value": "1500.00"},  # Different from PO
                {"name": "currencyCode", "value": "USD"},
                {"name": "excVatAmount", "value": "1250.00"},
                {"name": "type", "value": "DEBIT"},
                {"name": "orderReference", "value": "PO-DEV-001"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "text", "value": "Premium Widget X"},  # Description variation
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "WDG-X"},
                        {"name": "purchaseReceiptDataQuantity", "value": "10"},  # Quantity diff
                        {"name": "debit", "value": "600.00"},  # Amount diff
                        {"name": "purchaseReceiptDataUnitAmount", "value": "60.00"},  # Price diff
                    ]
                },
                {
                    "fields": [
                        {"name": "text", "value": "Extra Invoice Item"},  # Unmatched item
                        {"name": "lineNumber", "value": "2"},
                        {"name": "inventory", "value": "EXTRA-001"},
                        {"name": "purchaseReceiptDataQuantity", "value": "1"},
                        {"name": "debit", "value": "650.00"},
                    ]
                },
            ],
        }

        candidate_po = {
            "version": "v3",
            "id": "INT-DEV-PO-001",
            "kind": "purchase-order",
            "site": "integration-test",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-DEV-001"},
                {"name": "supplierId", "value": "SUPP-300"},
                {"name": "description", "value": "Test order with deviations"},
                {"name": "orderDate", "value": "2025-11-01"},
                {"name": "incVatAmount", "value": "1200.00"},  # Amount deviation
                {"name": "excVatAmount", "value": "1000.00"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "PO-DEV-ITEM-001"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "WDG-X"},
                        {"name": "description", "value": "Widget X Standard"},  # Different description
                        {"name": "uom", "value": "EA"},
                        {"name": "unitAmount", "value": "50.00"},  # Price deviation
                        {"name": "quantityOrdered", "value": "12"},  # Quantity deviation
                        {"name": "quantityToReceive", "value": "12"},
                        {"name": "quantityReceived", "value": "0"},
                        {"name": "quantityToInvoice", "value": "12"},
                    ]
                },
            ],
        }

        payload = {
            "document": primary_invoice,
            "candidate-documents": [candidate_po],
        }

        # Act: Send request
        response = client.post("/", json=payload)

        # Assert: Verify comprehensive deviation detection
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        result = response.json()

        # Should be a match despite deviations
        assert "match" in result.get("labels", []), "Should still match despite deviations"

        # Verify document-level deviations
        doc_deviation_codes = [dev.get("code") for dev in result.get("deviations", [])]
        assert "AMOUNTS_DIFFER" in doc_deviation_codes, \
            "Should detect document-level amount deviation"

        # Verify item-level deviations
        all_item_deviations = []
        for itempair in result.get("itempairs", []):
            for dev in itempair.get("deviations", []):
                all_item_deviations.append(dev.get("code"))

        # Check for various deviation types
        assert "QUANTITIES_DIFFER" in all_item_deviations or \
               "PRICES_PER_UNIT_DIFFER" in all_item_deviations or \
               "DESCRIPTIONS_DIFFER" in all_item_deviations, \
            "Should detect item-level deviations"

        # Check for unmatched item
        assert "ITEM_UNMATCHED" in all_item_deviations, \
            "Should detect unmatched item from invoice"

        # Verify all deviations have severity levels
        for dev in result.get("deviations", []):
            assert "severity" in dev, f"Deviation {dev.get('code')} missing severity"
            assert dev["severity"] in ["no-severity", "info", "low", "medium", "high"], \
                f"Invalid severity: {dev['severity']}"

        for itempair in result.get("itempairs", []):
            for dev in itempair.get("deviations", []):
                assert "severity" in dev, f"Item deviation {dev.get('code')} missing severity"
                assert dev["severity"] in ["no-severity", "info", "low", "medium", "high"], \
                    f"Invalid severity: {dev['severity']}"

        # Verify deviation-severity metric
        metrics = {m.get("name"): m.get("value") for m in result.get("metrics", [])}
        assert "deviation-severity" in metrics, "Should include deviation-severity metric"
        assert metrics["deviation-severity"] in ["no-severity", "info", "low", "medium", "high"], \
            f"Invalid deviation-severity metric: {metrics['deviation-severity']}"
