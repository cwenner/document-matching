@evaluation @metrics @story-3.4
Feature: Receive Comprehensive Performance Metrics
  As an Evaluator
  I want to receive detailed performance metrics for the matching service
  So that I can thoroughly assess matching accuracy and identify areas for improvement

  Background:
    Given I have an evaluation script
    And I have loaded a valid evaluation dataset
    And I have run the evaluation against a matching service
    And the evaluation has completed with results

  @metrics @basic_metrics
  Scenario: Calculate basic classification metrics
    When the script generates the evaluation report
    Then the report should include True Positives (matches correctly identified)
    And the report should include False Positives (incorrect matches)
    And the report should include True Negatives (non-matches correctly identified)
    And the report should include False Negatives (missed matches)
    And the report should include Precision (TP / (TP + FP))
    And the report should include Recall (TP / (TP + FN))
    And the report should include F1-score (2 * Precision * Recall / (Precision + Recall))

  @metrics @comparison
  Scenario: Compare predictions against ground truth
    When the script analyzes the service responses
    Then it should compare each predicted match against the ground truth
    And classify each prediction as true positive, false positive, true negative, or false negative
    And provide a clear summary of correct and incorrect predictions

  @metrics @document_types
  Scenario: Metrics by document type
    When the script generates the evaluation report with document type breakdown
    Then the report should include metrics separated by document type combinations
    And show specific performance for invoice-PO matches, invoice-delivery matches, and other combinations

  @metrics @confidence_thresholds
  Scenario: Evaluate metrics across confidence thresholds
    When the script generates the evaluation report with confidence threshold analysis
    Then the report should include metrics at various confidence threshold levels
    And calculate precision-recall curves based on match certainty values
    And recommend optimal confidence thresholds based on F1-score or other criteria

  @metrics @visualization
  Scenario: Visualize performance metrics
    When the script is run with visualization enabled
    Then it should generate visual representations of the metrics
    And include confusion matrices for classification results
    And create precision-recall curves for threshold analysis
    And provide other relevant visualizations that aid in understanding the performance

  @metrics @sequential
  Scenario: Performance metrics in sequential evaluation mode
    Given the evaluation was run with sequential document processing
    When the script generates the evaluation report
    Then it should calculate metrics that reflect the sequential nature of the evaluation
    And account for the impact of history building on match quality
    And track performance trends as the history grows over time
