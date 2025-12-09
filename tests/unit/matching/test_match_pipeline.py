"""Unit tests for match_pipeline.py functions."""

import pytest
from unittest.mock import MagicMock, patch, call

from match_pipeline import run_matching_pipeline, CONFIDENT_NO_MATCH_CERTAINTY
from itempair_deviations import FieldDeviation
from match_reporter import DeviationSeverity, NO_MATCH_CERTAINTY_THRESHOLD


class TestRunMatchingPipeline:
    """Tests for run_matching_pipeline function."""

    @pytest.fixture
    def mock_predictor(self, mocker):
        """Create a mock DocumentPairingPredictor."""
        predictor = mocker.MagicMock()
        predictor.id2document = {}
        predictor.clear_documents = mocker.MagicMock()
        predictor.record_document = mocker.MagicMock()
        predictor.predict_pairings = mocker.MagicMock(return_value=[])
        return predictor

    @pytest.fixture
    def sample_input_document(self):
        """Create a sample input document."""
        return {
            "id": "doc-001",
            "kind": "invoice",
            "fields": [
                {"name": "total", "value": "100.00"},
                {"name": "orderReference", "value": "PO-123"},
            ],
        }

    @pytest.fixture
    def sample_historical_documents(self):
        """Create sample historical documents."""
        return [
            {
                "id": "doc-002",
                "kind": "purchase-order",
                "fields": [{"name": "orderNumber", "value": "PO-123"}],
            },
            {
                "id": "doc-003",
                "kind": "delivery-receipt",
                "fields": [{"name": "receiptNumber", "value": "DR-456"}],
            },
        ]

    def test_returns_none_when_predictor_is_none(self):
        """Pipeline returns None if predictor is not initialized."""
        result = run_matching_pipeline(None, {"id": "test"}, [])
        assert result is None

    def test_returns_none_when_predictor_is_false(self):
        """Pipeline returns None if predictor is falsy."""
        result = run_matching_pipeline(False, {"id": "test"}, [])
        assert result is None

    @patch("match_pipeline.unpack_attachments")
    def test_unpacks_attachments_for_input_document(
        self, mock_unpack, mock_predictor, sample_input_document
    ):
        """Pipeline unpacks attachments for input document."""
        with patch("match_pipeline.generate_no_match_report", return_value={}):
            run_matching_pipeline(mock_predictor, sample_input_document, [])
            mock_unpack.assert_any_call(sample_input_document)

    @patch("match_pipeline.unpack_attachments")
    def test_unpacks_attachments_for_historical_documents(
        self,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline unpacks attachments for all historical documents."""
        with patch("match_pipeline.generate_no_match_report", return_value={}):
            run_matching_pipeline(
                mock_predictor, sample_input_document, sample_historical_documents
            )
            for doc in sample_historical_documents:
                mock_unpack.assert_any_call(doc)

    def test_clears_predictor_documents_before_recording(
        self, mock_predictor, sample_input_document, sample_historical_documents
    ):
        """Pipeline clears predictor documents before recording new ones."""
        with patch("match_pipeline.unpack_attachments"):
            with patch("match_pipeline.generate_no_match_report", return_value={}):
                run_matching_pipeline(
                    mock_predictor, sample_input_document, sample_historical_documents
                )
                mock_predictor.clear_documents.assert_called_once()

    def test_records_all_historical_documents(
        self, mock_predictor, sample_input_document, sample_historical_documents
    ):
        """Pipeline records all historical documents in predictor."""
        with patch("match_pipeline.unpack_attachments"):
            with patch("match_pipeline.generate_no_match_report", return_value={}):
                run_matching_pipeline(
                    mock_predictor, sample_input_document, sample_historical_documents
                )
                # Check that record_document was called for each historical doc
                assert mock_predictor.record_document.call_count >= len(
                    sample_historical_documents
                )

    def test_records_input_document(
        self, mock_predictor, sample_input_document, sample_historical_documents
    ):
        """Pipeline records input document in predictor."""
        with patch("match_pipeline.unpack_attachments"):
            with patch("match_pipeline.generate_no_match_report", return_value={}):
                run_matching_pipeline(
                    mock_predictor, sample_input_document, sample_historical_documents
                )
                # Input document should be recorded too
                calls = mock_predictor.record_document.call_args_list
                assert any(
                    call_args[0][0]["id"] == sample_input_document["id"]
                    for call_args in calls
                )

    def test_handles_input_document_without_id(
        self, mock_predictor, sample_historical_documents
    ):
        """Pipeline handles input document missing id field."""
        input_doc_no_id = {"kind": "invoice", "fields": []}
        with patch("match_pipeline.unpack_attachments"):
            with patch("match_pipeline.generate_no_match_report", return_value={}):
                result = run_matching_pipeline(
                    mock_predictor, input_doc_no_id, sample_historical_documents
                )
                # Should complete without error
                assert result is not None

    def test_handles_recording_error_gracefully(
        self, mock_predictor, sample_input_document, sample_historical_documents
    ):
        """Pipeline handles document recording errors gracefully."""
        mock_predictor.record_document.side_effect = Exception("Recording failed")
        with patch("match_pipeline.unpack_attachments"):
            with patch(
                "match_pipeline.generate_no_match_report"
            ) as mock_no_match_report:
                mock_no_match_report.return_value = {
                    "id": "test",
                    "labels": [],
                    "deviations": [],
                }
                result = run_matching_pipeline(
                    mock_predictor, sample_input_document, sample_historical_documents
                )
                # Should return error report
                assert result is not None
                assert "pipeline-error" in result["labels"]
                assert any(
                    d["code"] == "pipeline-setup-error" for d in result["deviations"]
                )

    def test_calls_predict_pairings_with_correct_arguments(
        self, mock_predictor, sample_input_document, sample_historical_documents
    ):
        """Pipeline calls predict_pairings with correct arguments."""
        with patch("match_pipeline.unpack_attachments"):
            with patch("match_pipeline.generate_no_match_report", return_value={}):
                run_matching_pipeline(
                    mock_predictor, sample_input_document, sample_historical_documents
                )
                mock_predictor.predict_pairings.assert_called_once()
                args = mock_predictor.predict_pairings.call_args[0]
                assert args[0] == sample_input_document
                assert args[1] == sample_historical_documents

    def test_handles_prediction_error_gracefully(
        self, mock_predictor, sample_input_document, sample_historical_documents
    ):
        """Pipeline handles prediction errors gracefully."""
        mock_predictor.predict_pairings.side_effect = Exception("Prediction failed")
        with patch("match_pipeline.unpack_attachments"):
            with patch(
                "match_pipeline.generate_no_match_report"
            ) as mock_no_match_report:
                mock_no_match_report.return_value = {"id": "test", "labels": []}
                result = run_matching_pipeline(
                    mock_predictor, sample_input_document, sample_historical_documents
                )
                # Should return no-match report
                assert result is not None
                mock_no_match_report.assert_called()

    def test_generates_no_match_report_when_no_pairings(
        self, mock_predictor, sample_input_document, sample_historical_documents
    ):
        """Pipeline generates no-match report when no pairings found."""
        mock_predictor.predict_pairings.return_value = []
        with patch("match_pipeline.unpack_attachments"):
            with patch(
                "match_pipeline.generate_no_match_report"
            ) as mock_no_match_report:
                mock_no_match_report.return_value = {"id": "test", "labels": []}
                result = run_matching_pipeline(
                    mock_predictor, sample_input_document, sample_historical_documents
                )
                mock_no_match_report.assert_called_once()
                # Check that it was called with confidence value
                kwargs = mock_no_match_report.call_args[1]
                assert "no_match_confidence" in kwargs
                assert kwargs["no_match_confidence"] == CONFIDENT_NO_MATCH_CERTAINTY

    def test_processes_top_pairing_when_pairings_exist(
        self, mock_predictor, sample_input_document, sample_historical_documents
    ):
        """Pipeline processes top pairing when pairings are found."""
        mock_predictor.predict_pairings.return_value = [("doc-002", 0.9)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        with patch("match_pipeline.unpack_attachments"):
            with patch("match_pipeline.collect_document_deviations", return_value=[]):
                with patch("match_pipeline.get_document_items", return_value=[]):
                    with patch(
                        "match_pipeline.generate_match_report"
                    ) as mock_match_report:
                        mock_match_report.return_value = {
                            "id": "test",
                            "labels": ["matched"],
                        }
                        result = run_matching_pipeline(
                            mock_predictor,
                            sample_input_document,
                            sample_historical_documents,
                        )
                        mock_match_report.assert_called_once()

    def test_handles_matched_document_not_found_in_id2doc(
        self, mock_predictor, sample_input_document, sample_historical_documents
    ):
        """Pipeline handles case where matched document ID is not in id2doc."""
        mock_predictor.predict_pairings.return_value = [("missing-doc", 0.9)]
        mock_predictor.id2document = {"doc-001": sample_input_document}
        with patch("match_pipeline.unpack_attachments"):
            with patch(
                "match_pipeline.generate_no_match_report"
            ) as mock_no_match_report:
                mock_no_match_report.return_value = {
                    "id": "test",
                    "labels": [],
                    "deviations": [],
                }
                result = run_matching_pipeline(
                    mock_predictor, sample_input_document, sample_historical_documents
                )
                # Should generate no-match report with error
                assert result is not None
                assert "internal-error" in result["labels"]
                assert any(
                    d["code"] == "match-lookup-failed" for d in result["deviations"]
                )

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    def test_collects_document_deviations_for_match(
        self,
        mock_get_items,
        mock_collect_deviations,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline collects document-level deviations for matched pair."""
        mock_predictor.predict_pairings.return_value = [("doc-002", 0.9)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        mock_collect_deviations.return_value = []
        mock_get_items.return_value = []
        with patch("match_pipeline.generate_match_report", return_value={}):
            run_matching_pipeline(
                mock_predictor, sample_input_document, sample_historical_documents
            )
            mock_collect_deviations.assert_called_once()

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    def test_extracts_items_from_both_documents(
        self,
        mock_get_items,
        mock_collect_deviations,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline extracts items from both matched documents."""
        mock_predictor.predict_pairings.return_value = [("doc-002", 0.9)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        mock_collect_deviations.return_value = []
        mock_get_items.return_value = []
        with patch("match_pipeline.generate_match_report", return_value={}):
            run_matching_pipeline(
                mock_predictor, sample_input_document, sample_historical_documents
            )
            # get_document_items should be called twice (once for each document)
            assert mock_get_items.call_count == 2

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    @patch("match_pipeline.pair_document_items")
    def test_pairs_items_when_both_documents_have_items(
        self,
        mock_pair_items,
        mock_get_items,
        mock_collect_deviations,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline pairs items when both documents have items."""
        mock_predictor.predict_pairings.return_value = [("doc-002", 0.9)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        mock_collect_deviations.return_value = []
        mock_get_items.return_value = [
            {"item_index": 0, "document_kind": "invoice", "raw_item": {"fields": []}}
        ]
        mock_pair_items.return_value = []
        with patch("match_pipeline.generate_match_report", return_value={}):
            run_matching_pipeline(
                mock_predictor, sample_input_document, sample_historical_documents
            )
            mock_pair_items.assert_called_once()

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    def test_skips_item_pairing_when_no_items_in_doc1(
        self,
        mock_get_items,
        mock_collect_deviations,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline skips item pairing when doc1 has no items."""
        mock_predictor.predict_pairings.return_value = [("doc-002", 0.9)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        mock_collect_deviations.return_value = []
        mock_get_items.side_effect = [[], [{"item_index": 0}]]
        with patch("match_pipeline.generate_match_report", return_value={}):
            with patch("match_pipeline.pair_document_items") as mock_pair:
                run_matching_pipeline(
                    mock_predictor, sample_input_document, sample_historical_documents
                )
                mock_pair.assert_not_called()

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    def test_skips_item_pairing_when_no_items_in_doc2(
        self,
        mock_get_items,
        mock_collect_deviations,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline skips item pairing when doc2 has no items."""
        mock_predictor.predict_pairings.return_value = [("doc-002", 0.9)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        mock_collect_deviations.return_value = []
        mock_get_items.side_effect = [[{"item_index": 0}], []]
        with patch("match_pipeline.generate_match_report", return_value={}):
            with patch("match_pipeline.pair_document_items") as mock_pair:
                run_matching_pipeline(
                    mock_predictor, sample_input_document, sample_historical_documents
                )
                mock_pair.assert_not_called()

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    @patch("match_pipeline.pair_document_items")
    @patch("match_pipeline.collect_itempair_deviations")
    def test_collects_deviations_for_item_pairs(
        self,
        mock_collect_item_devs,
        mock_pair_items,
        mock_get_items,
        mock_collect_deviations,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline collects deviations for each item pair."""
        mock_predictor.predict_pairings.return_value = [("doc-002", 0.9)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        mock_collect_deviations.return_value = []
        mock_get_items.return_value = [
            {
                "item_index": 0,
                "document_kind": "invoice",
                "raw_item": {"fields": []},
                "matched": True,
            }
        ]
        mock_pair_items.return_value = [
            {
                "item1": {
                    "item_index": 0,
                    "document_kind": "invoice",
                    "raw_item": {"fields": []},
                },
                "item2": {
                    "item_index": 0,
                    "document_kind": "purchase-order",
                    "raw_item": {"fields": []},
                },
                "score": 0.9,
                "similarities": {},
            }
        ]
        mock_collect_item_devs.return_value = []
        with patch("match_pipeline.generate_match_report", return_value={}):
            run_matching_pipeline(
                mock_predictor, sample_input_document, sample_historical_documents
            )
            mock_collect_item_devs.assert_called()

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    @patch("match_pipeline.pair_document_items")
    def test_handles_item_pair_missing_raw_item_fields(
        self,
        mock_pair_items,
        mock_get_items,
        mock_collect_deviations,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline handles item pairs with missing raw_item fields."""
        mock_predictor.predict_pairings.return_value = [("doc-002", 0.9)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        mock_collect_deviations.return_value = []
        mock_get_items.return_value = [
            {"item_index": 0, "document_kind": "invoice", "matched": True}
        ]
        # Item pair without raw_item fields
        mock_pair_items.return_value = [
            {
                "item1": {"item_index": 0, "document_kind": "invoice"},
                "item2": {"item_index": 0, "document_kind": "purchase-order"},
                "score": 0.9,
            }
        ]
        with patch("match_pipeline.generate_match_report", return_value={}):
            # Should not raise exception
            result = run_matching_pipeline(
                mock_predictor, sample_input_document, sample_historical_documents
            )
            assert result is not None

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    @patch("match_pipeline.pair_document_items")
    @patch("match_pipeline.collect_itempair_deviations")
    def test_handles_deviation_collection_error_for_item_pair(
        self,
        mock_collect_item_devs,
        mock_pair_items,
        mock_get_items,
        mock_collect_deviations,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline handles errors during item pair deviation collection."""
        mock_predictor.predict_pairings.return_value = [("doc-002", 0.9)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        mock_collect_deviations.return_value = []
        mock_get_items.return_value = [
            {
                "item_index": 0,
                "document_kind": "invoice",
                "raw_item": {"fields": []},
                "matched": True,
            }
        ]
        mock_pair_items.return_value = [
            {
                "item1": {
                    "item_index": 0,
                    "document_kind": "invoice",
                    "raw_item": {"fields": []},
                },
                "item2": {
                    "item_index": 0,
                    "document_kind": "purchase-order",
                    "raw_item": {"fields": []},
                },
                "score": 0.9,
            }
        ]
        mock_collect_item_devs.side_effect = Exception("Deviation error")
        with patch("match_pipeline.generate_match_report", return_value={}):
            # Should not raise exception
            result = run_matching_pipeline(
                mock_predictor, sample_input_document, sample_historical_documents
            )
            assert result is not None

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    @patch("match_pipeline.pair_document_items")
    @patch("match_pipeline.create_item_unmatched_deviation")
    def test_creates_unmatched_deviations_for_unmatched_doc1_items(
        self,
        mock_create_unmatched,
        mock_pair_items,
        mock_get_items,
        mock_collect_deviations,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline creates unmatched deviations for unmatched items in doc1."""
        mock_predictor.predict_pairings.return_value = [("doc-002", 0.9)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        mock_collect_deviations.return_value = []
        # Doc1 has unmatched item
        mock_get_items.side_effect = [
            [
                {
                    "item_index": 0,
                    "document_kind": "invoice",
                    "raw_item": {"fields": []},
                    "matched": False,
                }
            ],
            [],
        ]
        mock_pair_items.return_value = []
        mock_create_unmatched.return_value = FieldDeviation(
            code="unmatched", message="test", severity=DeviationSeverity.HIGH
        )
        with patch("match_pipeline.generate_match_report", return_value={}):
            run_matching_pipeline(
                mock_predictor, sample_input_document, sample_historical_documents
            )
            mock_create_unmatched.assert_called()

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    @patch("match_pipeline.pair_document_items")
    @patch("match_pipeline.create_item_unmatched_deviation")
    def test_creates_unmatched_deviations_for_unmatched_doc2_items(
        self,
        mock_create_unmatched,
        mock_pair_items,
        mock_get_items,
        mock_collect_deviations,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline creates unmatched deviations for unmatched items in doc2."""
        mock_predictor.predict_pairings.return_value = [("doc-002", 0.9)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        mock_collect_deviations.return_value = []
        # Doc2 has unmatched item
        mock_get_items.side_effect = [
            [],
            [
                {
                    "item_index": 0,
                    "document_kind": "purchase-order",
                    "raw_item": {"fields": []},
                    "matched": False,
                }
            ],
        ]
        mock_pair_items.return_value = []
        mock_create_unmatched.return_value = FieldDeviation(
            code="unmatched", message="test", severity=DeviationSeverity.HIGH
        )
        with patch("match_pipeline.generate_match_report", return_value={}):
            run_matching_pipeline(
                mock_predictor, sample_input_document, sample_historical_documents
            )
            mock_create_unmatched.assert_called()

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    def test_handles_item_processing_error_gracefully(
        self,
        mock_get_items,
        mock_collect_deviations,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline handles item processing errors gracefully."""
        mock_predictor.predict_pairings.return_value = [("doc-002", 0.9)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        mock_collect_deviations.return_value = []
        mock_get_items.side_effect = Exception("Item extraction failed")
        with patch("match_pipeline.generate_match_report", return_value={}):
            # Should not raise exception
            result = run_matching_pipeline(
                mock_predictor, sample_input_document, sample_historical_documents
            )
            assert result is not None

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    def test_generates_match_report_with_correct_parameters(
        self,
        mock_get_items,
        mock_collect_deviations,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline generates match report with correct parameters."""
        match_confidence = 0.85
        mock_predictor.predict_pairings.return_value = [("doc-002", match_confidence)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        mock_collect_deviations.return_value = []
        mock_get_items.return_value = []
        with patch("match_pipeline.generate_match_report") as mock_match_report:
            mock_match_report.return_value = {"id": "test", "labels": ["matched"]}
            run_matching_pipeline(
                mock_predictor, sample_input_document, sample_historical_documents
            )
            # Check that match_confidence was passed
            kwargs = mock_match_report.call_args[1]
            assert "match_confidence" in kwargs
            assert kwargs["match_confidence"] == match_confidence

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    def test_handles_match_report_generation_error(
        self,
        mock_get_items,
        mock_collect_deviations,
        mock_unpack,
        mock_predictor,
        sample_input_document,
        sample_historical_documents,
    ):
        """Pipeline handles match report generation errors."""
        mock_predictor.predict_pairings.return_value = [("doc-002", 0.9)]
        mock_predictor.id2document = {
            "doc-001": sample_input_document,
            "doc-002": sample_historical_documents[0],
        }
        mock_collect_deviations.return_value = []
        mock_get_items.return_value = []
        with patch("match_pipeline.generate_match_report") as mock_match_report:
            mock_match_report.side_effect = Exception("Report generation failed")
            result = run_matching_pipeline(
                mock_predictor, sample_input_document, sample_historical_documents
            )
            # Should return error report
            assert result is not None
            assert "error" in result
            assert "report-generation-error" in result["labels"]

    def test_handles_no_match_report_generation_error(
        self, mock_predictor, sample_input_document, sample_historical_documents
    ):
        """Pipeline handles no-match report generation errors."""
        mock_predictor.predict_pairings.return_value = []
        with patch("match_pipeline.unpack_attachments"):
            with patch("match_pipeline.generate_no_match_report") as mock_no_match:
                mock_no_match.side_effect = Exception("No-match report failed")
                result = run_matching_pipeline(
                    mock_predictor, sample_input_document, sample_historical_documents
                )
                # Should return error report
                assert result is not None
                assert "error" in result
                assert "report-generation-error" in result["labels"]

    def test_confident_no_match_certainty_is_below_threshold(self):
        """CONFIDENT_NO_MATCH_CERTAINTY should be below NO_MATCH_CERTAINTY_THRESHOLD."""
        assert CONFIDENT_NO_MATCH_CERTAINTY < NO_MATCH_CERTAINTY_THRESHOLD

    def test_confident_no_match_certainty_value(self):
        """CONFIDENT_NO_MATCH_CERTAINTY should be 0.15."""
        assert CONFIDENT_NO_MATCH_CERTAINTY == 0.15


class TestRunMatchingPipelineIntegration:
    """Integration-style tests for run_matching_pipeline."""

    @pytest.fixture
    def mock_predictor(self, mocker):
        """Create a mock predictor for integration tests."""
        predictor = mocker.MagicMock()
        predictor.id2document = {}
        predictor.clear_documents = mocker.MagicMock()
        predictor.record_document = mocker.MagicMock(
            side_effect=lambda doc: predictor.id2document.update({doc["id"]: doc})
        )
        predictor.predict_pairings = mocker.MagicMock(return_value=[])
        return predictor

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.collect_document_deviations")
    @patch("match_pipeline.get_document_items")
    @patch("match_pipeline.pair_document_items")
    @patch("match_pipeline.collect_itempair_deviations")
    @patch("match_pipeline.generate_match_report")
    def test_full_pipeline_with_successful_match(
        self,
        mock_gen_match,
        mock_collect_item_devs,
        mock_pair_items,
        mock_get_items,
        mock_collect_devs,
        mock_unpack,
        mock_predictor,
    ):
        """Test full pipeline flow with successful match."""
        input_doc = {"id": "inv-001", "kind": "invoice"}
        hist_docs = [{"id": "po-001", "kind": "purchase-order"}]

        mock_predictor.predict_pairings.return_value = [("po-001", 0.9)]
        mock_predictor.id2document = {"inv-001": input_doc, "po-001": hist_docs[0]}
        mock_collect_devs.return_value = []
        mock_get_items.return_value = [
            {
                "item_index": 0,
                "document_kind": "invoice",
                "raw_item": {"fields": []},
                "matched": True,
            }
        ]
        mock_pair_items.return_value = [
            {
                "item1": {
                    "item_index": 0,
                    "document_kind": "invoice",
                    "raw_item": {"fields": []},
                },
                "item2": {
                    "item_index": 0,
                    "document_kind": "purchase-order",
                    "raw_item": {"fields": []},
                },
                "score": 0.9,
            }
        ]
        mock_collect_item_devs.return_value = []
        mock_gen_match.return_value = {"id": "report-001", "labels": ["matched"]}

        result = run_matching_pipeline(mock_predictor, input_doc, hist_docs)

        assert result is not None
        assert result["id"] == "report-001"
        mock_predictor.predict_pairings.assert_called_once()
        mock_gen_match.assert_called_once()

    @patch("match_pipeline.unpack_attachments")
    @patch("match_pipeline.generate_no_match_report")
    def test_full_pipeline_with_no_match(
        self, mock_gen_no_match, mock_unpack, mock_predictor
    ):
        """Test full pipeline flow with no match."""
        input_doc = {"id": "inv-001", "kind": "invoice"}
        hist_docs = [{"id": "po-001", "kind": "purchase-order"}]

        mock_predictor.predict_pairings.return_value = []
        mock_gen_no_match.return_value = {"id": "report-001", "labels": ["no-match"]}

        result = run_matching_pipeline(mock_predictor, input_doc, hist_docs)

        assert result is not None
        assert result["id"] == "report-001"
        mock_predictor.predict_pairings.assert_called_once()
        mock_gen_no_match.assert_called_once()
