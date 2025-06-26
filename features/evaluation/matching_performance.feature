@evaluation @performance @story-3.2
Feature: Evaluate Matching Performance
  As an Evaluator (e.g., Developer, Data Scientist, QA Engineer)
  I want to run the evaluation by making calls to a running matching service
  So that I can test the end-to-end behavior of the deployed service

  Background:
    Given I have an evaluation script
    And I have loaded a valid evaluation dataset
    And a matching service instance is running and accessible

  @performance @endpoint_config
  Scenario: Configure target service endpoint
    When I configure the script with the target service endpoint URL
    Then the script should validate the endpoint is accessible
    And store the configuration for subsequent evaluation requests

  @performance @timeout_handling
  Scenario: Handle service timeouts gracefully
    Given the service endpoint occasionally experiences timeouts
    When I run the evaluation script with configurable timeout settings
    Then the script should retry failed requests according to the retry policy
    And record timeout events in the evaluation results
    And continue with the next evaluation case after retry attempts are exhausted

  @performance @error_handling
  Scenario: Handle service errors gracefully
    Given the service endpoint returns an error for certain requests
    When I run the evaluation script against the service
    Then the script should capture the error responses
    And include these errors in the evaluation report
    And continue processing the remaining evaluation cases

  @performance @batch_processing
  Scenario: Support batch processing of evaluation cases
    When I run the evaluation script with batch processing enabled
    Then the script should process evaluation cases in configurable batch sizes
    And aggregate results across all batches in the final report
    And provide batch-level progress feedback
