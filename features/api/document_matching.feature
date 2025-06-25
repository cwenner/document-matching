# To be implemented
# We leave it out for now to make sure everything else is in place.

# @api @core_matching
# Feature: Document Matching API - Core Functionality
#   As an API Consumer
#   I want to interact with the document matching service
#   So that I can identify relationships between my business documents.
# 

  Background:
    Given the matching service is expected to be running at "http://localhost:8000"

#   Scenario: Handle invalid request payload gracefully
#     Given I have an invalid request payload defined as "payload_invalid_structure.json"
#     When I send a POST request to "/" with the invalid payload
#     Then the response status code should be 400
#     And the response body should contain a clear, machine-readable error message
# 
#   Scenario: Utilize interpreted data from document attachments for matching
#     Given I have a primary document "primary_doc_with_attachment.json" that includes an "interpreted_data.json" attachment
#     And I have a list of candidate documents "candidates_for_attachment_test.json"
#     When I send a POST request to "/" with the primary document "primary_doc_with_attachment.json" and candidates "candidates_for_attachment_test.json"
#     Then the response status code should be 200
#     And the matching process should have considered data from the "interpreted_data.json" attachment
#     # Verification for the above step might involve checking logs, mock interactions, or specific match details influenced by attachment data.
