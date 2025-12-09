# ADR-002: Model Architecture for Document Matching

**Status**: Accepted
**Date**: 2025-12-08
**Issue**: #63
**Author**: Claude (via /start-ticket)
**Depends On**: ADR-001 (PO-Hub Topology)

---

## Context

The document matching system currently has one SVM model trained for **Invoice → PO** matching. For V1, we need to support bidirectional Invoice ↔ PO matching.

Given the PO-Hub topology (ADR-001), the required matching directions are:
- **Invoice ↔ PO** (bidirectional, ML-assisted)
- **PO ↔ Delivery** (reference-only for V1)
- **Invoice ↔ Delivery** (transitive via shared PO, no dedicated model)

### Options Considered

**Option A: Single Generalized Model**
- Retrain model on all document pair combinations
- Add document type as feature input
- High effort, over-engineered for V1

**Option B: Multiple Specialized Models**
- Separate model per document pair type
- `invoice-po-svm.pkl`, `po-invoice-svm.pkl`, etc.
- Unnecessary duplication

**Option C: Symmetric Feature Engineering**
- Retrain model on symmetric data (both directions)
- Unnecessary complexity

**Option D: Canonical Order Normalization** ← **CHOSEN**
- Keep existing model unchanged
- Normalize input to canonical (Invoice, PO) order at prediction time
- Zero retraining, minimal code change

---

## Decision

**We choose Option D: Canonical Order Normalization**

Keep the existing Invoice→PO model unchanged. At prediction time, normalize document pairs to canonical order before feature extraction.

---

## Rationale

### The Key Insight

The matching relationship between Invoice and PO is **symmetric** - if Invoice A matches PO B, then PO B matches Invoice A. The model doesn't care which document was the "primary" input; it only cares about the features comparing the pair.

### Implementation

```python
def predict_match(doc1, doc2):
    # Normalize to canonical order: (invoice, po)
    if doc1["kind"] == "purchase-order" and doc2["kind"] == "invoice":
        invoice, po = doc2, doc1
    elif doc1["kind"] == "invoice" and doc2["kind"] == "purchase-order":
        invoice, po = doc1, doc2
    else:
        # Handle other cases or raise error
        ...

    # Use existing model as-is
    features = _get_comparison_features(invoice, po)
    return model.predict(features)
```

### Why This Is Better

| Criterion | Option C (Symmetric Training) | **Option D (Normalize Order)** |
|-----------|-------------------------------|--------------------------------|
| Retraining | Required | **None** |
| Code changes | Moderate | **Minimal (swap logic)** |
| Risk | Model accuracy might change | **Zero risk to model** |
| Effort | Days | **Hours** |
| Complexity | New training pipeline | **Simple conditional** |

### Chronology Handling

If we need to track which document arrived first (for business logic, not matching):
- Add a separate feature or metadata: `is_invoice_newer: bool`
- This is independent of the matching prediction

---

## Implementation Plan

### Single Change Required

**File**: `src/docpairing.py`

1. In `_get_comparison_features()` or the calling code, add order normalization:
   - If (PO, Invoice) is passed, swap to (Invoice, PO)
   - Extract features using existing logic
   - Return prediction

2. Remove Invoice-only restriction at line 430:
   ```python
   # BEFORE
   if document["kind"] != "invoice":
       return base_pred

   # AFTER: Allow PO as primary, normalize order internally
   ```

### No Changes Required

- ❌ No retraining
- ❌ No new training data
- ❌ No new model file
- ❌ No feature engineering changes

---

## Consequences

### Positive

- **Zero model risk** - existing model unchanged
- **Minimal code change** - just order normalization
- **Immediate implementation** - no training pipeline needed
- **Simple to understand** - swap order, use existing model

### Negative

- **Assumes symmetry** - relies on match relationship being symmetric (which it is)

### Neutral

- **PO ↔ Delivery** remains reference-only for V1 (per ADR-001)

---

## Verification

1. **Unit test**: Pass (PO, Invoice) pair, verify same result as (Invoice, PO)
2. **Integration test**: API correctly returns matches regardless of input order

---

## References

- `src/docpairing.py` - Feature extraction (line ~580+)
- `src/docpairing.py:430` - Invoice-only restriction to remove
- ADR-001 - PO-Hub Topology (confirms scope)
- Issue #63 - Decision request
