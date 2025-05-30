# Category 4: Developer Test Client (Optional Supporting Tool)

These stories describe a simple client for ad-hoc testing by developers.

---

## Story 4.1: Send Ad-hoc Test Requests from Local Files
*   **As a** Developer
*   **I want to** use a simple client script to easily send ad-hoc `POST` requests with a-sample primary document and candidate documents (e.g., from local JSON files) to the matching service API
*   **So that** I can quickly test the service's basic functionality and observe its responses during development.

    **Acceptance Criteria (ACs):**
    *   The script accepts paths to local JSON files for primary and candidate documents.
    *   The script sends a `POST` request to the configured service API endpoint.

---

## Story 4.2: View Full API Responses in Console
*   **As a** Developer
*   **I want** the test client to display the full API response, including status code, headers (if relevant), and the formatted JSON body
*   **So that** I can thoroughly inspect the service's output and debug any issues immediately.

    **Acceptance Criteria (ACs):**
    *   The client script prints the HTTP status code and formatted JSON response body.

---

## Story 4.3: Override Key Parameters for Test Client Requests
*   **As a** Developer
*   **I want to** easily override key parameters (e.g., 'site' in the primary document, or a flag to simulate specific conditions if the client supports it) via command-line arguments when using the test client
*   **So that** I can quickly test different service behaviors or input variations without modifying the underlying JSON files or backend service configurations extensively.

    **Acceptance Criteria (ACs):**
    *   The test client script supports command-line arguments to override specific fields in the request payload (e.g., `--site <new_site_value>`).
    *   The request sent to the service reflects these overrides.

---

## Story 4.4: Easily Switch Target Service Environments
*   **As a** Developer
*   **I want** the test client to easily allow me to switch the target service API endpoint (e.g., by specifying a base URL or an environment name like 'dev', 'staging', 'local')
*   **So that** I can test against different deployed instances of the service without manually changing URLs in multiple places or scripts.

    **Acceptance Criteria (ACs):**
    *   The test client accepts a parameter (e.g., command-line argument `--target-env <env_name>` or `--base-url <url>`) to specify the service endpoint.
    *   The client uses the specified endpoint for its API requests.
    *   Default target can be configured if no parameter is provided (e.g., localhost).