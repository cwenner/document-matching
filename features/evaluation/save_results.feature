@evaluation @results @story-3.7
Feature: Save Evaluation Results
  As an Evaluator
  I want to save detailed evaluation results and metrics to files
  So that I can archive, review, and compare evaluation outcomes over time

  Background:
    Given I have an evaluation script
    And I have loaded a valid evaluation dataset
    And I have run the evaluation against a matching service
    And the evaluation has completed with results

  @results @output_path
  Scenario: Specify output file path
    When I run the script with an output file path specified
    Then the evaluation results should be saved to the specified path
    And the script should confirm successful file creation

  @results @summary_metrics
  Scenario: Include summary metrics in output file
    When I save the evaluation results to a file
    Then the file should include summary metrics on Total test cases processed
    And the file should include summary metrics on True positives, false positives
    And the file should include summary metrics on True negatives, false negatives
    And the file should include summary metrics on Precision, recall, F1-score
    And the file should include summary metrics on Runtime and processing statistics

  @results @detailed_results
  Scenario: Include detailed per-case results
    When I save the evaluation results to a file
    Then the file should include individual results on Primary document identifier
    And the file should include individual results on Candidate documents identifiers
    And the file should include individual results on Expected ground truth matches
    And the file should include individual results on Actual predictions from the service
    And the file should include individual results on Classification outcome (TP/FP/TN/FN)
    And the file should include individual results on Match certainty scores if available

  @results @comparison_ready
  Scenario: Format results for easy comparison
    When I save evaluation results with comparison mode enabled
    Then the output should include a unique evaluation identifier
    And include timestamp and service version information
    And use a format that facilitates automated comparison between evaluation runs

  @results @incremental_saving
  Scenario: Support incremental results saving during long evaluations
    Given I am running a long evaluation with many test cases
    When I configure incremental saving of results
    Then the script should periodically save intermediate results
    And update the output file as the evaluation progresses
    And enable resuming evaluation from checkpoint if interrupted
