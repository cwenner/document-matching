@operational @health @story-2.1
Feature: Service Readiness Probe
  As an Operations Engineer
  I want to probe a dedicated readiness endpoint
  So that my orchestration system can verify the service instance is ready to accept traffic

  @readiness @healthy
  Scenario: Service is ready to accept traffic
    Given the document matching service is running
    When I send a GET request to "/health/readiness"
    Then the response status code should be 200
    And the response body should contain a valid readiness status
    And the readiness status should indicate "READY" or "UP"

  @readiness @initialization
  Scenario: Service readiness during initialization
    Given the document matching service is starting up
    When I send a GET request to "/health/readiness" before initialization completes
    Then the response status code should not be 200
    And the response body should indicate the service is not yet ready

  @readiness @components
  Scenario: Readiness checks all required components
    Given the document matching service is running
    And all required components have been properly initialized
    When I send a GET request to "/health/readiness"
    Then the response status code should be 200
    And the response body should show all components as ready

  @readiness @degraded
  Scenario: One component is not ready
    Given the document matching service is running
    And one critical component has failed to initialize
    When I send a GET request to "/health/readiness"
    Then the response body should indicate which component is not ready
    And the response should reflect appropriate readiness status based on component criticality
