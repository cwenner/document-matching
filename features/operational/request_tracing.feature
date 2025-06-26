@operational @tracing @story-2.3
Feature: Request Tracing Support
  As an API Consumer or Developer/Operator
  I want the service to support a trace ID that is included in all relevant logs
  So that I can effectively track and debug specific requests across distributed systems

  @tracing @provided_id
  Scenario: Service uses provided trace ID in logs
    Given the document matching service is running with logging enabled
    When I send a request with an "X-Trace-ID" header containing "test-trace-123"
    Then the service should log entries related to that request
    And all log entries should include the trace ID "test-trace-123"
    And the response should maintain the same trace ID in headers

  @tracing @generated_id
  Scenario: Service generates trace ID when none provided
    Given the document matching service is running with logging enabled
    When I send a request without an "X-Trace-ID" header
    Then the service should log entries related to that request
    And all log entries should include a generated trace ID
    And the response should include the generated trace ID in headers

  @tracing @error_scenario
  Scenario: Trace ID is preserved in error scenarios
    Given the document matching service is running with logging enabled
    When I send an invalid request with an "X-Trace-ID" header containing "error-trace-456"
    Then the service should log error entries related to that request
    And all error log entries should include the trace ID "error-trace-456"
    And the error response should maintain the same trace ID in headers

  @tracing @multi_component
  Scenario: Trace ID is preserved across service components
    Given the document matching service is running with multiple internal components
    When I send a complex request with an "X-Trace-ID" header containing "multi-component-789"
    Then all components involved in processing should log with the same trace ID
    And the internal service calls should propagate the trace ID
    And the final response should maintain the original trace ID
