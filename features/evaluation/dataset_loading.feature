@evaluation @dataset @story-3.1
Feature: Load Evaluation Dataset
  As an Evaluator (e.g., Developer, Data Scientist, QA Engineer)
  I want to load an evaluation dataset from a structured file
  So that I can systematically test the matching service's performance

  @dataset @valid_format
  Scenario: Load a valid evaluation dataset
    Given I have an evaluation script
    And I have a structured dataset file in JSON format
    When I run the script with the path to the dataset file
    Then the script should successfully load the dataset
    And report the number of evaluation cases loaded
    And provide a summary of the dataset contents

  @dataset @structure
  Scenario: Dataset contains required structure
    Given I have an evaluation script
    And I have a structured dataset file
    When I examine the loaded dataset
    Then each evaluation case should contain a primary document
    And each case should contain candidate documents
    And each case should specify expected ground truth pairings

  @dataset @invalid_path
  Scenario: Handle invalid dataset path
    Given I have an evaluation script
    When I run the script with an invalid file path
    Then the script should fail gracefully
    And provide a clear error message about the invalid path

  @dataset @invalid_format
  Scenario: Handle malformed dataset
    Given I have an evaluation script
    And I have a malformed dataset file
    When I run the script with the path to the malformed file
    Then the script should fail gracefully
    And provide clear error messages about the formatting issues

  @dataset @missing_fields
  Scenario: Handle missing required fields
    Given I have an evaluation script
    And I have a dataset file with missing required fields
    When I run the script with the path to this dataset file
    Then the script should validate the dataset structure
    And report which required fields are missing
    
  @dataset @large_dataset
  Scenario: Handle large evaluation datasets efficiently
    Given I have an evaluation script
    And I have a large dataset file with many evaluation cases
    When I run the script with the path to this large dataset
    Then the script should load the dataset without excessive memory usage
    And provide progress feedback during the loading process
