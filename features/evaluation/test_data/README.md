# Evaluation Test Data

This directory contains test data files used by the evaluation BDD tests located in `features/evaluation/`.

## File Organization

### Dataset Files
- `valid_dataset.json` - Properly structured evaluation dataset with ground truth data
- `malformed_dataset.json` - Invalid dataset format for error testing scenarios
- `large_dataset.json` - Large dataset for performance testing with multiple candidates
- `ground_truth_sample.json` - Sample ground truth pairing data for evaluation metrics

## File Structure

### Dataset Format
Evaluation datasets follow this structure:
```json
[
  {
    "primary_document": { ... },
    "candidate_documents": [ ... ],
    "ground_truth": {
      "is_match": true/false,
      "confidence": 0.0-1.0,
      "match_reason": "description"
    }
  }
]
```

### Ground Truth Format
Ground truth files contain evaluation metadata and pairing results:
```json
{
  "version": "v1",
  "evaluation_metadata": { ... },
  "ground_truth_pairs": [ ... ]
}
```

## Usage

These files are used by evaluation feature tests to:
- Test dataset loading and validation
- Perform matching performance evaluation
- Generate metrics and diagnostics
- Simulate historical evaluation scenarios

Use "test-site" as the site value to ensure proper ML pipeline testing.