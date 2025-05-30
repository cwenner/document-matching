# To be implemented
# We leave it out for now to make sure everything else is in place.

# @api @core_matching
# Feature: Document Matching API - Core Functionality
#   As an API Consumer
#   I want to interact with the document matching service
#   So that I can identify relationships between my business documents.
# 
#   Background:
#     Given the matching service is expected to be running at "http://localhost:8000"
#     # The following are placeholders for actual test data files or setup steps
#     # e.g., Given I have a primary document "test_data/primary_doc_A.json"
#     # e.g., Given I have candidate documents "test_data/candidates_for_A.json"
# 
#   Scenario: Successfully match a primary document with one or more candidates
#     Given I have a primary document defined as "primary_doc_good_match.json"
#     And I have a list of candidate documents defined as "candidates_good_match.json"
#     When I send a POST request to "/match" with the primary document and candidate documents
#     Then the response status code should be 200
#     And the response body should be a JSON array of match reports
#     And each match report in the response should contain "primary_document_id", "candidate_document_id", and "confidence_score"
#     # Optional: And each match report can contain "item_pairings" and "deviations"
# 
#   Scenario: Receive a clear no-match report when no suitable matches are found
#     Given I have a primary document defined as "primary_doc_no_match.json"
#     And I have a list of candidate documents defined as "candidates_no_match.json"
#     When I send a POST request to "/match" with the primary document and candidate documents
#     Then the response status code should be 200
#     And the response body should indicate no matches were found (e.g., an empty JSON array or a specific status)
# 
#   Scenario: Handle invalid request payload gracefully
#     Given I have an invalid request payload defined as "payload_invalid_structure.json"
#     When I send a POST request to "/match" with the invalid payload
#     Then the response status code should be 400 # Or another appropriate 4xx client error
#     And the response body should contain a clear, machine-readable error message
# 
#   Scenario: Utilize interpreted data from document attachments for matching
#     Given I have a primary document "primary_doc_with_attachment.json" that includes an "interpreted_data.json" attachment
#     And I have a list of candidate documents "candidates_for_attachment_test.json"
#     When I send a POST request to "/match" with the primary document "primary_doc_with_attachment.json" and candidates "candidates_for_attachment_test.json"
#     Then the response status code should be 200
#     And the matching process should have considered data from the "interpreted_data.json" attachment
#     # Verification for the above step might involve checking logs, mock interactions, or specific match details influenced by attachment data.
