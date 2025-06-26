@evaluation @metrics_breakdown @story-3.5
Feature: Breakdown and Slice Performance Metrics
  As an Evaluator
  I want the evaluation report to break down metrics by various configurable facets
  So that I can identify performance variations across different business scenarios

  Background:
    Given I have an evaluation script
    And I have loaded a valid evaluation dataset
    And I have run the evaluation against a matching service
    And the evaluation has completed with results

  @metrics_breakdown @document_kind
  Scenario: Break down metrics by document kind combinations
    When I request metrics breakdown by document kind
    Then the report should include separate metrics for Primary "Invoice" vs candidate "Purchase Order" matches
    And the report should include separate metrics for Primary "Invoice" vs candidate "Delivery Receipt" matches
    And the report should include separate metrics for Other document kind combinations in the dataset
    And each breakdown should include precision, recall, and F1-score

  @metrics_breakdown @configurable_facets
  Scenario: Configure which facets to use for breakdown
    When I run the script with facet configuration
    Then the script should accept any dataset field as a breakdown dimension
    And generate separate metrics for each unique value of the configured facets
    And combine facets for multi-dimensional breakdowns if specified

  @metrics_breakdown @site_specific
  Scenario: Analyze performance for specific sites
    Given the dataset includes site identifiers for documents
    When I request metrics breakdown by site
    Then the report should include per-site performance metrics
    And highlight sites with significantly better or worse performance
    And provide comparative analysis between sites

  @metrics_breakdown @filtering
  Scenario: Filter evaluation to specific data subsets
    When I configure the script with data filters like "site_id=ABC123"
    Then the evaluation should only include data matching the filter criteria
    And metrics should be calculated only on the filtered subset
    And the report should clearly indicate the applied filters

  @metrics_breakdown @comparison
  Scenario: Compare performance across different dimensions
    When I run the evaluation with comparative analysis enabled
    Then the report should include statistical significance of performance differences
    And highlight the dimensions with the largest performance variations
    And provide actionable insights based on the dimensional analysis
