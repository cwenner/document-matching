@developer @adhoc_testing @story-4.5
Feature: Ad-hoc API Testing and Validation
  As a Developer
  I want to easily send ad-hoc requests to the matching service with documents from local files and validate responses
  So that I can quickly test service functionality during development

  Background:
    Given I have a local testing utility for the document matching service
    And the document matching service is available

  @adhoc_testing @basic_request
  Scenario: Send document matching request using local files
    Given I have a local JSON file containing a primary document
    And I have local JSON files containing candidate documents
    When I run the utility with paths to these files
    Then the utility should submit a request to the matching service
    And display the formatted response from the service
    And exit with a success status code

  @adhoc_testing @configuration_options
  Scenario: Override request parameters via command line
    When I run the utility with command-line options:
      | --primary-doc=path/to/invoice.json   |
      | --candidates=path/to/candidates/     |
    Then the utility should use these parameters in the request to the matching service
    And these parameters should override any defaults

  @adhoc_testing @response_validation
  Scenario: Validate response against expected output
    Given I have a local file containing expected output
    When I run the utility with validation enabled
    Then the utility should compare the service response to the expected output
    And report any discrepancies between actual and expected outputs
    And exit with a success status code if validation passes
    And exit with an error status code if validation fails
