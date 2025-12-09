"""Unit tests for bidirectional matching order symmetry (ADR-002)."""

import pytest

from docpairing import DocumentPairingPredictor


class TestFeatureExtractionOrderSymmetry:
    """Tests that feature extraction is symmetric for invoice/PO pairs."""

    @pytest.fixture
    def predictor(self):
        """Create a document pairing predictor instance."""
        return DocumentPairingPredictor()

    @pytest.fixture
    def sample_invoice(self):
        """Sample invoice document for testing."""
        return {
            "id": "invoice-001",
            "kind": "invoice",
            "site": "test-site",
            "stage": "input",
            "supplier": {"id": "supplier-001"},
            "inc_vat_amount": {"value": 1000.0, "currency": "EUR"},
            "exc_vat_amount": {"value": 800.0, "currency": "EUR"},
            "date": "2024-03-15",
            "items": [
                {
                    "fields": [
                        {"name": "article_number", "value": "ART-001"},
                        {"name": "description", "value": "Widget A"},
                    ]
                },
                {
                    "fields": [
                        {"name": "article_number", "value": "ART-002"},
                        {"name": "description", "value": "Widget B"},
                    ]
                },
            ],
        }

    @pytest.fixture
    def sample_po(self):
        """Sample purchase order document for testing."""
        return {
            "id": "po-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "historical",
            "supplier": {"id": "supplier-001"},
            "inc_vat_amount": {"value": 1000.0, "currency": "EUR"},
            "exc_vat_amount": {"value": 800.0, "currency": "EUR"},
            "date": "2024-03-10",
            "items": [
                {
                    "fields": [
                        {"name": "article_number", "value": "ART-001"},
                        {"name": "description", "value": "Widget A"},
                    ]
                },
                {
                    "fields": [
                        {"name": "article_number", "value": "ART-002"},
                        {"name": "description", "value": "Widget B"},
                    ]
                },
            ],
        }

    @pytest.mark.model
    def test_feature_extraction_order_symmetric(
        self, predictor, sample_invoice, sample_po
    ):
        """Feature extraction should produce same results regardless of argument order.

        This verifies ADR-002: canonical order normalization works correctly.
        """
        # Extract features with (invoice, po) order
        features_inv_po = predictor._get_comparison_features(sample_invoice, sample_po)

        # Extract features with (po, invoice) order
        features_po_inv = predictor._get_comparison_features(sample_po, sample_invoice)

        # Features should be identical regardless of order
        assert features_inv_po == features_po_inv, (
            "Feature extraction should be symmetric for invoice/PO pairs. "
            f"Got different features: {features_inv_po} vs {features_po_inv}"
        )

    @pytest.mark.model
    def test_symmetric_features_have_expected_keys(
        self, predictor, sample_invoice, sample_po
    ):
        """Extracted features should contain expected keys."""
        features = predictor._get_comparison_features(sample_invoice, sample_po)

        expected_keys = [
            "num_invoice_article_numbers",
            "num_po_article_numbers",
            "num_matching_article_numbers",
            "exc_vat_amount_diff",
            "inc_vat_amount_diff",
            "date_diff",
        ]

        for key in expected_keys:
            assert key in features, f"Expected feature key '{key}' not found"

    @pytest.mark.model
    def test_symmetric_features_amount_diff_consistent(
        self, predictor, sample_invoice, sample_po
    ):
        """Amount difference features should be consistent regardless of order."""
        features_inv_po = predictor._get_comparison_features(sample_invoice, sample_po)
        features_po_inv = predictor._get_comparison_features(sample_po, sample_invoice)

        # Amount diffs should be identical in both orderings
        assert (
            features_inv_po["exc_vat_amount_diff"]
            == features_po_inv["exc_vat_amount_diff"]
        )
        assert (
            features_inv_po["inc_vat_amount_diff"]
            == features_po_inv["inc_vat_amount_diff"]
        )

    @pytest.mark.model
    def test_symmetric_features_date_diff_consistent(
        self, predictor, sample_invoice, sample_po
    ):
        """Date difference should be consistent regardless of order."""
        features_inv_po = predictor._get_comparison_features(sample_invoice, sample_po)
        features_po_inv = predictor._get_comparison_features(sample_po, sample_invoice)

        # Date diff should be identical in both orderings
        assert features_inv_po["date_diff"] == features_po_inv["date_diff"]
