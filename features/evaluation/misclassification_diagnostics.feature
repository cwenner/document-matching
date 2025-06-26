@evaluation @diagnostics @story-3.6
Feature: Detailed Diagnostics for Misclassifications
  As an Evaluator
  I want detailed diagnostic information for false negatives and false positives
  So that I can diagnose why certain expected pairings were missed or incorrect matches occurred

  Background:
    Given I have an evaluation script
    And I have loaded a valid evaluation dataset
    And I have run the evaluation against a matching service
    And the evaluation has completed with results

  @diagnostics @false_negatives
  Scenario: Detailed reporting of false negatives (missed matches)
    When I request diagnostics for false negatives
    Then the report should include for each missed match, Primary document ID and key attributes
    And the report should include for each missed match, Expected candidate document ID and key attributes
    And the report should include for each missed match, Similarity scores between the documents (if available)
    And the report should include for each missed match, Possible reasons for the missed match
    And the report should include for each missed match, Visualization of document differences (if supported)

  @diagnostics @false_positives
  Scenario: Detailed reporting of false positives (incorrect matches)
    When I request diagnostics for false positives
    Then the report should include for each incorrect match, Primary document ID and key attributes
    And the report should include for each incorrect match, Incorrectly matched document ID and key attributes
    And the report should include for each incorrect match, The service's match certainty for this pair
    And the report should include for each incorrect match, Key fields that may have caused the incorrect match
    And the report should include for each incorrect match, The closest correct match (if one exists)

  @diagnostics @ranking
  Scenario: Rank misclassifications by severity or impact
    When I generate the diagnostics report
    Then the report should rank misclassifications by impact or severity
    And prioritize high-value transaction errors
    And group similar error patterns together
    And highlight the most significant or frequent error types

  @diagnostics @field_level
  Scenario: Field-level diagnostic information
    When I request field-level diagnostics
    Then the report should show which specific fields contributed to each misclassification
    And highlight significant differences between matched field values
    And provide field-by-field similarity scores where available

  @diagnostics @threshold_analysis
  Scenario: Impact of confidence thresholds on error types
    When I request diagnostics with threshold analysis
    Then the report should show how different confidence thresholds affect error distribution
    And identify the optimal threshold that minimizes critical errors
    And visualize the tradeoff between false positive and false negative rates

  @diagnostics @export
  Scenario: Export detailed error cases for further analysis
    When I request to export error cases
    Then the script should generate detailed files for each misclassification
    And these exports should contain the complete document data
    And include service responses and confidence scores
    And be in a format suitable for further analysis
