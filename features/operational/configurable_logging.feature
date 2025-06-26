@operational @logging @story-2.6
Feature: Configurable Logging Levels
  As an Operations Engineer
  I want to be able to configure the logging level for the service
  So that I can control the verbosity of logs for troubleshooting or normal operation

  Background:
    Given the document matching service is available

  @logging @default_level
  Scenario: Service starts with default logging level
    Given the document matching service is started without explicit logging configuration
    When I check the service logs
    Then they should reflect the default logging level
    And the default level should be appropriate for normal operation

  @logging @env_variable
  Scenario: Configure logging level via environment variable
    Given the document matching service is started with environment variable "LOG_LEVEL=DEBUG"
    When I perform operations that generate logs at different levels
    Then the logs should include entries at DEBUG level and higher
    When the service is restarted with environment variable "LOG_LEVEL=ERROR"
    And I perform the same operations
    Then the logs should only include entries at ERROR level and higher

  @logging @config_file
  Scenario: Configure logging level via configuration file
    Given the document matching service has a configuration file with "log_level: INFO"
    When I start the service
    And I perform operations that generate logs at different levels
    Then the logs should include entries at INFO level and higher
    When I update the configuration file to "log_level: WARN"
    And I restart the service
    And I perform the same operations
    Then the logs should only include entries at WARN level and higher

  @logging @component_specific
  Scenario: Configure component-specific logging levels
    Given the document matching service supports component-specific logging configuration
    When I configure component "item-semantic-matching" to log at DEBUG level
    And I configure component "document-matching" to log at ERROR level
    And I perform operations that involve both components
    Then logs from "item-semantic-matching" should include entries at DEBUG level and higher
    And logs from "document-matching" should only include entries at ERROR level and higher

  @logging @validation
  Scenario: Validate logging level configuration
    Given the document matching service is available
    When I attempt to set an invalid logging level
    Then the service should reject the invalid configuration
    And it should continue using the previous valid logging level
    And it should log an appropriate error about the invalid configuration
