@evaluation @history @story-3.3
Feature: Simulate History Building for Evaluation Context
  As an Evaluator
  I want to build a history of candidate documents before starting the actual predictions
  So that the matching context is more realistic, simulating a stream of documents

  Background:
    Given I have an evaluation script
    And I have loaded a valid evaluation dataset

  @history @initial_portion
  Scenario: Specify initial portion for history building
    When I configure the script to use 30% of the dataset for history building
    Then the script should process the first 30% of entries as history builders
    And these documents should be added to the candidate pool
    And no matching metrics should be calculated for these history-building documents

  @history @candidate_pool
  Scenario: Maintain candidate pool from history documents
    When I run the evaluation with history building enabled
    Then the script should maintain a pool of documents from the history portion
    And this candidate pool should be available for matching with test documents
    And the script should report the size and composition of the candidate pool

  @history @combined_candidates
  Scenario: Combine explicit and history candidates
    Given I have configured history building
    When I run the evaluation on a test document that has both:
      | Explicit candidates listed in the dataset    |
      | Matching candidates from the history pool    |
    Then the script should include both types of candidates in matching requests
    And distinguish between explicit and history-derived candidates in the results

  @history @selective_history
  Scenario: Filter history candidates by criteria
    When I configure the script to filter history candidates by document type
    Then only documents matching the filter criteria should be included in the candidate pool
    And the script should report the filter criteria and candidate pool composition

  @history @realistic_chronology
  Scenario: Respect document chronology in history simulation
    Given the dataset contains document creation timestamps
    When I run the evaluation with chronology-aware history building
    Then the script should process documents in chronological order
    And only include older documents as candidates for newer test documents
