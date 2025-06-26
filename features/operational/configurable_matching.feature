@operational @configuration @story-2.4
Feature: Configurable Matching Logic (Model vs. Dummy)
  As an Operations Engineer or Developer
  I want to configure the service to use either its predictive model or a dummy/fallback logic
  So that we can control model rollout or operate in environments where the model is unavailable

  Background:
    Given the document matching service is available

  @config @model_enabled
  Scenario: Service uses predictive model when configured
    Given the service is configured to use the predictive model
    When I send a document matching request with complex data
    Then the response should use the predictive model's logic
    And the matching results should reflect sophisticated analysis
    And the service logs should indicate that the model was used

  @config @dummy_fallback
  Scenario: Service uses dummy logic when configured
    Given the service is configured to use dummy/fallback logic
    When I send a document matching request with complex data
    Then the response should use the dummy/fallback logic
    And the matching results should follow the expected fallback behavior
    And the service logs should indicate that fallback logic was used

  @config @env_variable
  Scenario: Configuration via environment variable
    Given the service is deployed with environment variable "USE_PREDICTIVE_MODEL=false"
    When I send a document matching request
    Then the service should use the dummy/fallback logic
    And changing the environment variable to "USE_PREDICTIVE_MODEL=true" should enable the model

  @config @config_file
  Scenario: Configuration via configuration file
    Given the service has a configuration file with "matching_logic: dummy"
    When I send a document matching request
    Then the service should use the dummy/fallback logic
    And updating the configuration file to "matching_logic: model" should enable the model

  @config @site_specific
  Scenario: Site-specific configuration
    Given the service supports site-specific configurations
    And site "whitelisted" is configured to use the predictive model
    And site "blacklisted" is configured to use the dummy logic
    When I send a request for site "whitelisted"
    Then the response should use the predictive model
    When I send a request for site "blacklisted"
    Then the response should use the dummy logic
