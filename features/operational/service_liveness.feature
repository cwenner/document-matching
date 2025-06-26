@operational @health @story-2.2
Feature: Service Liveness/Health Probe
  As an Operations Engineer
  I want to probe a dedicated liveness endpoint
  So that my orchestration system can determine if the service is still running correctly

  @liveness @healthy
  Scenario: Service is running correctly
    Given the document matching service is running
    When I send a GET request to "/health/liveness"
    Then the response status code should be 200
    And the response body should contain a valid health status
    And the health status should indicate "HEALTHY"

  @liveness @unhealthy
  Scenario: Service is unhealthy
    Given the document matching service is in an unhealthy state
    When I send a GET request to "/health/liveness"
    Then the response status code should not be 200
    And the response body should indicate the service is unhealthy
