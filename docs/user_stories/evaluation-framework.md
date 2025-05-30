# Category 3: Evaluation Framework (Supporting Tool)

These stories describe a supporting tool for evaluating the performance of the matching service.

---

## Story 3.1: Load Evaluation Dataset
*   **As an** Evaluator (e.g., Data Scientist, QA Engineer)
*   **I want to** load an evaluation dataset consisting of primary documents, their associated candidate documents, and the expected (ground truth) pairings from a structured file (e.g., JSON)
*   **So that** I can systematically test the matching service's performance.

    **Acceptance Criteria (ACs):**
    *   The evaluation script accepts a path to a dataset file.
    *   The script can parse a defined structure containing evaluation cases (primary doc, candidates, expected outcomes).

---

## Story 3.2: Evaluate Matching Performance via API Calls
*   **As an** Evaluator
*   **I want to** run the evaluation by having the script make API calls to a running matching service instance
*   **So that** I can test the end-to-end behavior of the deployed service.

    **Acceptance Criteria (ACs):**
    *   The script can be configured with the target service API endpoint.
    *   For each case, the script sends a request to the service and captures the response.

---

## Story 3.3: Evaluate Matching Performance via Direct Logic Calls
*   **As an** Evaluator
*   **I want** the evaluation script to optionally support making direct calls to the core matching logic (bypassing the API)
*   **So that** I can test algorithms in isolation, potentially with higher performance for very large datasets, or with specific model paths not exposed via API config, facilitating easier debugging of the core logic.

    **Acceptance Criteria (ACs):**
    *   The script provides a mode to invoke the matching logic directly (e.g., as a library call).
    *   This mode allows specification of any necessary local resources (e.g., model files, configurations for the core logic).
    *   Results from direct calls (e.g., predicted pairings, scores) are in a format that can be compared to API results for evaluation metrics.
    *   The core matching logic is designed to be callable independently of the API framework.

---

## Story 3.4: Simulate History Building for Evaluation Context
*   **As an** Evaluator
*   **I want to** specify a portion of the evaluation dataset to be processed by the *evaluation script* to build a "history" of candidate documents *for the evaluation run itself* before starting the actual tested predictions
*   **So that** the matching context for tested documents is more realistic, simulating a stream where candidates are drawn from previously "seen" documents within the evaluation.

    **Acceptance Criteria (ACs):**
    *   The evaluation script allows specifying a number or fraction of initial dataset entries to be treated as "history builders."
    *   Documents from this initial portion are added to a candidate pool maintained by the script.
    *   Subsequent documents being tested for matching can use this script-managed candidate pool in addition to or instead of candidates explicitly listed for them in the dataset.
    *   This does not imply the service itself is stateful; the script manages this state for evaluation realism.

---

## Story 3.5: Receive Comprehensive Performance Metrics
*   **As an** Evaluator
*   **I want to** receive a report from the evaluation script with detailed performance metrics (e.g., True Positives, False Positives, True Negatives, False Negatives, Precision, Recall, F1-score)
*   **So that** I can thoroughly assess the matching accuracy and identify areas for improvement.

    **Acceptance Criteria (ACs):**
    *   The script compares actual responses/predictions against ground truth.
    *   The script calculates and displays overall TP, FP, TN, FN, Precision, Recall, F1-score.

---

## Story 3.6: Breakdown and Slice Performance Metrics
*   **As an** Evaluator
*   **I want** the evaluation report to break down performance metrics (e.g., accuracy, precision, recall, F1-score) by various configurable facets present in the dataset
*   **So that** I can identify performance variations across different document kinds, specific business scenarios, or error patterns (e.g., primary document kind vs. candidate document kind).

    **Acceptance Criteria (ACs):**
    *   The evaluation script allows specifying which dataset fields should be used for slicing and dicing metrics (e.g., via command-line argument or configuration).
    *   If the dataset contains categorization information (e.g., `primary_document_kind`, `candidate_document_kind`, `site_id`, `scenario_type`), the script can generate performance metrics per unique combination of these facets.
    *   The summary report includes these per-facet breakdowns alongside overall metrics.
    *   The report clearly shows accuracy/error rates for specific pairing types, such as when a primary "Invoice" is tested against candidate "Purchase Orders" versus when tested against candidate "Delivery Receipts."
    *   The script supports analyzing metrics for subsets of data based on specified criteria (e.g., "only for site X" or "only for high-value transactions" if such data exists in the dataset).

---

## Story 3.7: Detailed Diagnostics for Misclassifications
*   **As an** Evaluator
*   **I want** the evaluation script to provide detailed diagnostic information for false negatives (missed matches) and false positives (incorrect matches)
*   **So that** I can more easily diagnose why certain expected pairings were not made or why incorrect pairings occurred.

    **Acceptance Criteria (ACs):**
    *   For false negatives, the report includes details about the primary document and the missed expected candidate(s).
    *   For false positives, the report includes details about the primary document and the incorrectly matched candidate(s), and potentially why the service thought it was a match (if inferable from service output or direct logic output).
    *   This information helps pinpoint issues in the matching logic or feature engineering.

---

## Story 3.8: Save Evaluation Results
*   **As an** Evaluator
*   **I want** the evaluation script to save the detailed results (individual predictions vs. ground truth) and summary metrics to a file (e.g., JSON, CSV)
*   **So that** I can archive, review, and compare evaluation outcomes over time.

    **Acceptance Criteria (ACs):**
    *   The script allows specifying an output file path.
    *   The output file contains summary metrics and detailed per-case results.

---

## Story 3.9: Control Evaluation Script Verbosity
*   **As an** Evaluator
*   **I want to** control the verbosity of the evaluation script's console output (e.g., summary vs. detailed logs during execution)
*   **So that** I can get the level of information appropriate for my current task.

    **Acceptance Criteria (ACs):**
    *   The script provides a command-line option or configuration to set verbosity (e.g., quiet, normal, verbose/debug).
    *   The amount of console output during script execution corresponds to the selected verbosity level.