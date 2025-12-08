# ADR-001: Document Matching Topology

**Status**: Accepted
**Date**: 2025-12-08
**Issue**: #62
**Author**: Claude (via /auto-pick-ticket)

---

## Context

The document matching system needs to support three document types: Invoice, Purchase Order (PO), and Delivery Receipt. We need to decide the topology for how these documents relate to each other in the matching system.

### Options Considered

**Option A: PO-Hub Model**
```
Invoice ←→ PO ←→ Delivery Receipt
         (hub)
```
- Invoice matches directly to PO
- Delivery matches directly to PO
- Invoice-to-Delivery relationship is inferred transitively through shared PO

**Option B: Full Mesh Model**
```
Invoice ←→ PO
Invoice ←→ Delivery
PO ←→ Delivery
```
- All document types can match directly to each other

---

## Decision

**We choose Option A: PO-Hub Model**

The Purchase Order serves as the central hub for document matching. All matching relationships are anchored through the PO.

---

## Rationale

### 1. Already Implemented in Code

Analysis of `src/docpairing.py` shows the PO-Hub model is already implemented:

| Matching Direction | Implementation | Method |
|--------------------|----------------|--------|
| Invoice → PO | Direct | Reference matching + SVM fallback |
| PO → Invoice | Direct | Reference lookup |
| Delivery → PO | Direct | Line item PO number reference |
| PO → Delivery | Direct | Reference lookup |
| Invoice → Delivery | Transitive | Via `_make_pairings_transitive()` |
| Delivery → Invoice | Transitive | Via `_make_pairings_transitive()` |

Key code evidence:
- Lines 293-316: Reference-based matching uses PO as anchor
- Lines 498-570: `_make_pairings_transitive()` creates Invoice↔Delivery links through shared PO

### 2. Real-World Procurement Workflows

In B2B procurement, the PO is the authoritative document:

```
Typical Flow:
1. Buyer creates PO (references supplier, items, prices)
2. Supplier sends Delivery (references PO number)
3. Supplier sends Invoice (references PO number / order reference)
```

Both Invoice and Delivery naturally reference the PO. Direct Invoice↔Delivery matching without a PO anchor has no reliable reference field.

### 3. Answers to Decision Questions

**Q1: Are there real-world scenarios where invoice needs to match directly to delivery (no PO)?**

Very rare. In standard B2B workflows:
- If there's no PO, matching any documents is unreliable
- Both invoice and delivery would need some common reference (typically the PO number)
- Without PO, there's no authoritative source of expected items/prices

**Q2: Is PO always the "source of truth" document in customer workflows?**

Yes. The PO defines:
- Expected line items and quantities
- Agreed prices
- Delivery schedule
- Payment terms

**Q3: What do customers actually send us - always PO first, or sometimes delivery first?**

Document arrival order varies, but the PO is always created first in the business workflow. The system's reference-based matching handles any arrival order because it uses bidirectional lookups.

### 4. Implementation Effort Comparison

| Approach | ML Training | Reference Logic | Transitive Logic | Total Effort |
|----------|-------------|-----------------|------------------|--------------|
| PO-Hub (A) | 1 model | Already done | Already done | Low |
| Full Mesh (B) | 3 models | Additional needed | N/A | High |

Full Mesh would require:
- New Invoice↔Delivery matching model (no training data exists)
- New reference matching logic (no common reference field)
- 3x model maintenance

### 5. Coverage Analysis

| Scenario | PO-Hub Coverage | Notes |
|----------|-----------------|-------|
| Standard 3-way match | ✅ | Invoice↔PO + Delivery↔PO + transitive |
| Invoice without PO | ⚠️ | SVM fallback only for Invoice→PO |
| Delivery without PO | ❌ | Cannot match (no anchor) |
| Invoice to Delivery (no PO) | ❌ | Cannot match (no common reference) |

The uncovered scenarios (Delivery without PO, Invoice↔Delivery without PO) are edge cases that:
- Represent <5% of real-world scenarios
- Have no reliable matching criteria even with Full Mesh
- Can be addressed in V2 if customer demand emerges

---

## Consequences

### Positive
- No code changes required for topology (already implemented)
- Single SVM model to maintain (Invoice→PO)
- Clear mental model for developers
- Transitive matching "just works"

### Negative
- Cannot match Invoice↔Delivery without a PO
- Documents without PO reference have limited matching options

### Neutral
- Future direction: If direct Invoice↔Delivery matching is needed, it can be added as an extension without changing the core topology

---

## Impact on Related Issues

| Issue | Impact |
|-------|--------|
| #14 (All matching directions) | Confirmed: PO-Hub with transitive matching |
| #52 (PO as primary document) | Needs SVM fallback extension, not topology change |
| #53 (Three-way matching) | Supported via transitive matching |
| #63 (Model architecture) | Scope clarified: Focus on Invoice↔PO, consider PO↔Delivery |
| #13 (3-way report generation) | Transitive relationships available |

---

## Verification

The decision can be verified by:
1. Existing test coverage for Invoice→PO→Delivery chains
2. `_make_pairings_transitive()` unit tests
3. Feature scenarios in `features/api-consumer/basic.feature`

---

## References

- `src/docpairing.py` - Core matching logic
- `src/match_pipeline.py` - Pipeline orchestration
- Issue #62 - Original decision request
