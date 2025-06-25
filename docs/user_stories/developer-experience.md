# Category 4: Developer Experience

These stories describe features and capabilities aimed at improving the developer experience when working with the matching service.

---

## Story 4.1: Enable Debugging Support
*   **As a** Developer
*   **I want to** enable a debugging mode when working with the matching service
*   **So that** I can trace execution flow and diagnose unexpected behaviors.

    **Acceptance Criteria (ACs):**
    *   The service provides a debug flag that can be enabled via configuration or environment variable.
    *   When debug mode is enabled, detailed information about internal operations is logged.
    *   Debug output includes timing information for key operations and detailed matching steps.
    *   Debug mode can be enabled without restarting the service.

---

## Story 4.5: Ad-hoc API Testing and Validation
*   **As a** Developer
*   **I want to** easily send ad-hoc requests to the matching service with documents from local files and optionally validate responses against expected outputs
*   **So that** I can quickly test service functionality during development and verify correct behavior.

    **Acceptance Criteria (ACs):**
    *   A simple utility is available that accepts paths to local JSON files for primary and candidate documents.
    *   The utility sends requests to a configurable service endpoint and displays formatted responses.
    *   The utility supports overriding key request parameters via command-line arguments.
    *   The utility optionally validates responses against expected output files and reports discrepancies.
    *   The utility supports switching between different deployment environments (e.g., local, dev, staging).

---

## Story 4.2: Compare Test Results Against Expected Outputs
*   **As a** Developer
*   **I want to** compare matching results against expected outputs
*   **So that** I can efficiently validate service behavior before committing changes.

    **Acceptance Criteria (ACs):**
    *   A testing utility is available that accepts test inputs and expected outputs.
    *   The utility reports whether actual outputs match expected outputs.
    *   Differences between expected and actual outputs are highlighted in the report.
    *   The utility provides a summary showing pass/fail counts.
