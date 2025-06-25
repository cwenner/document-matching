# Category 3: Evaluation Framework (Supporting Tool)

These stories describe a supporting tool for evaluating the performance of the matching service. This tool is intended for use by evaluators, data scientists, QA engineers, and developers during both development and quality assurance processes.

---

## Story 3.1: Load Evaluation Dataset
*   **As an** Evaluator (e.g., Developer, Data Scientist, QA Engineer)
*   **I want to** load an evaluation dataset consisting of primary documents, their associated candidate documents, and the expected (ground truth) pairings from a structured file (e.g., JSON)
*   **So that** I can systematically test the matching service's performance.

    **Acceptance Criteria (ACs):**
    *   The evaluation script accepts a path to a dataset file.
    *   The script can parse a defined structure containing evaluation cases (primary doc, candidates, expected outcomes).

---

## Story 3.2: Evaluate Matching Performance
*   **As an** Evaluator (e.g., Developer, Data Scientist, QA Engineer)
*   **I want to** run the evaluation by having the script make calls to a running matching service instance
*   **So that** I can test the end-to-end behavior of the deployed service.

    **Acceptance Criteria (ACs):**
    *   The script can be configured with the target service endpoint.
    *   For each case, the script sends a request to the service and captures the response.

---

## Story 3.3: Simulate History Building for Evaluation Context
*   **As an** Evaluator
*   **I want to** specify a portion of the evaluation dataset to be processed by the *evaluation script* to build a "history" of candidate documents *for the evaluation run itself* before starting the actual tested predictions
*   **So that** the matching context for tested documents is more realistic, simulating a stream where candidates are drawn from previously "seen" documents within the evaluation.

    **Acceptance Criteria (ACs):**
    *   The evaluation script allows specifying a number or fraction of initial dataset entries to be treated as "history builders."
    *   Documents from this initial portion are added to a candidate pool maintained by the script.
    *   Subsequent documents being tested for matching can use this script-managed candidate pool in addition to or instead of candidates explicitly listed for them in the dataset.
    *   This does not imply the service itself is stateful; the script manages this state for evaluation realism.

---

## Story 3.4: Receive Comprehensive Performance Metrics
*   **As an** Evaluator
*   **I want to** receive a report from the evaluation script with detailed performance metrics (e.g., True Positives, False Positives, True Negatives, False Negatives, Precision, Recall, F1-score)
*   **So that** I can thoroughly assess the matching accuracy and identify areas for improvement.

    **Acceptance Criteria (ACs):**
    *   The script compares actual responses/predictions against ground truth.
    *   The script calculates and displays overall TP, FP, TN, FN, Precision, Recall, F1-score.

---

## Story 3.5: Breakdown and Slice Performance Metrics
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

## Story 3.6: Detailed Diagnostics for Misclassifications
*   **As an** Evaluator
*   **I want** the evaluation script to provide detailed diagnostic information for false negatives (missed matches) and false positives (incorrect matches)
*   **So that** I can more easily diagnose why certain expected pairings were not made or why incorrect pairings occurred.

    **Acceptance Criteria (ACs):**
    *   For false negatives, the report includes details about the primary document and the missed expected candidate(s).
    *   For false positives, the report includes details about the primary document and the incorrectly matched candidate(s), and potentially why the service thought it was a match (if inferable from service output or direct logic output).
    *   This information helps pinpoint issues in the matching logic or feature engineering.

---

## Story 3.7: Save Evaluation Results
*   **As an** Evaluator
*   **I want** the evaluation script to save the detailed results (individual predictions vs. ground truth) and summary metrics to a file (e.g., JSON, CSV)
*   **So that** I can archive, review, and compare evaluation outcomes over time.

    **Acceptance Criteria (ACs):**
    *   The script allows specifying an output file path.
    *   The output file contains summary metrics and detailed per-case results.
