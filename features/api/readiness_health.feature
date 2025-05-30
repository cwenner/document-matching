@api @health @smoke
Feature: API Readiness and Health Checks
  As an operations team member or an automated monitoring system
  I want to check the service's readiness and health status
  So that I can ensure the service is operational and responding correctly.

  Background:
    Given the matching service is expected to be running at "http://localhost:8000"

  Scenario: Readiness probe indicates service is ready
    When I send a GET request to "/health/readiness"
    Then the response status code should be 200
    And the JSON response should contain a field "status" with value "READY"

  Scenario: Liveness probe indicates service is healthy
    When I send a GET request to "/health/liveness"
    Then the response status code should be 200
    And the JSON response should contain a field "status" with value "HEALTHY"
