@operational @stateless @story-2.5
Feature: Statelessness Assurance
  As an Architect or Developer/QA
  I want to ensure that the service is stateless regarding match requests
  So that it can be scaled horizontally without issues and identical requests produce identical results

  Background:
    Given the document matching service is available

  @stateless @identical_requests
  Scenario: Identical requests produce identical results
    Given I have a primary document with specific attributes
    And I have candidate documents with specific attributes
    When I send a POST request to "/" with the primary and candidate documents
    And I record the response
    And I send the exact same POST request to "/" again
    Then both responses should be functionally identical
    And only dynamic fields like timestamps or request IDs may differ

  @stateless @request_isolation
  Scenario: Processing a request does not affect subsequent unrelated requests
    Given I have a primary document A with specific attributes
    And I have candidate documents A with specific attributes
    And I have a completely different primary document B with specific attributes
    And I have completely different candidate documents B with specific attributes
    When I send a POST request to "/" with primary document A and candidates A
    And I record the response as response A
    And I send a POST request to "/" with primary document B and candidates B
    And I record the response as response B
    And I send another POST request to "/" with primary document A and candidates A
    Then this response should be functionally identical to response A
    And only dynamic fields like timestamps or request IDs may differ

  @stateless @high_volume
  Scenario: Service maintains statelessness under high volume
    Given the document matching service is available
    When I send multiple different requests in rapid succession
    And then I send a specific test request
    And I record the response
    And I wait for some time to pass
    And I send the exact same test request again
    Then both test responses should be functionally identical
    And only dynamic fields like timestamps or request IDs may differ
