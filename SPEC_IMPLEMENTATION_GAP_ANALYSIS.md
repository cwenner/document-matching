# Specification vs Implementation Gap Analysis

This document compares the deviation/certainty specification against the current implementation.

## Deviation Codes Summary

| Code | Specified | Implemented | Issue |
|------|-----------|-------------|-------|
| `ITEM_UNMATCHED` | Item | ❌ Not implemented | #20 |
| `CURRENCIES_DIFFER` | Header | ✅ Implemented | - |
| `AMOUNTS_DIFFER` | Header+Item | ⚠️ Wrong thresholds | #24 |
| `PRICES_PER_UNIT_DIFFER` | Item | ⚠️ Wrong thresholds | #25 |
| `PARTIAL_DELIVERY` | Item | ❌ Not implemented | #21 |
| `QUANTITIES_DIFFER` | Item | ⚠️ No severity calc | #26 |
| `DESCRIPTIONS_DIFFER` | Item | ⚠️ No similarity severity | #27 |
| `ARTICLE_NUMBERS_DIFFER` | Item | ❌ Not implemented | #22 |
| `ITEMS_DIFFER` | Item | ❌ Not implemented | #23 |

## Threshold Comparison

### AMOUNTS_DIFFER (Header)

| Severity | Spec | Current |
|----------|------|---------|
| no-severity | abs≤0.01 AND rel≤0.001 | ❌ Not implemented |
| low | abs≤1 AND rel≤0.01 | abs<1 AND rel<0.001 |
| medium | abs≤50 AND rel≤0.05 | abs≤1000 AND rel≤0.10 |
| high | otherwise | otherwise |

**Status**: Thresholds are too loose, missing no-severity level.

### AMOUNTS_DIFFER (Line)

| Severity | Spec | Current |
|----------|------|---------|
| no-severity | abs≤0.01 | ❌ Not implemented |
| low | abs≤1 OR rel≤0.01 | Uses header thresholds |
| medium | abs≤10 OR rel≤0.10 | Uses header thresholds |
| high | otherwise | otherwise |

**Status**: No separate line-level thresholds.

### PRICES_PER_UNIT_DIFFER

| Severity | Spec | Current |
|----------|------|---------|
| no-severity | abs≤0.005 OR rel≤0.005 | ❌ Not implemented |
| low | rel≤0.05 | Uses generic amount thresholds |
| medium | rel≤0.20 | Uses generic amount thresholds |
| high | otherwise | otherwise |

**Status**: No dedicated unit price severity function.

### QUANTITIES_DIFFER

| Severity | Spec | Current |
|----------|------|---------|
| low | abs≤1 AND rel≤0.10 | ❌ Always MEDIUM |
| medium | abs≤10 OR rel≤0.50 | ❌ Always MEDIUM |
| high | otherwise | ❌ Always MEDIUM |

**Status**: No severity calculation, always uses default MEDIUM.

### DESCRIPTIONS_DIFFER

| Severity | Spec (similarity-based) | Current |
|----------|-------------------------|---------|
| no-severity | sim≥0.98 | ❌ Not implemented |
| info | sim≥0.90 | Always INFO |
| low | sim≥0.75 | ❌ Not implemented |
| medium | sim≥0.50 | ❌ Not implemented |
| high | sim<0.50 or empty | ❌ Not implemented |

**Status**: Always returns INFO, ignores actual similarity score.

## Labels

| Label | Spec | Current |
|-------|------|---------|
| `matched` | certainty≥0.5 | Uses `match` not `matched` |
| `no-match` | certainty<0.2 or no match | ✅ Correct |
| `partial-delivery` | Any PARTIAL_DELIVERY deviation | ❌ Not implemented |

**Issue**: #29

## Certainty Metrics

| Metric | Spec | Current |
|--------|------|---------|
| `certainty` | P(pairing is final) | Hardcoded 0.93 / 0.95 |
| `deviation-severity` | max(all severities) | ✅ Implemented correctly |
| `{kind}-has-future-match-certainty` | P(more docs coming) | Hardcoded 0.0 / 0.88 |
| `item_unchanged_certainty` | P(item pairing unchanged) | Hardcoded 0.95 |

**Issue**: #30

## Review Thresholds

| Decision | Spec | Current |
|----------|------|---------|
| Auto-approve | certainty≥0.975, severity≤low, future≤0.2 | ❌ Not implemented |
| Light review | severity≥medium OR certainty∈[0.7,0.975) | ❌ Not implemented |
| Human review | severity=high OR CURRENCIES_DIFFER/ITEMS_DIFFER | ❌ Not implemented |
| Surface item in UI | certainty<0.9 OR severity≥medium | ❌ Not implemented |

**Issue**: #31

## Code Naming Convention

| Spec | Current | Status |
|------|---------|--------|
| UPPER_SNAKE_CASE | UPPER_SNAKE_CASE | ✅ Implemented |

**Issue**: #28 (COMPLETED)

## Created GitHub Issues

| # | Title |
|---|-------|
| 20 | Implement ITEM_UNMATCHED deviation code |
| 21 | Implement PARTIAL_DELIVERY deviation code |
| 22 | Implement ARTICLE_NUMBERS_DIFFER deviation code |
| 23 | Implement ITEMS_DIFFER deviation code |
| 24 | Fix AMOUNTS_DIFFER severity thresholds |
| 25 | Implement PRICES_PER_UNIT_DIFFER with correct thresholds |
| 26 | Implement QUANTITIES_DIFFER severity thresholds |
| 27 | Implement DESCRIPTIONS_DIFFER with similarity-based severity |
| 28 | Standardize deviation code naming convention |
| 29 | Implement proper 'matched' vs 'no-match' label logic |
| 30 | Implement computed certainty metrics |
| 31 | Implement review threshold logic for UI surfacing |

## Priority Recommendations

### High Priority (Core functionality)
1. #24 - AMOUNTS_DIFFER thresholds (affects all amount comparisons)
2. #30 - Certainty metrics (all hardcoded)
3. #20 - ITEM_UNMATCHED (required for complete reporting)
4. #21 - PARTIAL_DELIVERY (key business requirement)

### Medium Priority (Feature completeness)
5. #25 - PRICES_PER_UNIT_DIFFER thresholds
6. #26 - QUANTITIES_DIFFER thresholds
7. #27 - DESCRIPTIONS_DIFFER similarity
8. #22 - ARTICLE_NUMBERS_DIFFER
9. #23 - ITEMS_DIFFER
10. #29 - Label logic

### Lower Priority (Polish)
11. #28 - Code naming convention
12. #31 - Review thresholds (UI feature)
