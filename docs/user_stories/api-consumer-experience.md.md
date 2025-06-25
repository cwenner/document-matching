# Category 1: API Consumer Experience (Core Service Functionality)

These stories describe the primary interactions an API client will have with the matching service.

---

## Story 1.1: Request a Document Match and Receive Success Report(s)
*   **As an** API Consumer
*   **I want to** submit a primary document and a list of candidate documents (which can be of various types) to the matching service
*   **So that** I can receive one or more detailed match reports if suitable matches are found, enabling me to understand the relationships and act upon them.

    **Acceptance Criteria (ACs):**
    *   The service accepts a `POST` request to a designated `/` endpoint.
    *   The request payload includes a primary document and a list of candidate documents.
    *   If one or more valid matches are identified between the primary document and any of the diverse candidate documents, the service returns an HTTP `200 OK` status.
    *   The response body for a successful match is a JSON array containing one or more match reports, adhering to the V3 report specification.
    *   Each match report in the success response includes:
        *   Identifier of the primary document (e.g., the `id` field from its input structure).
        *   Identifier of the matched candidate document (e.g., the `id` field from its input structure).
        *   A confidence score for the match.
        *   Details of item-level pairings (if applicable, including item IDs and similarity scores).
        *   A list of identified deviations (e.g., differing amounts, quantities, descriptions) with severity levels between the matched documents/items.
    *   The service correctly processes and attempts to match the primary document against different document kinds provided within the `candidate-documents` list.
    *   The service responds to matching requests with up to 10 candidate documents in under 60 seconds (after service startup).

---

## Story 1.2: Receive Clear No-Match Report
*   **As an** API Consumer
*   **I want to** receive a clear and distinct no-match report when no suitable matches are found for my primary document within the provided candidates
*   **So that** I know the document could not be paired and can proceed with alternative actions.

    **Acceptance Criteria (ACs):**
    *   When a `POST` request is made to the `/` endpoint with a primary document and candidates, and no suitable matches are found:
        *   The service returns an HTTP `200 OK` status.
        *   The response body is a JSON structure (adhering to the V3 report specification) clearly indicating "no-match" (e.g., an empty array of match reports or a specific `status: "no-match"` field).

---

## Story 1.3: Handle Invalid Input Gracefully
*   **As an** API Consumer
*   **I want to** receive appropriate error responses (e.g., `400 Bad Request`) when I submit invalid or malformed requests
*   **So that** I can understand and correct my requests.

    **Acceptance Criteria (ACs):**
    *   If a `POST` request to the `/` endpoint has an invalid payload (e.g., missing `document` field, `candidate-documents` field not a list, unsupported document content):
        *   The service returns an appropriate `4xx` client error HTTP status code (e.g., `400`, `415`).
        *   The response body contains a clear, machine-readable error message describing the validation failure (potentially adhering to a common error schema if defined for the API ecosystem, e.g., RFC 7807 Problem Details).

---

## Story 1.4: Utilize Interpreted Data from Document Attachments
*   **As an** API Consumer
*   **I want** the matching service to automatically unpack and utilize `interpreted_data.json` and `interpreted_xml.json` from document attachments if present
*   **So that** structured data within these attachments can be leveraged for more accurate matching without manual pre-processing on my end.

    **Acceptance Criteria (ACs):**
    *   If a submitted primary document or candidate document contains attachments named `interpreted_data.json` or `interpreted_xml.json`, the service attempts to parse and use their content for matching.
    *   The matching logic can leverage data fields extracted from these interpreted files. (Note: Precedence if both file types are present for the same attachment will be defined in detailed design).
    *   If these files are not present or malformed, the service continues processing gracefully using other available document data.

---

## Story 1.5: Receive Detailed Deviation Information in Match Reports
*   **As an** API Consumer
*   **I want to** receive detailed deviation information whenever matches are found with discrepancies between documents
*   **So that** I can quickly identify and assess issues that require attention, such as price differences, quantity differences, or description mismatches.

    **Acceptance Criteria (ACs):**
    *   Each match report includes a "deviations" section listing document-level deviations.
    *   Each item pair in the match report includes an item-level "deviations" section where applicable.
    *   All deviations include standardized codes (e.g., "AMOUNTS_DIFFER", "QUANTITIES_DIFFER") indicating their type.
    *   All deviations include a severity level (e.g., "info", "low", "medium", "high").
    *   All deviations include human-readable messages explaining the discrepancy.
    *   All deviations include field references and values showing the actual data that differs.
    *   The overall match report includes a "deviation-severity" metric reflecting the highest deviation severity in the match.

---

## Story 1.6: Receive Match Certainty Metrics
*   **As an** API Consumer
*   **I want to** receive confidence metrics for each match and prediction about future matches
*   **So that** I can make informed decisions about which matches to trust and how to handle documents that might receive future matches.

    **Acceptance Criteria (ACs):**
    *   Each match report includes a "metrics" section with a "certainty" value indicating the confidence of the match.
    *   For relevant document types, the metrics include "has-future-match-certainty" values (e.g., "invoice-has-future-match-certainty").
    *   Item-level pairings include "item_unchanged_certainty" indicating confidence in the item match.
    *   All certainty metrics are expressed as decimal values between 0 and 1 (or percentage equivalents).
    *   The certainty metrics can be used to filter or flag matches that may require manual review.