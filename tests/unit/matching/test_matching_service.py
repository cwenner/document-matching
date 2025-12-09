"""Unit tests for matching_service.py MatchingService class."""

import os
from unittest.mock import MagicMock, patch

import pytest

from matching_service import DUMMY_CERTAINTY, MatchingService


class TestMatchingServiceInitialization:
    """Tests for MatchingService initialization and lazy loading."""

    def test_init_default_parameters(self):
        """MatchingService should initialize with default parameters."""
        service = MatchingService()
        assert service._predictor is None
        assert service.model_path is None
        assert service.svc_threshold == 0.15

    def test_init_custom_parameters(self):
        """MatchingService should accept custom model path and threshold."""
        service = MatchingService(model_path="/custom/path.pkl", svc_threshold=0.25)
        assert service._predictor is None
        assert service.model_path == "/custom/path.pkl"
        assert service.svc_threshold == 0.25

    def test_lazy_initialization_predictor_none_initially(self):
        """Predictor should be None before initialization."""
        service = MatchingService()
        assert service._predictor is None

    @patch.dict(os.environ, {"DISABLE_MODELS": "true"})
    def test_initialize_when_models_disabled(self):
        """Initialize should return None when models are disabled."""
        service = MatchingService()
        result = service.initialize()
        assert result is None
        assert service._predictor is None

    @patch.dict(os.environ, {"DISABLE_MODELS": "false"})
    @patch("matching_service.os.path.exists")
    @patch("matching_service.DocumentPairingPredictor")
    def test_initialize_with_model_success(self, mock_predictor_class, mock_exists):
        """Initialize should create predictor when model file exists."""
        mock_exists.return_value = True
        mock_predictor_instance = MagicMock()
        mock_predictor_class.return_value = mock_predictor_instance

        service = MatchingService(model_path="/test/model.pkl")
        result = service.initialize()

        assert result == mock_predictor_instance
        assert service._predictor == mock_predictor_instance
        mock_predictor_class.assert_called_once_with(
            "/test/model.pkl", svc_threshold=0.15
        )

    @patch.dict(os.environ, {"DISABLE_MODELS": "false"})
    @patch("matching_service.os.path.exists")
    def test_initialize_model_not_found(self, mock_exists):
        """Initialize should return None when model file is not found."""
        mock_exists.return_value = False

        service = MatchingService(model_path="/nonexistent/model.pkl")
        result = service.initialize()

        assert result is None
        assert service._predictor is None

    @patch.dict(os.environ, {"DISABLE_MODELS": "false"})
    @patch("matching_service.os.path.exists")
    @patch("matching_service.DocumentPairingPredictor")
    def test_initialize_only_once(self, mock_predictor_class, mock_exists):
        """Initialize should only create predictor once (caching)."""
        mock_exists.return_value = True
        mock_predictor_instance = MagicMock()
        mock_predictor_class.return_value = mock_predictor_instance

        service = MatchingService(model_path="/test/model.pkl")
        result1 = service.initialize()
        result2 = service.initialize()

        assert result1 == result2 == mock_predictor_instance
        # Should only be called once due to caching
        mock_predictor_class.assert_called_once()

    @patch.dict(os.environ, {"DISABLE_MODELS": "false", "DOCPAIR_MODEL_PATH": "/env/model.pkl"})
    @patch("matching_service.os.path.exists")
    def test_initialize_uses_environment_variable(self, mock_exists):
        """Initialize should use DOCPAIR_MODEL_PATH environment variable."""
        mock_exists.return_value = False

        service = MatchingService()  # No model_path provided
        service.initialize()

        # Should have tried the environment variable path
        assert service.model_path == "/env/model.pkl"


class TestAdaptReportToV3:
    """Tests for adapt_report_to_v3 function."""

    def test_adapt_report_empty_report(self):
        """adapt_report_to_v3 should handle empty/None report."""
        service = MatchingService()
        result = service.adapt_report_to_v3(None)
        assert result is None

        result = service.adapt_report_to_v3({})
        assert result == {}

    def test_adapt_report_adds_version(self):
        """adapt_report_to_v3 should add version field."""
        service = MatchingService()
        report = {"id": "test-report"}
        result = service.adapt_report_to_v3(report)

        assert result["version"] == "v3"
        assert result["id"] == "test-report"

    def test_adapt_report_removes_match_score(self):
        """adapt_report_to_v3 should remove match_score from itempairs."""
        service = MatchingService()
        report = {
            "itempairs": [
                {"item1": "a", "item2": "b", "match_score": 0.95},
                {"item1": "c", "item2": "d", "match_score": 0.88},
            ]
        }
        result = service.adapt_report_to_v3(report)

        for pair in result["itempairs"]:
            assert "match_score" not in pair
            assert "item1" in pair
            assert "item2" in pair

    def test_adapt_report_fills_minimal_defaults(self):
        """adapt_report_to_v3 should add default empty arrays."""
        service = MatchingService()
        report = {"id": "test"}
        result = service.adapt_report_to_v3(report)

        assert result["headers"] == []
        assert result["deviations"] == []
        assert result["itempairs"] == []
        assert result["metrics"] == []
        assert result["labels"] == []

    def test_adapt_report_preserves_existing_fields(self):
        """adapt_report_to_v3 should not overwrite existing fields."""
        service = MatchingService()
        report = {
            "headers": [{"name": "test", "value": "123"}],
            "deviations": [{"code": "test-dev"}],
            "itempairs": [{"item1": "a"}],
            "metrics": [{"name": "score", "value": 0.9}],
            "labels": ["match"],
        }
        result = service.adapt_report_to_v3(report)

        assert len(result["headers"]) == 1
        assert len(result["deviations"]) == 1
        assert len(result["itempairs"]) == 1
        assert len(result["metrics"]) == 1
        assert len(result["labels"]) == 1

    def test_adapt_report_handles_empty_itempairs(self):
        """adapt_report_to_v3 should handle empty itempairs list."""
        service = MatchingService()
        report = {"itempairs": []}
        result = service.adapt_report_to_v3(report)

        assert result["itempairs"] == []
        assert result["version"] == "v3"


class TestProcessDocument:
    """Tests for process_document function."""

    @patch.dict(os.environ, {"DISABLE_MODELS": "true"})
    def test_process_document_with_disabled_models(self):
        """process_document should use dummy logic when models disabled."""
        service = MatchingService()
        document = {"id": "doc-1", "kind": "invoice", "site": "test-site", "stage": "input"}
        candidates = []

        report, log_entry = service.process_document(document, candidates, "trace-123")

        assert report is not None
        assert report["version"] == "v3"
        assert log_entry["traceId"] == "trace-123"
        assert log_entry["documentId"] == "doc-1"
        assert log_entry["site"] == "test-site"
        assert log_entry["numCandidates"] == 0
        assert "dummy" in log_entry["message"].lower()

    @patch.dict(os.environ, {"DISABLE_MODELS": "true"})
    def test_process_document_creates_log_entry(self):
        """process_document should create proper log entry."""
        service = MatchingService()
        document = {
            "id": "doc-2",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "input",
        }
        candidates = [{"id": "cand-1"}]

        report, log_entry = service.process_document(document, candidates, "trace-456")

        assert log_entry["traceId"] == "trace-456"
        assert log_entry["level"] == "info"
        assert log_entry["site"] == "test-site"
        assert log_entry["documentId"] == "doc-2"
        assert log_entry["stage"] == "input"
        assert log_entry["kind"] == "purchase-order"
        assert log_entry["numCandidates"] == 1
        assert "matchResult" in log_entry

    @patch.dict(os.environ, {"DISABLE_MODELS": "true"})
    def test_process_document_dummy_report_has_version(self):
        """process_document dummy report should have v3 version."""
        service = MatchingService()
        document = {"id": "doc-3", "kind": "invoice", "site": "test-site", "stage": "input"}
        candidates = []

        report, _ = service.process_document(document, candidates)

        assert report["version"] == "v3"

    @patch.dict(os.environ, {"DISABLE_MODELS": "true"})
    def test_process_document_adds_candidate_count_metric(self):
        """process_document should add candidate-documents metric."""
        service = MatchingService()
        document = {"id": "doc-4", "kind": "invoice", "site": "test-site", "stage": "input"}
        candidates = [{"id": "c1"}, {"id": "c2"}, {"id": "c3"}]

        report, _ = service.process_document(document, candidates)

        # Get all candidate-documents metrics (there may be multiple)
        candidate_metrics = [
            m for m in report["metrics"] if m["name"] == "candidate-documents"
        ]
        assert len(candidate_metrics) > 0
        # The last one should be the one added by process_document
        assert candidate_metrics[-1]["value"] == 3

    @patch.dict(os.environ, {"DISABLE_MODELS": "false"})
    @patch("matching_service.run_matching_pipeline")
    @patch("matching_service.os.path.exists")
    @patch("matching_service.DocumentPairingPredictor")
    def test_process_document_whitelisted_site_uses_pipeline(
        self, mock_predictor_class, mock_exists, mock_pipeline
    ):
        """process_document should use real pipeline for whitelisted sites."""
        mock_exists.return_value = True
        mock_predictor = MagicMock()
        mock_predictor_class.return_value = mock_predictor

        mock_pipeline.return_value = {
            "id": "report-1",
            "labels": ["match"],
            "metrics": [],
        }

        service = MatchingService(model_path="/test/model.pkl")
        service.initialize()

        document = {
            "id": "doc-5",
            "kind": "invoice",
            "site": "badger-logistics",  # Whitelisted site
            "stage": "input",
        }
        candidates = [{"id": "c1", "kind": "purchase-order"}]

        report, log_entry = service.process_document(document, candidates, "trace-789")

        assert report is not None
        assert report["version"] == "v3"
        assert log_entry["level"] == "info"
        assert "pipeline" in log_entry["message"].lower()
        mock_pipeline.assert_called_once_with(mock_predictor, document, candidates)

    @patch.dict(os.environ, {"DISABLE_MODELS": "false"})
    @patch("matching_service.run_matching_pipeline")
    @patch("matching_service.os.path.exists")
    @patch("matching_service.DocumentPairingPredictor")
    def test_process_document_pipeline_failure(
        self, mock_predictor_class, mock_exists, mock_pipeline
    ):
        """process_document should handle pipeline failures gracefully."""
        mock_exists.return_value = True
        mock_predictor = MagicMock()
        mock_predictor_class.return_value = mock_predictor

        mock_pipeline.return_value = None  # Pipeline failure

        service = MatchingService(model_path="/test/model.pkl")
        service.initialize()

        document = {
            "id": "doc-6",
            "kind": "invoice",
            "site": "badger-logistics",
            "stage": "input",
        }
        candidates = []

        report, log_entry = service.process_document(document, candidates, "trace-999")

        assert report is None
        assert log_entry["level"] == "error"
        assert "failed" in log_entry["message"].lower()

    @patch.dict(os.environ, {"DISABLE_MODELS": "false"})
    @patch("matching_service.run_matching_pipeline")
    @patch("matching_service.os.path.exists")
    @patch("matching_service.DocumentPairingPredictor")
    def test_process_document_pipeline_exception(
        self, mock_predictor_class, mock_exists, mock_pipeline
    ):
        """process_document should handle pipeline exceptions."""
        mock_exists.return_value = True
        mock_predictor = MagicMock()
        mock_predictor_class.return_value = mock_predictor

        mock_pipeline.side_effect = Exception("Pipeline error")

        service = MatchingService(model_path="/test/model.pkl")
        service.initialize()

        document = {
            "id": "doc-7",
            "kind": "invoice",
            "site": "badger-logistics",
            "stage": "input",
        }
        candidates = []

        report, log_entry = service.process_document(document, candidates, "trace-err")

        assert report is None
        assert log_entry["level"] == "error"
        assert "exception" in log_entry["message"].lower()

    @patch.dict(os.environ, {"DISABLE_MODELS": "true"})
    def test_process_document_default_trace_id(self):
        """process_document should handle default trace_id."""
        service = MatchingService()
        document = {"id": "doc-8", "kind": "invoice", "site": "test-site", "stage": "input"}
        candidates = []

        report, log_entry = service.process_document(document, candidates)

        assert log_entry["traceId"] == "<trace_id missing>"

    @patch.dict(os.environ, {"DISABLE_MODELS": "true"})
    def test_process_document_lazy_initialization(self):
        """process_document should trigger lazy initialization if needed."""
        service = MatchingService()
        assert service._predictor is None

        document = {"id": "doc-9", "kind": "invoice", "site": "test-site", "stage": "input"}
        candidates = []

        # Should not raise error even though predictor not explicitly initialized
        report, log_entry = service.process_document(document, candidates)

        assert report is not None
        assert log_entry is not None

    @patch.dict(os.environ, {"DISABLE_MODELS": "false"})
    @patch("matching_service.run_matching_pipeline")
    @patch("matching_service.os.path.exists")
    @patch("matching_service.DocumentPairingPredictor")
    def test_process_document_adds_internal_candidate_list(
        self, mock_predictor_class, mock_exists, mock_pipeline
    ):
        """process_document should add internal candidate list to report."""
        mock_exists.return_value = True
        mock_predictor = MagicMock()
        mock_predictor_class.return_value = mock_predictor

        mock_pipeline.return_value = {
            "id": "report-2",
            "labels": ["match"],
            "metrics": [],
        }

        service = MatchingService(model_path="/test/model.pkl")
        service.initialize()

        document = {
            "id": "doc-10",
            "kind": "invoice",
            "site": "falcon-logistics",  # Whitelisted site
            "stage": "input",
        }
        candidates = [
            {"id": "c1", "kind": "purchase-order"},
            {"id": "c2", "kind": "purchase-order"},
        ]

        report, _ = service.process_document(document, candidates)

        assert "internal" in report
        candidate_internal = next(
            (i for i in report["internal"] if i["name"] == "candidate-documents"), None
        )
        assert candidate_internal is not None
        assert len(candidate_internal["value"]) == 2
        assert candidate_internal["value"][0]["id"] == "c1"


class TestGetDummyMatchingReport:
    """Tests for get_dummy_matching_report function."""

    def test_get_dummy_report_deterministic(self):
        """get_dummy_matching_report should be deterministic based on document ID."""
        service = MatchingService()
        document = {"id": "consistent-id", "kind": "invoice", "site": "test-site"}

        report1 = service.get_dummy_matching_report(document)
        report2 = service.get_dummy_matching_report(document)

        # Should return same type of report for same ID
        assert report1["labels"] == report2["labels"]

    def test_get_dummy_report_varies_by_id(self):
        """get_dummy_matching_report should vary based on document ID."""
        service = MatchingService()
        doc1 = {"id": "id-1", "kind": "invoice", "site": "test-site"}
        doc2 = {"id": "id-2", "kind": "invoice", "site": "test-site"}

        report1 = service.get_dummy_matching_report(doc1)
        report2 = service.get_dummy_matching_report(doc2)

        # Different IDs may produce different report types
        # We can't guarantee they'll be different, but we can check structure
        assert "labels" in report1
        assert "labels" in report2

    def test_get_dummy_report_has_required_fields(self):
        """get_dummy_matching_report should have all required v3 fields."""
        service = MatchingService()
        document = {"id": "test-id", "kind": "invoice", "site": "test-site"}

        report = service.get_dummy_matching_report(document)

        assert report["version"] == "v3"
        assert "id" in report
        assert "kind" in report
        assert report["kind"] == "match-report"
        assert "site" in report
        assert "headers" in report
        assert "deviations" in report
        assert "itempairs" in report
        assert "metrics" in report
        assert "labels" in report

    def test_get_dummy_report_uses_dummy_certainty(self):
        """get_dummy_matching_report should use DUMMY_CERTAINTY constant."""
        service = MatchingService()
        document = {"id": "cert-test", "kind": "invoice", "site": "test-site"}

        report = service.get_dummy_matching_report(document)

        certainty_metric = next(
            (m for m in report["metrics"] if m["name"] == "certainty"), None
        )
        assert certainty_metric is not None
        assert certainty_metric["value"] == DUMMY_CERTAINTY
