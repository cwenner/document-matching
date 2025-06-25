# User Stories for Document Matching Service

This service aims to automatically identify relationships between different business documents (like invoices and purchase orders) to streamline reconciliation processes.

This directory contains the user stories that define the capabilities and requirements for the Document Matching Service. The service is designed to be stateless, producing match reports with an API given a document and a list of candidates.

## Structure

User stories are organized into the following categories, each in its own Markdown file:

1.  **`api-consumer-experience.md`**: Describes the primary interactions an API client will have with the matching service.
2.  **`operational-concerns.md`**: Covers stories crucial for deploying, monitoring, and maintaining the service.
3.  **`evaluation-framework.md`**: Outlines stories for a supporting tool used to evaluate the performance of the matching service by developers, data scientists, and QA engineers.
4.  **`developer-experience.md`**: Covers features and capabilities aimed at improving the developer experience, including debugging support, testing tools, and code organization.

## Format

Each story generally follows the format:

*   **Story Title**
*   **As a** [Role]
*   **I want to** [Goal]
*   **So that** [Benefit]
*   **Acceptance Criteria (ACs):** Bullet points outlining what needs to be true for the story to be considered complete.

These user stories will serve as the foundation for more detailed feature files (e.g., Gherkin) for automated testing.